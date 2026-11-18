"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

Runs each profile through the agentic workflow (see agent_workflow.py).
"""

import sys

from agent_workflow import Orchestrator
from explainer import LLMExplainer, anthropic_generate

USER_PROFILES = {
    "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.9},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.35},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.95},
    "Conflicting Style and Mood": {"genre": "rock", "mood": "chill", "energy": 0.9},
    "Unlisted Preferences": {"genre": "metal", "mood": "sad", "energy": 0.5},
    "Minimum Energy": {"genre": "lofi", "mood": "chill", "energy": 0.0},
    "Maximum Energy": {"genre": "rock", "mood": "intense", "energy": 1.0}
}


def print_run(name: str, run) -> None:
    print(f"\nTop Recommendations for {name}")
    print("=" * 60)
    if run.status in ("needs_clarification", "no_match"):
        print("I need a bit more information:" if run.status == "needs_clarification" else "No match:")
        for question in run.questions:
            print(f"  - {question}")
    elif run.status == "error":
        print(f"Could not produce recommendations: {run.error}")
    else:
        for rec in run.recommendations:
            print(f"{rec.rank}. {rec.song['title']} by {rec.song['artist']}")
            print(f"   {rec.explanation}")
            print("-" * 60)
        for note in run.limitations:
            print(f"Note: {note}")
    print("Workflow steps: " + " > ".join(
        f"{s.agent}{'/' + s.tool if s.tool else ''}[{s.status}]" for s in run.steps))


def main() -> None:
    # Pass --llm to have a model word the explanations (needs `pip install
    # anthropic` and credentials). Output is checked against the facts and
    # falls back to the template if it doesn't pass.
    explainer = LLMExplainer(anthropic_generate()) if "--llm" in sys.argv else None
    orchestrator = Orchestrator("data/songs.csv", explainer=explainer)
    for name, prefs in USER_PROFILES.items():
        print_run(name, orchestrator.run({**prefs, "top_k": 5}))

    # Hybrid: free-text query picks candidates, score_song reranks them.
    query = "calm quiet music for studying"
    print_run(
        f"Chill Lofi + text query: {query!r}",
        orchestrator.run({**USER_PROFILES["Chill Lofi"], "top_k": 5, "query": query}),
    )


if __name__ == "__main__":
    main()
