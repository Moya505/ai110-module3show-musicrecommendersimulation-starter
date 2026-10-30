# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch Classroom Recommender**

## 2. Intended Use

This tool ranks songs by a user's genre, mood, and energy preferences.
It is for classroom learning and experimentation.
It assumes each user can be described by one genre, one mood, and one energy target.
It is not designed for real-world listening decisions.

## 3. How the Model Works

The model compares each song's genre and mood with the user's choices.
A genre match adds 2 points, and a mood match adds 1 point.
Energy similarity adds up to 1 point, using `1 - abs(song energy - target energy)`.
The model sorts songs by total score and returns the top results.
It explains each score with match and similarity reasons.
It uses genre, mood, and energy; it ignores the other song features.

## 4. Data

The catalog contains 20 songs.
It includes pop, lofi, rock, ambient, jazz, synthwave, and indie pop.
The moods are happy, chill, intense, relaxed, moody, and focused.
Ten songs were added to the starter catalog.
The catalog is small and does not represent all music styles or listeners.
It has no lyrics, listener ratings, or listening history.

## 5. Strengths

The model is easy to understand and explain.
It works well when a user's genre and mood appear in the catalog.
Energy similarity helps sort songs within a matching genre and mood.
The lofi/chill profile ranks lofi and chill songs near the top.
The pop/happy profile ranks pop and happy songs near the top.

## 6. Limitations and Bias

Genre is worth more than mood, so it can dominate the result.
In the conflicting profile, rock songs rank above chill songs.
Genre and mood matches are exact; related labels get no partial credit.
Energy uses a symmetric gap, so equally distant high and low energy receive the same score.
The model ignores tempo, valence, danceability, and acousticness.
Users with genres or moods missing from the catalog get no category-match points.
The small catalog limits variety and discovery.
Ties keep the original catalog order.

## 7. Evaluation

I tested seven profiles against all 20 songs.
I checked whether their top-five results matched the preferences and score reasons.
The profiles were High-Energy Pop, Chill Lofi, Deep Intense Rock, Conflicting Style and Mood, Unlisted Preferences, Minimum Energy, and Maximum Energy.
The conflicting profile surprised me: its rock preference outweighed its chill mood.
The unlisted profile still got recommendations, but only energy affected its scores.
The minimum-energy lofi profile kept lofi songs at the top because genre and mood bonuses outweighed energy distance.

### Pairwise Profile Comparisons

- **High-Energy Pop and Chill Lofi:** Pop and happy songs lead the first; lofi and chill songs lead the second.
- **High-Energy Pop and Deep Intense Rock:** Pop songs lead one list, while rock songs lead the other.
- **High-Energy Pop and Conflicting Style and Mood:** Pop leads the first; rock leads the conflict because genre earns 2 points.
- **High-Energy Pop and Unlisted Preferences:** Pop gets genre and mood points; unlisted preferences get energy points only.
- **High-Energy Pop and Minimum Energy:** High energy favors upbeat pop; the lofi/chill matches lead the low-energy profile.
- **High-Energy Pop and Maximum Energy:** The genre and mood changes move the lead from Sunrise City to Storm Runner.
- **Chill Lofi and Deep Intense Rock:** Library Rain leads the lofi profile; Storm Runner leads the rock profile.
- **Chill Lofi and Conflicting Style and Mood:** Lofi matches lead one; the rock bonus puts Storm Runner first in the conflict.
- **Chill Lofi and Unlisted Preferences:** Lofi gets genre and mood bonuses; unlisted preferences rely on energy similarity.
- **Chill Lofi and Minimum Energy:** Both favor lofi and chill, so their top three are the same; energy changes scores.
- **Chill Lofi and Maximum Energy:** Library Rain leads the first; high-energy rock leads the second.
- **Deep Intense Rock and Conflicting Style and Mood:** Both lead with Storm Runner; the conflict loses the mood point.
- **Deep Intense Rock and Unlisted Preferences:** Rock and intense matches lift Storm Runner; unlisted preferences have no category matches.
- **Deep Intense Rock and Minimum Energy:** Storm Runner leads the high-energy profile; Library Rain leads the low-energy one.
- **Deep Intense Rock and Maximum Energy:** Both rank Storm Runner first; the higher target energy changes scores slightly.
- **Conflicting Style and Mood and Unlisted Preferences:** Genre points put rock songs first in the conflict; energy alone ranks the unlisted profile.
- **Conflicting Style and Mood and Minimum Energy:** Rock leads the conflict; lofi leads the minimum-energy profile due to its category matches.
- **Conflicting Style and Mood and Maximum Energy:** Both favor high-energy rock; the mood point changes their scores and lower ranks.
- **Unlisted Preferences and Minimum Energy:** Unlisted preferences use energy alone; minimum energy also rewards lofi and chill matches.
- **Unlisted Preferences and Maximum Energy:** Energy near 0.5 leads the unlisted profile; rock, intense, high-energy songs lead the other.
- **Minimum Energy and Maximum Energy:** Low-energy lofi leads one; high-energy rock leads the other.

These are checks against a small, hand-labeled catalog.
They do not show whether real listeners would like the recommendations.

## 8. Future Work

I could add more songs and more genres.
I could let users set multiple genres and moods.
I could test different point weights.
I could use tempo, valence, danceability, and acousticness.
I could add a rule to make the top results more varied.
I could validate preferences and energy values before scoring.

## 9. Personal Reflection

I learned that small scoring choices can change a recommendation list.
Genre's larger point value can outweigh mood.
The explanations make those choices easier to notice.
Real recommendation systems need more data and more varied signals.
