# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world recommendation platforms combine content-based signals (similarities between songs or videos) with collaborative signals (what people with similar behavior enjoy). They also learn from interactions such as plays, skips, likes, and watch time, and may account for context. This simulation focuses on a simpler content-based approach: it compares a user's stated preferences with each song's genre, mood, energy, and acoustic character, then ranks songs by how well they match. It does not model other users or learn from listening history.

The simulation uses these features:

- **`Song`**: `id`, `title`, `artist`, `genre`, `mood`, `energy`, `tempo_bpm`, `valence`, `danceability`, and `acousticness`. The ID, title, and artist identify or describe a track; the remaining fields describe its style and sound.
- **`UserProfile`**: `favorite_genre`, `favorite_mood`, `target_energy`, and `likes_acoustic`.

The scoring recipe below defines how the simulation will compare songs with the user's preferences and rank the strongest matches.

The intended system compares each song’s genre, mood, and energy with the user’s preferences. It awards 2 points for a genre match, 1 for a mood match, and up to 1 point for energy similarity. It then sorts songs by total score and returns the top K. Although the Song data includes other features—such as tempo and acousticness—the documented scoring recipe does not use them.

Potential biases and limitations:

Genre is strongly prioritized: its 2 points equal the maximum combined mood and energy points, so a genre match can outweigh a strong mood-and-energy match.
Exact-match categories are inflexible: a related genre or mood gets no partial credit, even if it might appeal to the user.
The profile is narrow: one preferred genre, mood, and energy target may not capture someone’s varied or changing taste.
Unscored features are ignored: acousticness, tempo, danceability, and valence cannot affect recommendations under this recipe.
The catalog limits discovery: songs missing from the CSV cannot be recommended, and ties retain catalog order rather than using another preference signal.
### Data Flow

```text
Input: User preferences (genre, mood, target energy) + songs.csv
                         |
                         v
Process: For each song, compare its genre and mood to the preferences,
         calculate energy similarity, and add the points
                         |
                         v
Collect: Keep each song together with its total score
                         |
                         v
Ranking: Sort by score, highest first (keep catalog order for ties)
                         |
                         v
Output: Return the top K songs as recommendations
```

### Scoring Recipe

For each song, start at 0 points and add:

- **+2.0 points** if the song's genre matches the user's preferred genre; otherwise, add 0.
- **+1.0 point** if the song's mood matches the user's preferred mood; otherwise, add 0.
- **0 to 1 similarity points** for energy, calculated as `1 - abs(song energy - target energy)`. Energy values are on a 0-to-1 scale, so an exact match earns 1 point and the greatest possible difference earns 0.

Add these points to get a total score from 0 to 4, then rank songs from highest to lowest and recommend the top results. Genre is weighted most heavily, mood next, and energy similarity breaks ties or boosts songs with a closer energy level. If totals tie, keep the songs in their original catalog order.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Top Recommendations
============================================================
1. Open Skies
   Final score: 3.99 / 4.00
   Reasons:
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+0.99)
------------------------------------------------------------
2. Sunrise City
   Final score: 3.98 / 4.00
   Reasons:
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+0.98)
------------------------------------------------------------
3. Weekend Motion
   Final score: 2.90 / 4.00
   Reasons:
     - genre match (+2.0)
     - mood mismatch (+0.0)
     - energy similarity (+0.90)
------------------------------------------------------------
4. Gym Hero
   Final score: 2.87 / 4.00
   Reasons:
     - genre match (+2.0)
     - mood mismatch (+0.0)
     - energy similarity (+0.87)
------------------------------------------------------------
5. Rooftop Lights
   Final score: 1.96 / 4.00
   Reasons:
     - genre mismatch (+0.0)
     - mood match (+1.0)
     - energy similarity (+0.96)
     ---------------------------------------
     High-Energy Pop
1. Sunrise City — 3.92 (genre match, mood match, energy +0.92)
2. Open Skies — 3.89 (genre match, mood match, energy +0.89)
3. Weekend Motion — 3.00 (genre match, mood mismatch, energy +1.00)
4. Gym Hero — 2.97 (genre match, mood mismatch, energy +0.97)
5. Rooftop Lights — 1.86 (genre mismatch, mood match, energy +0.86)

Chill Lofi
1. Library Rain — 4.00 (genre match, mood match, energy +1.00)
2. Soft Focus — 3.97 (genre match, mood match, energy +0.97)
3. Midnight Coding — 3.93 (genre match, mood match, energy +0.93)
4. Quiet Pages — 2.97 (genre match, mood mismatch, energy +0.97)
5. Focus Flow — 2.95 (genre match, mood mismatch, energy +0.95)

Deep Intense Rock
1. Storm Runner — 3.96 (genre match, mood match, energy +0.96)
2. After the Rain — 2.73 (genre match, mood mismatch, energy +0.73)
3. Gym Hero — 1.98 (genre mismatch, mood match, energy +0.98)
4. Weekend Motion — 1.95 (genre mismatch, mood match, energy +0.95)
5. Neon Sprint — 1.93 (genre mismatch, mood match, energy +0.93)

Conflicting Style and Mood
1. Storm Runner — 2.99 (genre match, mood mismatch, energy +0.99)
2. After the Rain — 2.78 (genre match, mood mismatch, energy +0.78)
3. Midnight Coding — 1.52 (genre mismatch, mood match, energy +0.52)
4. Soft Focus — 1.48 (genre mismatch, mood match, energy +0.48)
5. Library Rain — 1.45 (genre mismatch, mood match, energy +0.45)

Unlisted Preferences
1. Blue Lantern — 0.94 (both mismatched, energy +0.94)
2. Midnight Coding — 0.92 (both mismatched, energy +0.92)
3. Amber Room — 0.91 (both mismatched, energy +0.91)
4. Focus Flow — 0.90 (both mismatched, energy +0.90)
5. Soft Focus — 0.88 (both mismatched, energy +0.88)

Minimum Energy
1. Library Rain — 3.65 (genre match, mood match, energy +0.65)
2. Soft Focus — 3.62 (genre match, mood match, energy +0.62)
3. Midnight Coding — 3.58 (genre match, mood match, energy +0.58)
4. Quiet Pages — 2.68 (genre match, mood mismatch, energy +0.68)
5. Focus Flow — 2.60 (genre match, mood mismatch, energy +0.60)

Maximum Energy
1. Storm Runner — 3.91 (genre match, mood match, energy +0.91)
2. After the Rain — 2.68 (genre match, mood mismatch, energy +0.68)
3. Gym Hero — 1.93 (genre mismatch, mood match, energy +0.93)
4. Weekend Motion — 1.90 (genre mismatch, mood match, energy +0.90)
5. Neon Sprint — 1.88 (genre mismatch, mood match, energy +0.88)
------------------------------------------------------------

---

## Experiments You Tried

I compared seven profiles: High-Energy Pop, Chill Lofi, Deep Intense Rock, Conflicting Style and Mood, Unlisted Preferences, Minimum Energy, and Maximum Energy. The top songs changed when genre, mood, or target energy changed. For example, High-Energy Pop ranked *Sunrise City* first, while Chill Lofi ranked *Library Rain* first.

I also temporarily removed the mood points and tested the conflicting rock-and-chill profile. The rock songs stayed on top because they earned genre points, with energy similarity deciding their order. The total score range changed from 0–4 to 0–3, which confirmed that removing a one-point feature lowers the maximum by one. I restored the mood rule after the comparison.

---

## Limitations and Risks

- The catalog has only 20 songs, so many genres and moods are missing.
- Genre is worth 2 points, so it can outweigh a mood match.
- Genre and mood matches must be exact; related labels get no credit.
- Energy similarity treats equal gaps above and below the target the same.
- Tempo, valence, danceability, and acousticness do not affect recommendations.
- The system does not use lyrics, listening history, or feedback from other users.
- Users whose preferences are absent from the catalog may receive weak matches.
- Tied scores keep the catalog's original order, which can favor earlier entries.

---

## Reflection

I learned that a recommender turns user preferences and song features into scores, then uses those scores to rank choices. Even a small change to the scoring weights can change which songs appear first. The explanations help show why each song was recommended.

The experiments showed that scoring rules can favor some preferences over others. In my system, genre has more weight than mood, and users with unlisted genres or moods receive no points for those features. A larger catalog, more flexible preferences, and more varied signals could make recommendations fairer and more useful.
