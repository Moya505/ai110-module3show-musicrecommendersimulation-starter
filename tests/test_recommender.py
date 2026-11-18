import pytest

from src.recommender import PlaylistCriteria, Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_playlist_criteria_normalizes_genres_and_accepts_constraints():
    criteria = PlaylistCriteria(
        genres=[" pop ", "Pop", "indie pop"],
        moods=(" happy ",),
        min_energy=0.4,
        max_energy=0.9,
        likes_acoustic=False,
        song_count=10,
        duration_minutes=30,
    )

    assert criteria.genres == ("pop", "indie pop")
    assert criteria.moods == ("happy",)
    assert criteria.min_energy == 0.4
    assert criteria.max_energy == 0.9
    assert criteria.likes_acoustic is False
    assert criteria.song_count == 10
    assert criteria.duration_minutes == 30.0


@pytest.mark.parametrize(
    "criteria",
    [
        {},
        {"genres": (" ",)},
        {"min_energy": -0.1},
        {"max_energy": 1.1},
        {"min_energy": 0.8, "max_energy": 0.2},
        {"likes_acoustic": "yes"},
        {"song_count": 0},
        {"song_count": 1.5},
        {"duration_minutes": 0},
        {"duration_minutes": float("inf")},
    ],
)
def test_playlist_criteria_rejects_invalid_values(criteria):
    with pytest.raises((TypeError, ValueError)):
        PlaylistCriteria(**criteria)
