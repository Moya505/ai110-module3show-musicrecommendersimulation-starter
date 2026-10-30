import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

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

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Load song records from a CSV file."""
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against the user's genre, mood, and energy preferences."""
    score = 0.0
    reasons = []

    if song["genre"].strip().casefold() == user_prefs["genre"].strip().casefold():
        score += 2.0
        reasons.append("genre match (+2.0)")
    else:
        reasons.append("genre mismatch (+0.0)")

    if song["mood"].strip().casefold() == user_prefs["mood"].strip().casefold():
        score += 1.0
        reasons.append("mood match (+1.0)")
    else:
        reasons.append("mood mismatch (+0.0)")

    energy_difference = abs(float(song["energy"]) - float(user_prefs["energy"]))
    energy_score = max(0.0, min(1.0, 1.0 - energy_difference))
    score += energy_score
    reasons.append(f"energy similarity (+{energy_score:.2f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Return the top-k songs ranked by score with explanations."""
    scored_songs = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        scored_songs.append((song, score, ", ".join(reasons)))

    ranked_songs = sorted(scored_songs, key=lambda recommendation: recommendation[1], reverse=True)
    return ranked_songs[:max(0, k)]
