"""
Retrieval step for the music recommender (the "R" in RAG).

    songs --> song_document() --> Embedder --> VectorIndex
    query --> Embedder --> VectorIndex.search() --> Candidates

The default TfidfEmbedder is pure Python and fully offline. Anything that
implements the Embedder interface (a sentence-transformer, an API model, or
a fake in tests) can be swapped in without changing Retriever.

Vectors are sparse mappings {feature: weight}. A dense embedding can be
passed as {index: value}.
"""

import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Hashable, List, Mapping, Optional, Sequence

Vector = Mapping[Hashable, float]

_STOPWORDS = frozenset(
    "a an and are as at be by for from in into is it its of on or that the "
    "this to with some something music song songs track".split()
)


@dataclass(frozen=True)
class Candidate:
    song: Dict
    document: str
    similarity: float


# --- Documents ----------------------------------------------------------------

def _band(value: float, low: float, high: float) -> str:
    return "low" if value < low else "high" if value >= high else "medium"


def song_document(song: Dict) -> str:
    """Text that gets embedded for one song.

    Numeric columns are turned into words so that a query like "high energy"
    or "acoustic" can match features the scorer ignores.
    """
    parts = [
        f"{song['title']} by {song['artist']}.",
        f"Genre: {song['genre']}. Mood: {song['mood']}.",
        f"{_band(song['energy'], 0.4, 0.7)} energy,",
        f"{_band(song['tempo_bpm'], 85, 120)} tempo,",
        f"{_band(song['acousticness'], 0.35, 0.65)} acoustic.",
    ]
    description = str(song.get("description", "")).strip()
    if description:
        parts.append(description)
    return " ".join(parts)


# --- Embedders ----------------------------------------------------------------

class Embedder(ABC):
    """Turns text into a vector. fit() lets corpus-based embedders learn."""

    def fit(self, documents: Sequence[str]) -> None:
        """Called once with every document before indexing. Optional."""

    @abstractmethod
    def embed(self, text: str) -> Vector:
        ...


def tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9]+", text.casefold())
    return [t for t in tokens if t not in _STOPWORDS]


def _normalize(vector: Dict[Hashable, float]) -> Dict[Hashable, float]:
    norm = math.sqrt(sum(v * v for v in vector.values()))
    return {k: v / norm for k, v in vector.items()} if norm else {}


class TfidfEmbedder(Embedder):
    """Offline TF-IDF vectors, L2-normalized so dot product is cosine."""

    def __init__(self) -> None:
        self._idf: Dict[str, float] = {}

    def fit(self, documents: Sequence[str]) -> None:
        doc_freq: Counter = Counter()
        for doc in documents:
            doc_freq.update(set(tokenize(doc)))
        total = len(documents)
        # Smoothed IDF: always positive, rare terms weigh more.
        self._idf = {
            term: math.log((1 + total) / (1 + df)) + 1 for term, df in doc_freq.items()
        }

    def embed(self, text: str) -> Vector:
        counts = Counter(t for t in tokenize(text) if t in self._idf)
        return _normalize({t: c * self._idf[t] for t, c in counts.items()})


# --- Index --------------------------------------------------------------------

def cosine(a: Vector, b: Vector) -> float:
    """Dot product; equals cosine similarity for normalized vectors."""
    if len(a) > len(b):
        a, b = b, a
    return sum(weight * b.get(key, 0.0) for key, weight in a.items())


class VectorIndex:
    """Brute-force in-memory index. Fine for hundreds of songs."""

    def __init__(self) -> None:
        self._entries: List[tuple] = []  # (song, vector, document)

    def __len__(self) -> int:
        return len(self._entries)

    def add(self, song: Dict, vector: Vector, document: str) -> None:
        self._entries.append((song, vector, document))

    def search(self, vector: Vector, n: int) -> List[Candidate]:
        scored = [
            Candidate(song, document, cosine(vector, stored))
            for song, stored, document in self._entries
        ]
        # sorted() is stable, so equal similarities keep catalog order.
        scored.sort(key=lambda c: c.similarity, reverse=True)
        return scored[:n]


# --- Retriever ----------------------------------------------------------------

class Retriever:
    def __init__(
        self,
        songs: Sequence[Dict],
        embedder: Optional[Embedder] = None,
        min_similarity: float = 0.0,
    ):
        self.embedder = embedder or TfidfEmbedder()
        self.min_similarity = min_similarity
        self.index = VectorIndex()

        documents = [song_document(song) for song in songs]
        self.embedder.fit(documents)
        for song, document in zip(songs, documents):
            self.index.add(song, self.embedder.embed(document), document)

    def retrieve(self, query: str, n: int = 20) -> List[Candidate]:
        """Top n songs by similarity. Songs at or below min_similarity are
        dropped, so an unrelated query returns [] instead of random songs."""
        if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
            raise ValueError("n must be a positive integer")
        if not isinstance(query, str) or not query.strip():
            return []

        vector = self.embedder.embed(query)
        return [
            c for c in self.index.search(vector, n) if c.similarity > self.min_similarity
        ]
