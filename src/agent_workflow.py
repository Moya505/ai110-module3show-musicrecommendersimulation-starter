"""
Agentic workflow around the deterministic music recommender.

Implements docs/agentic_music_workflow.mmd. The data classes mirror the
entities in docs/agentic_music_entities.mmd (WORKFLOW_RUN, AGENT_STEP,
RECOMMENDATION, USER_FEEDBACK, TOOL, AGENT).

The agents are rule-based (no LLM, no network), so every run is reproducible.
The existing scoring code stays the only source of truth for scores; agents
plan, validate, verify and explain, but never invent a score.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

try:  # imported as src.agent_workflow (tests)
    from .recommender import load_songs, recommend_songs, score_song
    from .retriever import Candidate, Retriever
    from .explainer import Explainer, Recommendation, TemplateExplainer
except ImportError:  # run as a script from src/
    from recommender import load_songs, recommend_songs, score_song
    from retriever import Candidate, Retriever
    from explainer import Explainer, Recommendation, TemplateExplainer

MAX_SCORE = 4.0
SCORED_FEATURES_NOTE = (
    "Only genre, mood and energy are scored; tempo, valence, danceability "
    "and acousticness are ignored."
)

Ranked = List[Tuple[Dict, float, str]]
DEFAULT_CANDIDATE_POOL = 20


# --- Entities (from the ER diagram) -----------------------------------------

@dataclass
class AgentStep:
    step_order: int
    agent: str
    tool: Optional[str]  # optional FK to TOOL, as in the diagram
    status: str          # "ok" | "failed" | "retry"
    detail: str = ""


@dataclass
class WorkflowRun:
    run_id: int
    request: Dict
    status: str = "running"  # complete | needs_clarification | no_match | error
    steps: List[AgentStep] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)  # for clarification
    limitations: List[str] = field(default_factory=list)
    error: str = ""
    feedback: List[str] = field(default_factory=list)   # USER_FEEDBACK rows

    def log(self, agent: str, tool: Optional[str], status: str, detail: str = "") -> None:
        self.steps.append(AgentStep(len(self.steps) + 1, agent, tool, status, detail))


# --- Agents -----------------------------------------------------------------

class PreferenceAgent:
    """Validate and normalize user input; ask questions instead of guessing."""

    def validate(self, request: Dict) -> Tuple[Dict, int, List[str]]:
        questions: List[str] = []
        prefs: Dict = {}

        for key in ("genre", "mood"):
            value = request.get(key)
            if isinstance(value, str) and value.strip():
                prefs[key] = value.strip().casefold()
            else:
                questions.append(f"Which {key} would you like?")

        energy = request.get("energy")
        if (
            isinstance(energy, bool)
            or not isinstance(energy, (int, float))
            or not 0 <= energy <= 1
        ):
            questions.append("What energy level (0.0 calm to 1.0 intense) do you want?")
        else:
            prefs["energy"] = float(energy)

        top_k = request.get("top_k", 5)
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
            questions.append("How many songs (a positive whole number) do you want?")
            top_k = 5
        return prefs, top_k, questions


    def validate_query(self, request: Dict) -> Tuple[Optional[str], List[str]]:
        """The free-text query is optional; blank means "no query"."""
        query = request.get("query")
        if query is None:
            return None, []
        if not isinstance(query, str):
            return None, ["Please describe what you want as text."]
        return (query.strip() or None), []


class CriticAgent:
    """Independently verify the ranking before anything reaches the user."""

    def verify(
        self,
        prefs: Dict,
        ranked: Ranked,
        k: int,
        catalog_size: int,
        allowed_ids: Optional[Sequence[int]] = None,
    ) -> List[str]:
        problems: List[str] = []
        expected = min(k, catalog_size)
        if len(ranked) != expected:
            problems.append(f"expected {expected} results, got {len(ranked)}")

        scores = [score for _, score, _ in ranked]
        if scores != sorted(scores, reverse=True):
            problems.append("results are not sorted by score")

        ids = [song["id"] for song, _, _ in ranked]
        if len(ids) != len(set(ids)):
            problems.append("duplicate songs in results")

        if allowed_ids is not None:
            stray = [s["title"] for s, _, _ in ranked if s["id"] not in set(allowed_ids)]
            if stray:
                problems.append(f"results outside the retrieved candidates: {stray}")

        for song, score, explanation in ranked:
            if not 0 <= score <= MAX_SCORE:
                problems.append(f"{song['title']}: score {score:.2f} out of range")
            expected_score, _ = score_song(prefs, song)
            if abs(expected_score - score) > 1e-9:
                problems.append(f"{song['title']}: score does not match the recipe")
            if not explanation.strip():
                problems.append(f"{song['title']}: empty explanation")
        return problems


class ExplanationAgent:
    """Turn verified scores into grounded explanations and limitations.

    The wording comes from a pluggable Explainer (template by default, or an
    LLM-backed one that is checked against the facts); scores never change.
    """

    def __init__(self, explainer: Optional[Explainer] = None):
        self.explainer = explainer or TemplateExplainer()

    def limitations(
        self, prefs: Dict, catalog: List[Dict], pool_size: Optional[int] = None
    ) -> List[str]:
        notes = [SCORED_FEATURES_NOTE]
        if pool_size is not None:
            notes.append(
                f"Your text query pre-selected {pool_size} candidate songs; "
                "songs outside those text matches were never scored."
            )
        genres = {s["genre"].casefold() for s in catalog}
        moods = {s["mood"].casefold() for s in catalog}
        if prefs["genre"] not in genres:
            notes.append(f"No songs in the catalog have genre '{prefs['genre']}'.")
        if prefs["mood"] not in moods:
            notes.append(f"No songs in the catalog have mood '{prefs['mood']}'.")
        return notes

    def explain(
        self,
        ranked: Ranked,
        candidates: Optional[Dict[int, Candidate]] = None,
        prefs: Optional[Dict] = None,
    ) -> List[Recommendation]:
        return self.explainer.explain(ranked, candidates, prefs)


# --- Orchestrator -----------------------------------------------------------

class Orchestrator:
    """Plans and tracks one workflow run; the user stays in control."""

    def __init__(
        self,
        catalog_path: str = "data/songs.csv",
        catalog_tool: Callable[[str], List[Dict]] = load_songs,
        recommend_tool: Callable[[Dict, List[Dict], int], Ranked] = recommend_songs,
        retriever_factory: Callable[[List[Dict]], Retriever] = Retriever,
        candidate_pool: int = DEFAULT_CANDIDATE_POOL,
        explainer: Optional[Explainer] = None,
    ):
        self.catalog_path = catalog_path
        self.catalog_tool = catalog_tool
        self.recommend_tool = recommend_tool
        self.retriever_factory = retriever_factory
        self.candidate_pool = candidate_pool
        self.preference_agent = PreferenceAgent()
        self.critic = CriticAgent()
        self.explainer = ExplanationAgent(explainer)
        self.runs: List[WorkflowRun] = []

    def run(self, request: Dict) -> WorkflowRun:
        run = WorkflowRun(run_id=len(self.runs) + 1, request=dict(request))
        self.runs.append(run)
        run.log("orchestrator", None, "ok", "plan: validate > catalog > recommend > verify > explain")

        # 1. Preference agent
        prefs, top_k, questions = self.preference_agent.validate(request)
        query, query_questions = self.preference_agent.validate_query(request)
        questions += query_questions
        if questions:
            run.status, run.questions = "needs_clarification", questions
            run.log("preference_agent", None, "failed", "; ".join(questions))
            return run
        run.log("preference_agent", None, "ok", f"normalized: {prefs}, top_k={top_k}")

        # 2. Catalog tool
        try:
            catalog = self.catalog_tool(self.catalog_path)
            if not catalog:
                raise ValueError("catalog is empty")
        except (OSError, ValueError, KeyError) as exc:
            run.log("orchestrator", "catalog", "failed", str(exc))
            return self._fail(run, f"Song catalog unavailable: {exc}")
        run.log("orchestrator", "catalog", "ok", f"{len(catalog)} songs")

        # 2b. Hybrid step: text retrieval narrows the pool, score_song reranks it.
        candidates: Optional[Dict[int, Candidate]] = None
        pool = catalog
        if query:
            found = self.retriever_factory(catalog).retrieve(
                query, n=max(self.candidate_pool, top_k)
            )
            run.log("orchestrator", "retriever", "ok" if found else "failed",
                    f"{len(found)} candidates for {query!r}")
            if not found:
                run.status = "no_match"
                run.questions = ["I couldn't find songs matching that description. Try rephrasing."]
                return run
            candidates = {c.song["id"]: c for c in found}
            pool = [c.song for c in found]

        # 3-4. Recommendation tool + critic, with exactly one retry
        ranked: Ranked = []
        problems: List[str] = []
        for attempt in (1, 2):
            ranked = self.recommend_tool(prefs, pool, top_k)
            run.log("orchestrator", "recommender", "ok", f"attempt {attempt}")
            problems = self.critic.verify(
                prefs, ranked, top_k, len(pool),
                allowed_ids=list(candidates) if candidates else None,
            )
            if not problems:
                run.log("critic", None, "ok", "ranking, scores and explanations verified")
                break
            run.log("critic", None, "failed" if attempt == 2 else "retry", "; ".join(problems))
            # Corrected inputs for the retry: fresh catalog copy, normalized prefs.
            catalog = self.catalog_tool(self.catalog_path)
            if not candidates:
                pool = catalog
        else:
            return self._fail(run, "Results failed verification: " + "; ".join(problems))

        # 5. Explanation agent
        run.recommendations = self.explainer.explain(ranked, candidates, prefs)
        run.limitations = self.explainer.limitations(
            prefs, catalog, len(pool) if candidates else None
        )
        by_llm = sum(r.generated_by == "llm" for r in run.recommendations)
        run.log("explanation_agent", None, "ok",
                f"{len(run.recommendations)} explained ({by_llm} by LLM, "
                f"{len(run.recommendations) - by_llm} by template)")
        run.status = "complete"
        return run

    def record_feedback(self, run: WorkflowRun, text: str) -> None:
        """Optional feedback is stored on the run; it never changes results by itself."""
        if text.strip():
            run.feedback.append(text.strip())
            run.log("orchestrator", None, "ok", "feedback recorded")

    def _fail(self, run: WorkflowRun, message: str) -> WorkflowRun:
        # Never return unverified recommendations.
        run.status, run.error, run.recommendations = "error", message, []
        return run
