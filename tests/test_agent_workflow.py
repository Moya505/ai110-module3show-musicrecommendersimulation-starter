import pytest

from src.agent_workflow import Orchestrator
from src.recommender import recommend_songs

SONGS = [
    {"id": 1, "title": "A", "artist": "x", "genre": "pop", "mood": "happy", "energy": 0.8,
     "tempo_bpm": 120, "acousticness": 0.2, "description": "bright dance"},
    {"id": 2, "title": "B", "artist": "x", "genre": "lofi", "mood": "chill", "energy": 0.4,
     "tempo_bpm": 80, "acousticness": 0.8, "description": "quiet study"},
    {"id": 3, "title": "C", "artist": "x", "genre": "rock", "mood": "intense", "energy": 0.9,
     "tempo_bpm": 150, "acousticness": 0.1, "description": "heavy guitars"},
]
GOOD = {"genre": "Pop", "mood": "happy", "energy": 0.8, "top_k": 2}


def make(recommend_tool=recommend_songs, catalog=lambda _p: [dict(s) for s in SONGS]):
    return Orchestrator("ignored.csv", catalog_tool=catalog, recommend_tool=recommend_tool)


def test_happy_path_returns_verified_explained_results():
    run = make().run(GOOD)
    assert run.status == "complete"
    assert [r.song["title"] for r in run.recommendations][0] == "A"
    assert len(run.recommendations) == 2
    assert run.recommendations[0].explanation
    assert [s.step_order for s in run.steps] == list(range(1, len(run.steps) + 1))
    assert any(s.agent == "critic" and s.status == "ok" for s in run.steps)


@pytest.mark.parametrize("bad", [{}, {**GOOD, "energy": 1.5}, {**GOOD, "genre": " "}, {**GOOD, "top_k": 0}])
def test_invalid_preferences_ask_for_clarification(bad):
    run = make().run(bad)
    assert run.status == "needs_clarification"
    assert run.questions and not run.recommendations


def test_missing_catalog_reports_error_without_recommendations():
    def broken(_path):
        raise FileNotFoundError("nope.csv")

    run = make(catalog=broken).run(GOOD)
    assert run.status == "error" and not run.recommendations


def test_critic_triggers_exactly_one_retry_then_succeeds():
    calls = []

    def flaky(prefs, songs, k):
        calls.append(1)
        good = recommend_songs(prefs, songs, k)
        return good[::-1] if len(calls) == 1 else good  # unsorted on 1st try

    run = make(flaky).run(GOOD)
    assert len(calls) == 2 and run.status == "complete"
    assert [s.status for s in run.steps if s.agent == "critic"] == ["retry", "ok"]


def test_persistent_bad_results_are_never_returned():
    calls = []

    def always_bad(prefs, songs, k):
        calls.append(1)
        return recommend_songs(prefs, songs, k)[::-1]

    run = make(always_bad).run(GOOD)
    assert len(calls) == 2
    assert run.status == "error" and not run.recommendations


def test_unlisted_genre_is_reported_as_limitation_and_feedback_is_stored():
    orch = make()
    run = orch.run({**GOOD, "genre": "metal"})
    assert any("metal" in note for note in run.limitations)
    orch.record_feedback(run, "more mellow please")
    assert run.feedback == ["more mellow please"]


# --- hybrid retrieve-then-rerank ---------------------------------------------

from src.retriever import Embedder, Retriever, tokenize


class KeywordEmbedder(Embedder):
    """Fake embedder: a song 'matches' if its document contains the query word."""

    def embed(self, text):
        words = set(tokenize(text))
        return {w: 1.0 for w in words}


def hybrid(**kwargs):
    return Orchestrator(
        "ignored.csv",
        catalog_tool=lambda _p: [dict(s) for s in SONGS],
        retriever_factory=lambda songs: Retriever(songs, embedder=KeywordEmbedder()),
        **kwargs,
    )


def test_query_narrows_pool_then_score_song_reranks():
    # Prefs favor song A (pop/happy), but the query only matches lofi song B.
    run = hybrid().run({**GOOD, "query": "lofi", "top_k": 3})
    assert run.status == "complete"
    assert [r.song["title"] for r in run.recommendations] == ["B"]  # A never scored
    assert run.recommendations[0].similarity > 0
    assert run.recommendations[0].sources
    assert any("pre-selected" in note for note in run.limitations)
    assert any(s.tool == "retriever" and s.status == "ok" for s in run.steps)


def test_rerank_order_comes_from_score_song_not_similarity():
    run = hybrid().run({**GOOD, "query": "x pop lofi rock", "top_k": 3})
    # Retrieval only keeps songs whose text matches; ranking is the recipe's.
    titles = [r.song["title"] for r in run.recommendations]
    assert titles[0] == "A"
    scores = [r.score for r in run.recommendations]
    assert scores == sorted(scores, reverse=True)


def test_query_with_no_matches_returns_no_match_without_recommendations():
    run = hybrid().run({**GOOD, "query": "zzzz"})
    assert run.status == "no_match"
    assert run.questions and not run.recommendations


def test_no_query_keeps_original_behavior_and_skips_retriever():
    run = hybrid().run(GOOD)
    assert run.status == "complete"
    assert not any(s.tool == "retriever" for s in run.steps)
    assert run.recommendations[0].similarity is None


def test_non_text_query_asks_for_clarification():
    run = hybrid().run({**GOOD, "query": 42})
    assert run.status == "needs_clarification"


def test_critic_rejects_results_outside_retrieved_candidates():
    def ignores_pool(prefs, songs, k):
        return recommend_songs(prefs, [dict(s) for s in SONGS], k)  # full catalog

    run = hybrid(recommend_tool=ignores_pool).run({**GOOD, "query": "lofi", "top_k": 3})
    assert run.status == "error" and not run.recommendations
