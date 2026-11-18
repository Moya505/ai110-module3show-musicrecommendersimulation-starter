import pytest

from src import evaluate
from src.recommender import load_songs


@pytest.fixture(scope="module")
def catalog():
    return load_songs(str(evaluate.CATALOG))


def test_all_profiles_run_cleanly_through_the_workflow(catalog):
    rows = evaluate.evaluate_profiles(catalog)
    assert len(rows) == 7
    for r in rows:
        assert r["status"] == "complete" and r["sorted"] and r["critic_ok"], r
        assert r["top_matches_expected"] in (True, None), r
    unlisted = next(r for r in rows if r["profile"] == "Unlisted Preferences")
    assert unlisted["limitation_flagged"]


def test_hybrid_is_no_worse_than_scorer_only_on_free_text(catalog):
    rows = evaluate.evaluate_queries(catalog)
    assert len(rows) >= 5
    mean = lambda key: sum(r[key] for r in rows) / len(rows)
    assert mean("hybrid_p") >= mean("scorer_p")
    assert mean("hybrid_p") >= 0.6          # loose floor to catch regressions
    assert mean("hybrid_hit") == 1.0        # every query gets >= 1 relevant song


def test_every_query_has_relevant_songs_in_catalog(catalog):
    for case in evaluate.QUERIES:
        assert any(case.relevant(s) for s in catalog), case.text


def test_grounding_check_is_correct_on_red_team(catalog):
    result = evaluate.evaluate_grounding(catalog)
    assert all(should == got for _, should, got in result["red_team"])
    assert result["template_ungrounded"] == 0


def test_gibberish_query_gives_no_match(catalog):
    assert evaluate.evaluate_no_match(catalog)


def test_report_builds_with_all_sections():
    report = evaluate.build_report()
    for heading in ("## 1. Profiles", "## 2. Free-text queries", "## 3. Grounding"):
        assert heading in report
