# Evaluation results (100 songs, k=5)

## 1. Profiles through the full workflow

| Profile | Status | Results | Sorted | Critic ok | Top-1 | Top genre as expected | Gap flagged |
|---|---|---|---|---|---|---|---|
| High-Energy Pop | complete | 5 | yes | yes | Confetti Day (pop) | yes | - |
| Chill Lofi | complete | 5 | yes | yes | Library Rain (lofi) | yes | - |
| Deep Intense Rock | complete | 5 | yes | yes | Wall of Noise (rock) | yes | - |
| Conflicting Style and Mood | complete | 5 | yes | yes | Storm Runner (rock) | yes | - |
| Unlisted Preferences | complete | 5 | yes | yes | Pocket Sun (indie pop) | n/a | yes |
| Minimum Energy | complete | 5 | yes | yes | Library Rain (lofi) | yes | - |
| Maximum Energy | complete | 5 | yes | yes | Wall of Noise (rock) | yes | - |

Workflow healthy on 7/7 profiles.

## 2. Free-text queries (precision@5 / hit@5)

| Query | Relevant in catalog | Scorer only | Retrieval only | Hybrid | Pool |
|---|---|---|---|---|---|
| calm quiet music for studying | 19 | 1.00 / 1 | 0.80 / 1 | 0.80 / 1 | 9 |
| high energy workout dance music | 13 | 1.00 / 1 | 0.80 / 1 | 0.80 / 1 | 20 |
| romantic dinner music | 8 | 0.20 / 1 | 1.00 / 1 | 1.00 / 1 | 8 |
| sad rainy day | 9 | 0.20 / 1 | 0.40 / 1 | 0.40 / 1 | 3 |
| upbeat happy summer road trip | 14 | 0.60 / 1 | 0.80 / 1 | 1.00 / 1 | 20 |
| dark brooding night drive | 9 | 0.20 / 1 | 0.80 / 1 | 1.00 / 1 | 10 |
| relaxing acoustic evening | 29 | 0.60 / 1 | 0.80 / 1 | 0.80 / 1 | 20 |
| nostalgic memories | 5 | 0.20 / 1 | 1.00 / 1 | 1.00 / 1 | 5 |

| System | Mean precision@5 | Hit rate@5 |
|---|---|---|
| Scorer only | 0.50 | 1.00 |
| Retrieval only | 0.80 | 1.00 |
| Hybrid | 0.85 | 1.00 |

Gibberish query returns no_match with no recommendations: yes

## 3. Grounding

- Template explanations that stay within their facts: 35/35

| Simulated model output | Should accept | Accepted | Correct |
|---|---|---|---|
| grounded sentence | yes | yes | yes |
| restates real score | yes | yes | yes |
| invented BPM | no | no | yes |
| invented rank claim | no | no | yes |
| fake quote | no | no | yes |
| changed score | no | no | yes |
| empty reply | no | no | yes |

Grounding check correct on 7/7 red-team cases.
