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
------------------------------------------------------------

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this
