
# Music Recommender: From Scoring Rule to Grounded, Agentic RAG Pipeline

## Original Project (Modules 1-3)

This project extends my **Music Recommender Simulation** from Modules 1-3. The original goal was to represent songs and a user "taste profile" as data, then design a scoring rule that turns them into ranked recommendations. It was a content-based, CLI-first recommender. Each song got up to 4 points: +2 for a genre match, +1 for a mood match, and up to +1 for energy similarity. The top K songs were returned with the reasons for each score.

## Title and Summary

**Music Recommender with Retrieval-Augmented Generation and an Agentic Workflow**

The system recommends songs from a 100-song catalog in two ways. A user can give structured preferences (genre, mood, target energy), a free-text request such as *"calm quiet music for studying"*, or both. Free-text requests are handled by a retrieval step that narrows the catalog before the original scorer ranks the results. A set of small agents validates the input, retrieves candidates, ranks them, checks the output, and explains each pick.

Why it matters: recommenders are often black boxes. Here the **score is always computed by deterministic code**, and any generated explanation is **checked against the facts** (score, rank, song attributes) before it is shown. If a language model is used and its wording invents a number or a claim, the system rejects it and falls back to a template. This keeps the explanations trustworthy.

## Architecture Overview

```
                  user request (genre / mood / energy  and/or  free-text query)
                                      |
                                      v
                          Orchestrator (runs and logs every step)
                                      |
   PreferenceAgent -> validates input, asks a clarifying question if it is unusable
                                      |
   Retriever (the "R" in RAG) -> TF-IDF vectors over song descriptions,
                                 cosine search -> candidate pool
                                      |
   Recommender -> score_song() ranks candidates (genre 2 + mood 1 + energy 1)
                                      |
   CriticAgent -> verifies sorting, score range, result count
                                      |
   ExplanationAgent -> TemplateExplainer (offline) or LLMExplainer (optional)
                                      |      each sentence is grounding-checked,
                                      |      and falls back to the template if it fails
                                      v
                   ranked recommendations + explanations + limitation notes
```

| Component | File | Role |
|---|---|---|
| Scoring and data | [src/recommender.py](src/recommender.py) | Loads `songs.csv`, defines `score_song` and `recommend_songs` |
| Retrieval | [src/retriever.py](src/retriever.py) | Turns each song into a text document, embeds it (offline TF-IDF, swappable), and does a cosine-similarity search |
| Explanation | [src/explainer.py](src/explainer.py) | Builds a fact sheet, wording from a template or LLM, `check_grounding` verifier |
| Agents | [src/agent_workflow.py](src/agent_workflow.py) | `PreferenceAgent`, `CriticAgent`, `ExplanationAgent`, and the `Orchestrator` that logs a step trail |
| Evaluation | [src/evaluate.py](src/evaluate.py) | Evaluation harness that writes [docs/evaluation_results.md](docs/evaluation_results.md) |
| Diagrams | [docs/](docs/) | Mermaid workflow and entity diagrams |

The diagrams can be regenerated with `python -m src.generate_agentic_workflow`.

## Setup Instructions

1. **Clone the repo and enter it**
   ```bash
   cd ai110-module3show-musicrecommendersimulation-starter
   ```
2. **(Optional) create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Mac/Linux
   .venv\Scripts\activate           # Windows
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the recommender.** `main.py` uses script-style imports, so run it as a file:
   ```bash
   python src/main.py
   ```
5. **Run the tests** (71 tests):
   ```bash
   python -m pytest tests
   ```
6. **Run the evaluation harness**
   ```bash
   python src/evaluate.py            # print the report
   python src/evaluate.py --write    # save to docs/evaluation_results.md
   ```
7. **(Optional) have an LLM word the explanations**
   ```bash
   pip install anthropic
   export ANTHROPIC_API_KEY=...
   python src/main.py --llm
   ```
   No API key is needed for steps 1-6. The default path is fully offline and reproducible.

## Sample Interactions

**1. Structured preferences: `genre=pop, mood=happy, energy=0.9`**
```
1. Confetti Day by Daybreak Club
   3.95/4.00: genre match (+2.00), mood match (+1.00), energy similarity (+0.95)
2. Sunrise City by Neon Echo
   3.92/4.00: genre match (+2.00), mood match (+1.00), energy similarity (+0.92)
3. Open Skies by Daybreak Club
   3.89/4.00: genre match (+2.00), mood match (+1.00), energy similarity (+0.89)
```

**2. Hybrid: Chill Lofi profile plus the text query `"calm quiet music for studying"`**
```
Note: Your text query pre-selected 9 candidate songs; songs outside those text matches were never scored.
1. Library Rain by Paper Lanterns
   4.00/4.00: genre match (+2.00), mood match (+1.00), energy similarity (+1.00) | text match 0.29
2. Study Hall by Paper Lanterns
   2.99/4.00: genre match (+2.00), energy similarity (+0.99) | text match 0.14
```
Retrieval picks the candidates, then the scorer ranks them. The system also tells the user that songs outside the retrieved pool were never scored.

**3. A preference the catalog can't satisfy: `genre=metal, mood=sad, energy=0.5`**
```
1. Pocket Sun by Fern Atlas       1.00/4.00: energy similarity (+1.00)
2. Smoky Backroom by Sunday Theory 1.00/4.00: energy similarity (+1.00)
```
No metal songs exist, so only energy can match. The result is flagged as a catalog gap instead of pretending to be a strong match.

## Design Decisions

- **Deterministic scoring stays the source of truth.** Agents plan, validate, and explain, but never invent a score. This makes every run reproducible and the output testable.
- **Offline TF-IDF retrieval instead of a hosted embedding model.** It needs no API key or network and is easy to inspect. The cost is that it matches words, not meaning, so a paraphrase with no shared vocabulary can miss. The `Embedder` interface lets a real embedding model replace it without changing the rest of the pipeline.
- **Hybrid retrieval, then rerank.** Retrieval alone is good at vibe queries, and the scorer alone is good at exact genre and mood. Combining them scored best in evaluation. The trade-off is that retrieval can exclude a song that the scorer would have liked, which is why the system states how many candidates were pre-selected.
- **Grounding check on LLM output.** Generated text is verified against a fact sheet and falls back to a template on any failure or error. This costs some fluency but prevents fabricated claims.
- **Genre weighted most heavily (2 of 4 points).** This is simple and easy to explain, but it can outweigh mood and energy (see Testing Summary).

## Testing Summary

**What worked**
- **71 automated tests pass** across the scorer, retriever, explainer, agents, evaluation harness, and diagram generator.
- The workflow completed healthily on **7 of 7** user profiles, including edge cases like minimum and maximum energy.
- Across 8 free-text queries (mean precision@5):

  | System | Mean precision@5 | Hit rate@5 |
  |---|---|---|
  | Scorer only | 0.50 | 1.00 |
  | Retrieval only | 0.80 | 1.00 |
  | **Hybrid** | **0.85** | 1.00 |

- All **35 of 35** template explanations stayed within their facts, and the grounding check handled **7 of 7** red-team cases (invented BPM, fake quote, changed score, empty reply, and so on). A gibberish query correctly returned `no_match`.

**What didn't work well**
- Queries with sparse vocabulary overlap, like *"sad rainy day"* (0.40 precision), retrieve poorly with TF-IDF.
- The "Conflicting Style and Mood" profile (rock + chill) ranked rock songs above chill ones. Genre's 2 points outweigh mood plus energy, so users whose mood matters more than genre are underserved.
- Only genre, mood, and energy are scored. Tempo, valence, danceability, and acousticness are ignored, and the system says so in its output.
- Running `python -m src.main` fails because of script-style imports, and I documented `python src/main.py` as the supported entry point.
- A duplicate nested copy of the project folder made `pytest` fail at collection, so tests are run with `python -m pytest tests`.

**What I learned**: evaluating the retrieval and the explanations separately showed where each part helps. Retrieval raised precision, and the grounding check addressed trust.

## Reflection

This project taught me that adding AI to a system is mostly about deciding what the AI should *not* control. Keeping the score deterministic and treating generated text as something to verify made the system easier to test, explain, and trust. Building the evaluation harness mattered as much as building the features, because the numbers showed me that retrieval helps, where it fails, and which of my assumptions were wrong. The deeper reflection on collaborating with AI, including a suggestion I accepted, one I revised, and the system's limitations, is in [model_card.md](model_card.md).
