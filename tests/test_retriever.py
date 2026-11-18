from pathlib import Path

import pytest

from src.recommender import load_songs
from src.retriever import (
    Embedder,
    Retriever,
    TfidfEmbedder,
    VectorIndex,
    cosine,
    song_document,
    tokenize,
)

CATALOG = Path(__file__).resolve().parent.parent / "data" / "songs.csv"

SONGS = [
    {"id": 1, "title": "Sunny Pop", "artist": "A", "genre": "pop", "mood": "happy",
     "energy": 0.8, "tempo_bpm": 120, "acousticness": 0.2, "description": "bright dance"},
    {"id": 2, "title": "Rain Loop", "artist": "B", "genre": "lofi", "mood": "chill",
     "energy": 0.3, "tempo_bpm": 70, "acousticness": 0.9, "description": "quiet study"},
    {"id": 3, "title": "Loud Riff", "artist": "C", "genre": "rock", "mood": "intense",
     "energy": 0.95, "tempo_bpm": 150, "acousticness": 0.1, "description": "heavy guitars"},
]


class FakeEmbedder(Embedder):
    """Deterministic keyword embedder: no corpus, no randomness, no network."""

    KEYWORDS = ("pop", "lofi", "rock", "study", "dance", "guitars")

    def __init__(self):
        self.fit_calls = []

    def fit(self, documents):
        self.fit_calls.append(len(documents))

    def embed(self, text):
        words = set(tokenize(text))
        vector = {k: 1.0 for k in self.KEYWORDS if k in words}
        norm = len(vector) ** 0.5
        return {k: v / norm for k, v in vector.items()}


# --- with a fake embedder (fully offline, fully predictable) ----------------

def test_retrieve_ranks_by_similarity_using_injected_embedder():
    retriever = Retriever(SONGS, embedder=FakeEmbedder())
    results = retriever.retrieve("lofi study", n=3)
    assert [c.song["id"] for c in results] == [2]  # others have similarity 0
    assert results[0].similarity == pytest.approx(1.0)


def test_embedder_is_fitted_once_with_every_document():
    fake = FakeEmbedder()
    Retriever(SONGS, embedder=fake)
    assert fake.fit_calls == [3]


def test_irrelevant_query_returns_no_candidates():
    assert Retriever(SONGS, embedder=FakeEmbedder()).retrieve("opera") == []


def test_blank_query_returns_no_candidates():
    assert Retriever(SONGS, embedder=FakeEmbedder()).retrieve("   ") == []


def test_n_limits_results_and_ties_keep_catalog_order():
    retriever = Retriever(SONGS, embedder=FakeEmbedder())
    results = retriever.retrieve("pop rock", n=2)
    assert [c.song["id"] for c in results] == [1, 3]  # equal scores, catalog order
    assert len(retriever.retrieve("pop rock", n=1)) == 1


def test_min_similarity_filters_weak_matches():
    retriever = Retriever(SONGS, embedder=FakeEmbedder(), min_similarity=0.9)
    assert [c.song["id"] for c in retriever.retrieve("pop dance")] == [1]


@pytest.mark.parametrize("n", [0, -1, 1.5, True, "3"])
def test_invalid_n_is_rejected(n):
    with pytest.raises(ValueError):
        Retriever(SONGS, embedder=FakeEmbedder()).retrieve("pop", n=n)


def test_candidate_carries_song_and_document():
    candidate = Retriever(SONGS, embedder=FakeEmbedder()).retrieve("rock")[0]
    assert candidate.song["title"] == "Loud Riff"
    assert "heavy guitars" in candidate.document


# --- documents, index, math ---------------------------------------------------

def test_song_document_turns_numbers_into_words_and_keeps_description():
    doc = song_document(SONGS[1])
    assert "low energy" in doc and "low tempo" in doc and "high acoustic" in doc
    assert "Genre: lofi" in doc and "quiet study" in doc


def test_song_document_works_without_description():
    song = {k: v for k, v in SONGS[0].items() if k != "description"}
    assert "Sunny Pop" in song_document(song)


def test_cosine_of_identical_normalized_vectors_is_one():
    v = {"a": 0.6, "b": 0.8}
    assert cosine(v, v) == pytest.approx(1.0)
    assert cosine(v, {"c": 1.0}) == 0.0


def test_empty_index_search_returns_nothing():
    assert VectorIndex().search({"a": 1.0}, 5) == []


# --- default TF-IDF embedder --------------------------------------------------

def test_tfidf_vectors_are_normalized_and_ignore_unknown_words():
    embedder = TfidfEmbedder()
    embedder.fit(["pop dance", "lofi study"])
    vec = embedder.embed("pop zzz")
    assert set(vec) == {"pop"}
    assert sum(v * v for v in vec.values()) == pytest.approx(1.0)
    assert embedder.embed("zzz") == {}


def test_tfidf_weights_rarer_terms_higher():
    embedder = TfidfEmbedder()
    embedder.fit(["common rare1", "common rare2", "common rare3"])
    vec = embedder.embed("common rare1")
    assert vec["rare1"] > vec["common"]


# --- real catalog with the default embedder (still offline) -------------------

@pytest.fixture(scope="module")
def catalog_retriever():
    return Retriever(load_songs(str(CATALOG)))


def test_catalog_study_query_finds_calm_lofi_or_ambient(catalog_retriever):
    top = catalog_retriever.retrieve("calm quiet music for studying", n=5)
    assert top
    assert {c.song["genre"] for c in top[:3]} <= {"lofi", "ambient", "classical"}


def test_catalog_workout_query_finds_high_energy_tracks(catalog_retriever):
    top = catalog_retriever.retrieve("high energy workout dance", n=5)
    assert top
    assert all(c.song["energy"] >= 0.6 for c in top[:3])


def test_catalog_gibberish_query_returns_nothing(catalog_retriever):
    assert catalog_retriever.retrieve("xqzv plorf") == []
