"""
Offline evaluation of the music recommender.

    python3 src/evaluate.py            # prints a report
    python3 src/evaluate.py --write    # also writes docs/evaluation_results.md

Three parts, none of which need a network or API key:

1. PROFILES  - the 7 profiles in main.py run through the full workflow.
2. QUERIES   - free-text queries scored three ways: scorer only, retrieval
               only, and hybrid (retrieve 20, rerank with score_song).
3. GROUNDING - explanations are checked against their fact sheets, plus a
               small red-team set of good and bad "model" outputs.

Relevance for a query is defined by SONG ATTRIBUTES (mood, energy, genre...),
not by words in the description, so the retriever is not graded on the same
text it searches.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List

try:
    from .agent_workflow import Orchestrator
    from .explainer import LLMExplainer, check_grounding, fact_sheet
    from .recommender import load_songs, recommend_songs
    from .retriever import Retriever
except ImportError:  # run as a script from src/ or repo root
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from agent_workflow import Orchestrator
    from explainer import LLMExplainer, check_grounding, fact_sheet
    from recommender import load_songs, recommend_songs
    from retriever import Retriever

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "songs.csv"
K = 5

PROFILES = {
    "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.9},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.35},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.95},
    "Conflicting Style and Mood": {"genre": "rock", "mood": "chill", "energy": 0.9},
    "Unlisted Preferences": {"genre": "metal", "mood": "sad", "energy": 0.5},
    "Minimum Energy": {"genre": "lofi", "mood": "chill", "energy": 0.0},
    "Maximum Energy": {"genre": "rock", "mood": "intense", "energy": 1.0},
}
# What a sensible system should put first. None = no genre exists to match.
EXPECTED_TOP_GENRE = {
    "High-Energy Pop": "pop", "Chill Lofi": "lofi", "Deep Intense Rock": "rock",
    "Conflicting Style and Mood": "rock", "Unlisted Preferences": None,
    "Minimum Energy": "lofi", "Maximum Energy": "rock",
}


@dataclass(frozen=True)
class QueryCase:
    text: str
    prefs: Dict                       # structured prefs a user might also state
    relevant: Callable[[Dict], bool]  # attribute-based relevance judgment
    why: str


QUERIES: List[QueryCase] = [
    QueryCase("calm quiet music for studying",
              {"genre": "lofi", "mood": "focused", "energy": 0.35},
              lambda s: s["energy"] <= 0.45 and s["genre"] in {"lofi", "ambient", "classical"},
              "energy <= 0.45 and lofi/ambient/classical"),
    QueryCase("high energy workout dance music",
              {"genre": "pop", "mood": "intense", "energy": 0.9},
              lambda s: s["energy"] >= 0.8 and s["danceability"] >= 0.7,
              "energy >= 0.8 and danceability >= 0.7"),
    QueryCase("romantic dinner music",
              {"genre": "jazz", "mood": "romantic", "energy": 0.4},
              lambda s: s["mood"] == "romantic", "mood is romantic"),
    QueryCase("sad rainy day",
              {"genre": "lofi", "mood": "melancholy", "energy": 0.35},
              lambda s: s["mood"] == "melancholy" and s["energy"] <= 0.5,
              "melancholy and energy <= 0.5"),
    QueryCase("upbeat happy summer road trip",
              {"genre": "pop", "mood": "happy", "energy": 0.75},
              lambda s: s["mood"] == "happy" and s["energy"] >= 0.6,
              "happy and energy >= 0.6"),
    QueryCase("dark brooding night drive",
              {"genre": "synthwave", "mood": "moody", "energy": 0.7},
              lambda s: s["mood"] == "moody", "mood is moody"),
    QueryCase("relaxing acoustic evening",
              {"genre": "folk", "mood": "relaxed", "energy": 0.3},
              lambda s: s["acousticness"] >= 0.7 and s["energy"] <= 0.45,
              "acousticness >= 0.7 and energy <= 0.45"),
    QueryCase("nostalgic memories",
              {"genre": "folk", "mood": "nostalgic", "energy": 0.4},
              lambda s: s["mood"] == "nostalgic", "mood is nostalgic"),
]
GIBBERISH_QUERY = "xqzv plorf"

# (label, model output, should the grounding check accept it?)
RED_TEAM = [
    ("grounded sentence", "A calm lofi pick that fits your chill mood.", True),
    ("restates real score", "Scores 4.00 thanks to genre and mood matches.", True),
    ("invented BPM", "Great at 140 BPM for running.", False),
    ("invented rank claim", "Ranked #1 of 5000 songs worldwide.", False),
    ("fake quote", 'Described as "perfect for sleeping".', False),
    ("changed score", "Honestly this deserves 9.50 out of 10.", False),
    ("empty reply", "", False),
]


# --- helpers ------------------------------------------------------------------

def precision_at_k(songs: List[Dict], relevant: Callable[[Dict], bool], k: int = K) -> float:
    top = songs[:k]
    return sum(relevant(s) for s in top) / k if top else 0.0


def hit_at_k(songs: List[Dict], relevant: Callable[[Dict], bool], k: int = K) -> float:
    return float(any(relevant(s) for s in songs[:k]))


def evaluate_queries(catalog: List[Dict]) -> List[Dict]:
    retriever = Retriever(catalog)
    rows = []
    for case in QUERIES:
        n_relevant = sum(case.relevant(s) for s in catalog)
        scorer_only = [s for s, _, _ in recommend_songs(case.prefs, catalog, K)]
        retrieved = [c.song for c in retriever.retrieve(case.text, n=K)]
        pool = [c.song for c in retriever.retrieve(case.text, n=20)]
        hybrid = [s for s, _, _ in recommend_songs(case.prefs, pool, K)] if pool else []
        rows.append({
            "query": case.text, "relevant_in_catalog": n_relevant,
            **{f"{name}_p": precision_at_k(songs, case.relevant)
               for name, songs in (("scorer", scorer_only), ("retrieval", retrieved), ("hybrid", hybrid))},
            **{f"{name}_hit": hit_at_k(songs, case.relevant)
               for name, songs in (("scorer", scorer_only), ("retrieval", retrieved), ("hybrid", hybrid))},
            "pool": len(pool),
        })
    return rows


def evaluate_profiles(catalog: List[Dict]) -> List[Dict]:
    rows = []
    for name, prefs in PROFILES.items():
        orch = Orchestrator(str(CATALOG))
        run = orch.run({**prefs, "top_k": K})
        recs = run.recommendations
        expected = EXPECTED_TOP_GENRE[name]
        top_genre = recs[0].song["genre"] if recs else None
        scores = [r.score for r in recs]
        baseline_top = recommend_songs(prefs, catalog, 1)[0][0]["id"]
        rows.append({
            "profile": name,
            "status": run.status,
            "n": len(recs),
            "sorted": scores == sorted(scores, reverse=True),
            "critic_ok": any(s.agent == "critic" and s.status == "ok" for s in run.steps),
            "top_matches_expected": top_genre == expected if expected else None,
            "same_top_as_scorer": bool(recs) and recs[0].song["id"] == baseline_top,
            "limitation_flagged": any("No songs in the catalog" in n for n in run.limitations),
            "top": f"{recs[0].song['title']} ({top_genre})" if recs else "-",
        })
    return rows


def evaluate_grounding(catalog: List[Dict]) -> Dict:
    # (a) every template explanation across all profiles stays grounded.
    checked = ungrounded = 0
    for prefs in PROFILES.values():
        run = Orchestrator(str(CATALOG)).run({**prefs, "top_k": K})
        for rec in run.recommendations:
            reasons = rec.explanation.split(": ", 1)[1].split(" | ")[0]
            facts = fact_sheet(rec.song, rec.score, reasons, prefs, None)
            body = reasons  # the part derived from score_song
            checked += 1
            ungrounded += bool(check_grounding(body, facts))

    # (b) red team: does the checker accept good text and reject bad text?
    song = catalog[3]  # Library Rain
    ranked = [(song, 4.0, "genre match (+2.00), mood match (+1.00), energy similarity (+1.00)")]
    results = []
    for label, output, should_accept in RED_TEAM:
        llm = LLMExplainer(lambda system, user, o=output: o)
        rec = llm.explain(ranked, prefs=PROFILES["Chill Lofi"])[0]
        accepted = rec.generated_by == "llm"
        results.append((label, should_accept, accepted))
    return {"template_checked": checked, "template_ungrounded": ungrounded, "red_team": results}


def evaluate_no_match(catalog: List[Dict]) -> bool:
    run = Orchestrator(str(CATALOG)).run(
        {**PROFILES["Chill Lofi"], "top_k": K, "query": GIBBERISH_QUERY}
    )
    return run.status == "no_match" and not run.recommendations


# --- report -------------------------------------------------------------------

def build_report() -> str:
    catalog = load_songs(str(CATALOG))
    queries = evaluate_queries(catalog)
    profiles = evaluate_profiles(catalog)
    grounding = evaluate_grounding(catalog)
    no_match_ok = evaluate_no_match(catalog)

    out: List[str] = [f"# Evaluation results ({len(catalog)} songs, k={K})", ""]

    out += ["## 1. Profiles through the full workflow", "",
            "| Profile | Status | Results | Sorted | Critic ok | Top-1 | Top genre as expected | Gap flagged |",
            "|---|---|---|---|---|---|---|---|"]
    for r in profiles:
        exp = {True: "yes", False: "NO", None: "n/a"}[r["top_matches_expected"]]
        out.append(f"| {r['profile']} | {r['status']} | {r['n']} | {'yes' if r['sorted'] else 'NO'} "
                   f"| {'yes' if r['critic_ok'] else 'NO'} | {r['top']} | {exp} "
                   f"| {'yes' if r['limitation_flagged'] else '-'} |")
    ok = sum(r["status"] == "complete" and r["sorted"] and r["critic_ok"] for r in profiles)
    out += ["", f"Workflow healthy on {ok}/{len(profiles)} profiles.", ""]

    out += [f"## 2. Free-text queries (precision@{K} / hit@{K})", "",
            "| Query | Relevant in catalog | Scorer only | Retrieval only | Hybrid | Pool |",
            "|---|---|---|---|---|---|"]
    for q in queries:
        cells = " | ".join(f"{q[f'{n}_p']:.2f} / {int(q[f'{n}_hit'])}" for n in ("scorer", "retrieval", "hybrid"))
        out.append(f"| {q['query']} | {q['relevant_in_catalog']} | {cells} | {q['pool']} |")
    n = len(queries)
    means = {name: sum(q[f"{name}_p"] for q in queries) / n for name in ("scorer", "retrieval", "hybrid")}
    hits = {name: sum(q[f"{name}_hit"] for q in queries) / n for name in ("scorer", "retrieval", "hybrid")}
    out += ["", "| System | Mean precision@5 | Hit rate@5 |", "|---|---|---|"]
    for name, label in (("scorer", "Scorer only"), ("retrieval", "Retrieval only"), ("hybrid", "Hybrid")):
        out.append(f"| {label} | {means[name]:.2f} | {hits[name]:.2f} |")
    out += ["", f"Gibberish query returns no_match with no recommendations: {'yes' if no_match_ok else 'NO'}", ""]

    g = grounding
    out += ["## 3. Grounding", "",
            f"- Template explanations that stay within their facts: "
            f"{g['template_checked'] - g['template_ungrounded']}/{g['template_checked']}", "",
            "| Simulated model output | Should accept | Accepted | Correct |", "|---|---|---|---|"]
    for label, should, got in g["red_team"]:
        out.append(f"| {label} | {'yes' if should else 'no'} | {'yes' if got else 'no'} | {'yes' if should == got else 'NO'} |")
    correct = sum(should == got for _, should, got in g["red_team"])
    out += ["", f"Grounding check correct on {correct}/{len(g['red_team'])} red-team cases.", ""]
    return "\n".join(out)


def main() -> None:
    report = build_report()
    print(report)
    if "--write" in sys.argv:
        path = ROOT / "docs" / "evaluation_results.md"
        path.write_text(report, encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
