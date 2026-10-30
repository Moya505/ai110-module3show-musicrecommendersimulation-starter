"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs

USER_PROFILES = {
    "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.9},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.35},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.95},
    "Conflicting Style and Mood": {"genre": "rock", "mood": "chill", "energy": 0.9},
    "Unlisted Preferences": {"genre": "metal", "mood": "sad", "energy": 0.5},
    "Minimum Energy": {"genre": "lofi", "mood": "chill", "energy": 0.0},
    "Maximum Energy": {"genre": "rock", "mood": "intense", "energy": 1.0}
}


def main() -> None:
    songs = load_songs("data/songs.csv") 

    profile_name = "High-Energy Pop"
    user_prefs = USER_PROFILES[profile_name]
    recommendations = recommend_songs(user_prefs, songs, k=5)

    print(f"\nTop Recommendations for {profile_name}")
    print("=" * 60)
    for rank, rec in enumerate(recommendations, start=1):
        song, score, explanation = rec
        print(f"{rank}. {song['title']}")
        print(f"   Final score: {score:.2f} / 4.00")
        print("   Reasons:")
        for reason in explanation.split(", "):
            print(f"     - {reason}")
        print("-" * 60)


if __name__ == "__main__":
    main()
