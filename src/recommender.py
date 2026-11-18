import csv
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


@dataclass(frozen=True)
class PlaylistCriteria:
    """Validated, request-specific criteria for a playlist."""

    genres: Sequence[str] = ()
    moods: Sequence[str] = ()
    min_energy: Optional[float] = None
    max_energy: Optional[float] = None
    likes_acoustic: Optional[bool] = None
    song_count: Optional[int] = None
    duration_minutes: Optional[float] = None

    def __post_init__(self) -> None:
        for field_name in ("genres", "moods"):
            values = getattr(self, field_name)
            if isinstance(values, str) or not isinstance(values, Sequence):
                raise TypeError(f"{field_name} must be a sequence of strings")

            normalized = []
            seen = set()
            for value in values:
                if not isinstance(value, str):
                    raise TypeError(f"each {field_name} entry must be a string")
                label = value.strip()
                if not label:
                    raise ValueError(f"{field_name} entries cannot be empty")
                normalized_label = label.casefold()
                if normalized_label not in seen:
                    normalized.append(label)
                    seen.add(normalized_label)
            object.__setattr__(self, field_name, tuple(normalized))

        for field_name in ("min_energy", "max_energy"):
            value = getattr(self, field_name)
            if value is not None:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise TypeError(f"{field_name} must be a number between 0 and 1")
                if not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError(f"{field_name} must be between 0 and 1")
                object.__setattr__(self, field_name, float(value))

        if (
            self.min_energy is not None
            and self.max_energy is not None
            and self.min_energy > self.max_energy
        ):
            raise ValueError("min_energy cannot be greater than max_energy")

        if self.likes_acoustic is not None and not isinstance(self.likes_acoustic, bool):
            raise TypeError("likes_acoustic must be True, False, or None")

        if self.song_count is not None:
            if isinstance(self.song_count, bool) or not isinstance(self.song_count, int):
                raise TypeError("song_count must be a positive integer")
            if self.song_count <= 0:
                raise ValueError("song_count must be a positive integer")

        if self.duration_minutes is not None:
            if (
                isinstance(self.duration_minutes, bool)
                or not isinstance(self.duration_minutes, (int, float))
            ):
                raise TypeError("duration_minutes must be a positive number")
            if not math.isfinite(self.duration_minutes) or self.duration_minutes <= 0:
                raise ValueError("duration_minutes must be a positive number")
            object.__setattr__(self, "duration_minutes", float(self.duration_minutes))

        has_criteria = any(
            (
                self.genres,
                self.moods,
                self.min_energy is not None,
                self.max_energy is not None,
                self.likes_acoustic is not None,
                self.song_count is not None,
                self.duration_minutes is not None,
            )
        )
        if not has_criteria:
            raise ValueError("provide at least one playlist criterion")


def _song_to_dict(song: Song) -> Dict:
    return {
        "id": song.id, "title": song.title, "artist": song.artist,
        "genre": song.genre, "mood": song.mood, "energy": song.energy,
    }


class Recommender:
    """OOP wrapper around the same scoring recipe as score_song()."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    @staticmethod
    def _prefs(user: UserProfile) -> Dict:
        return {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
        }

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        prefs = self._prefs(user)
        ranked = sorted(  # sorted() is stable: ties keep catalog order
            self.songs,
            key=lambda s: score_song(prefs, _song_to_dict(s))[0],
            reverse=True,
        )
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        _, reasons = score_song(self._prefs(user), _song_to_dict(song))
        return ", ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file, converting numeric columns to numbers."""
    int_fields = {"id"}
    float_fields = {"energy", "tempo_bpm", "valence", "danceability", "acousticness"}
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for name in int_fields:
                row[name] = int(row[name])
            for name in float_fields:
                row[name] = float(row[name])
            songs.append(row)
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song (0-4): genre +2, mood +1, energy similarity 0-1."""
    score = 0.0
    reasons: List[str] = []

    if song["genre"].casefold() == str(user_prefs.get("genre", "")).casefold():
        score += 2.0
        reasons.append("genre match (+2.00)")
    if song["mood"].casefold() == str(user_prefs.get("mood", "")).casefold():
        score += 1.0
        reasons.append("mood match (+1.00)")

    similarity = max(0.0, 1 - abs(song["energy"] - user_prefs.get("energy", 0.0)))
    score += similarity
    reasons.append(f"energy similarity (+{similarity:.2f})")
    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Rank songs by score (ties keep catalog order) and return the top k."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        scored.append((song, score, ", ".join(reasons)))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
