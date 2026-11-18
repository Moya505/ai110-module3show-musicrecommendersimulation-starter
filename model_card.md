# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 2.0: Grounded Hybrid Music Recommender**

---

## 2. Intended Use

VibeMatch recommends songs from a small catalog. It accepts structured preferences (one genre, one mood, one target energy), a free-text request such as "calm quiet music for studying", or both. Each recommendation comes with an explanation.

- **Who it is for:** classroom learning and portfolio demonstration. It is not for real listening decisions or production use.
- **Assumptions about the user:** their taste can be summarized by one genre, one mood, and one energy level, and they can describe what they want in a few words.
- **Not intended for:** personalization from listening history, ranking real artists, or any decision that affects people's exposure or income.

---

## 3. How the Model Works

The system has three stages.

1. **Retrieve (optional).** If the user types a free-text request, the system compares it with a short text description of every song and keeps the closest matches as candidates. This uses word-overlap (TF-IDF) similarity and runs offline.
2. **Score.** Each candidate gets points: 2 for matching the preferred genre, 1 for matching the mood, and up to 1 for how close its energy is to the target, for a maximum of 4. Songs are sorted by total score, and ties keep catalog order.
3. **Explain and check.** Each pick gets a plain-language explanation. By default it is built from a template. Optionally a language model words it, but the text is then checked against the real score, rank, and song facts. If it contains anything not in those facts, the template is used instead.

A small set of rule-based "agents" validates the input, runs these steps, and verifies that the output is sorted and within range. They never change a score.

**What changed from the starter logic:** I added the retrieval step, the grounded explainer, the agent workflow with a step log, input validation, limitation notes shown to the user, a 100-song catalog, and an evaluation harness.

---

## 4. Data

- **Size:** 100 songs in `data/songs.csv`, which I expanded from the 20-song classroom version.
- **Genres (16):** pop 9, lofi 9, rock 7, jazz 7, classical 7, blues 7, ambient 6, synthwave 6, indie pop 6, country 6, hip hop 6, folk 5, rnb 5, edm 5, latin 5, reggae 4.
- **Moods (10):** happy 17, chill 12, energetic 12, melancholy 10, intense 9, relaxed 9, moody 9, focused 9, romantic 8, nostalgic 5.
- **Fields:** title, artist, genre, mood, energy, tempo, valence, danceability, acousticness, and a one-sentence text description used for retrieval.
- **What is missing:** lyrics, listener ratings, listening history, language or region, release year, and song duration. The songs and artists are invented for the simulation, not real catalog data. Genres such as metal, K-pop, and Afrobeats do not appear, and the catalog is skewed toward pop and lofi.

---

## 5. Strengths

- **Transparent:** every score can be traced to genre, mood, and energy points, and the explanation shows them.
- **Reproducible:** the default path uses no network or model, so the same input always gives the same output.
- **Retrieval helps vibe-based requests.** Across 8 free-text test queries, mean precision@5 was 0.50 for the scorer alone, 0.80 for retrieval alone, and **0.85 for the hybrid**. "Romantic dinner music" and "nostalgic memories" went from 0.20 to 1.00 once retrieval was added.
- **Honest about gaps:** a gibberish query returns `no_match` instead of random songs, and a preference that has no match in the catalog (metal/sad) is flagged.
- **Trustworthy explanations:** all 35 template explanations stayed within their facts, and the grounding check rejected 7 of 7 fabricated model outputs.

---

## 6. Limitations and Bias

- **Genre dominates.** A genre match is worth 2 points, which is as much as the maximum mood and energy points combined. In the "Conflicting Style and Mood" test (rock + chill), rock songs ranked above chill songs even though the user asked for chill. This disadvantages people whose mood matters more than genre.
- **Exact-match labels.** Related genres (indie pop and pop) or moods (relaxed and chill) get no partial credit.
- **Ignored features.** Tempo, valence, danceability, and acousticness never affect the score. The system says so in its output.
- **Retrieval matches words, not meaning.** "Sad rainy day" only reached 0.40 precision because the song descriptions don't share much vocabulary with it. Paraphrases can miss.
- **Retrieval can hide good songs.** In hybrid mode, songs outside the retrieved pool are never scored. The system tells the user how many candidates were pre-selected.
- **Narrow profile.** One genre, mood, and energy cannot represent varied or changing taste.
- **Catalog bias.** Underrepresented genres (reggae 4, folk 5) have fewer chances to appear, and users whose taste is missing from the catalog get weaker, energy-only results.
- **Synthetic, author-labeled data.** The genre and mood labels are my own judgments, so the evaluation partly reflects my assumptions.
- **Optional LLM path.** The grounding check catches invented numbers and claims, but it does not guarantee that the wording is good or free of subtle bias.

---

## 7. Evaluation

I used four kinds of checks, all reproducible with `python src/evaluate.py` (full results in [docs/evaluation_results.md](docs/evaluation_results.md)).

1. **Unit tests:** 71 automated tests pass across the scorer, retriever, explainer, agents, and evaluation code.
2. **Profile checks (7 profiles):** High-Energy Pop, Chill Lofi, Deep Intense Rock, Conflicting Style and Mood, Unlisted Preferences, Minimum Energy, and Maximum Energy. The workflow was healthy on 7 of 7. Results were sorted, passed the critic, and the top genre matched expectations, with the catalog-gap profile flagged as intended.
3. **Free-text retrieval (8 queries):** I hand-labeled which songs were relevant for each query and compared scorer-only, retrieval-only, and hybrid. Hybrid had the best mean precision@5 (0.85), and all three had a 1.00 hit rate.
4. **Grounding red-team (7 cases):** I fed the checker a good sentence, a sentence restating the real score, and five bad ones (invented BPM, invented rank claim, fake quote, changed score, empty reply). It judged all 7 correctly.

**What surprised me:**
- The rock + chill conflict showed how much one weight can decide the outcome.
- For "Unlisted Preferences" (metal/sad), the system still returned confident-looking results even though only energy mattered, which is why the gap warning matters.
- A minimum-energy lofi profile still ranked lofi first, because the genre and mood bonuses outweighed the energy distance.

**Caveat:** these are checks against a small, hand-labeled catalog. They do not show whether real listeners would like the recommendations.

---

## 8. Future Work

- Replace TF-IDF with a real embedding model through the existing `Embedder` interface, to handle paraphrases like "sad rainy day".
- Allow multiple genres and moods, give partial credit for related labels, and tune the weights (for example, lower the genre weight).
- Use tempo, valence, danceability, and acousticness in the score.
- Add a diversity rule so the top 5 aren't all from one artist or genre.
- Add song duration so the playlist-length criteria in `PlaylistCriteria` can be enforced.
- Use the stored user feedback to adjust results over time.
- Expand and balance the catalog, and have someone other than me label a sample of it.

---

## 9. Personal Reflection

### What I learned about recommenders and AI

Small design choices, such as a genre weight of 2, shape who gets good recommendations. A recommender can feel "smart" while mostly reflecting what its designer chose to score. The most useful part of the project was separating what code decides (scores and rankings) from what AI is allowed to say** (wording that is checked against facts). It made the system easier to test and made failures visible.

### How I collaborated with AI

<!-- TODO (Jamoya): confirm or replace the items below with what actually happened in your sessions. -->

- **Where AI helped:** drafting the retriever, explainer, agent workflow, and tests, and writing the evaluation harness.
- **One suggestion I accepted:** `[describe a specific AI suggestion you used. Candidate: checking LLM-written explanations against a fact sheet and falling back to a template.]` **Why:** `[your reason]`
- **One suggestion I rejected or revised:** `[describe a specific suggestion you changed or declined, and why. Candidate: using a hosted embedding model for retrieval, which I replaced with offline TF-IDF so the project runs without keys and results are reproducible.]`
- **What I checked by hand:** I ran the tests and the evaluation report myself and read the sample outputs, rather than trusting that the generated code worked. For example, I found that `python -m src.main` fails because of script-style imports, so the README documents `python src/main.py`.

### What I would tell another student

Build the evaluation before you trust the output. The numbers (0.50 vs 0.85 precision) told me more than my sense that the system "looked right".
