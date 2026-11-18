"""Generate Mermaid diagrams for the proposed agentic music recommender."""

from pathlib import Path


WORKFLOW_DIAGRAM = """\
flowchart TD
    user[User: preferences, top K, and optional feedback]
    planner[Orchestrator agent: plan and track workflow]
    validator[Preference agent: validate and normalize inputs]
    clarification{Are preferences complete and valid?}
    ask[Ask user to clarify or correct preferences]
    catalog[Catalog tool: load songs.csv]
    catalog_check{Is the catalog available?}
    recommender[Recommendation tool: score and rank songs]
    critic[Critic agent: verify ranking, scores, and explanations]
    quality_check{Do results pass checks?}
    retry_budget{Has the retry already been used?}
    retry[Retry once with corrected tool inputs]
    explainer[Explanation agent: summarize grounded match reasons]
    results[Return recommendations and limitations]
    feedback[Collect optional user feedback for the next request]
    error[Report the issue; do not return unverified recommendations]

    user --> planner
    planner --> validator
    validator --> clarification
    clarification -- No --> ask
    ask --> user
    clarification -- Yes --> catalog
    catalog --> catalog_check
    catalog_check -- No --> error
    catalog_check -- Yes --> recommender
    recommender --> critic
    critic --> quality_check
    quality_check -- No --> retry_budget
    retry_budget -- No --> retry
    retry --> recommender
    quality_check -- Yes --> explainer
    retry_budget -- Yes --> error
    explainer --> results
    results --> feedback
    feedback -. Next request; user remains in control .-> planner

    subgraph tools[Existing deterministic system tools]
        catalog
        recommender
    end
"""

ENTITY_RELATIONSHIP_DIAGRAM = """\
erDiagram
    USER {
        int user_id PK
    }
    USER_PREFERENCES {
        int preference_id PK
        int user_id FK
        string favorite_genre
        string favorite_mood
        float target_energy
        boolean likes_acoustic
    }
    RECOMMENDATION_REQUEST {
        int request_id PK
        int user_id FK
        int preference_id FK
        int top_k
    }
    WORKFLOW_RUN {
        int run_id PK
        int request_id FK
        string status
    }
    AGENT {
        int agent_id PK
        string name
        string responsibility
    }
    TOOL {
        int tool_id PK
        string name
        string purpose
    }
    AGENT_STEP {
        int step_id PK
        int run_id FK
        int agent_id FK
        int tool_id FK "optional"
        int step_order
        string status
    }
    SONG {
        int song_id PK
        string title
        string artist
        string genre
        string mood
        float energy
        float tempo_bpm
        float valence
        float danceability
        float acousticness
    }
    RECOMMENDATION {
        int recommendation_id PK
        int run_id FK
        int song_id FK
        int rank
        float score
        string explanation
    }
    USER_FEEDBACK {
        int feedback_id PK
        int run_id FK
        string feedback_text
    }

    USER ||--|| USER_PREFERENCES : configures
    USER ||--o{ RECOMMENDATION_REQUEST : submits
    USER_PREFERENCES ||--o{ RECOMMENDATION_REQUEST : supplies
    RECOMMENDATION_REQUEST ||--|| WORKFLOW_RUN : starts
    WORKFLOW_RUN ||--|{ AGENT_STEP : records
    AGENT ||--o{ AGENT_STEP : executes
    TOOL o|--o{ AGENT_STEP : invoked_by
    WORKFLOW_RUN ||--o{ RECOMMENDATION : produces
    SONG ||--o{ RECOMMENDATION : appears_in
    WORKFLOW_RUN ||--o| USER_FEEDBACK : may_receive
"""

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "docs"
WORKFLOW_PATH = OUTPUT_DIR / "agentic_music_workflow.mmd"
ENTITY_RELATIONSHIP_PATH = OUTPUT_DIR / "agentic_music_entities.mmd"


def generate_diagrams(output_dir: Path = OUTPUT_DIR) -> tuple[Path, Path]:
    """Write the workflow and entity-relationship Mermaid sources."""
    output_dir.mkdir(parents=True, exist_ok=True)
    workflow_path = output_dir / WORKFLOW_PATH.name
    entity_relationship_path = output_dir / ENTITY_RELATIONSHIP_PATH.name
    workflow_path.write_text(WORKFLOW_DIAGRAM, encoding="utf-8")
    entity_relationship_path.write_text(
        ENTITY_RELATIONSHIP_DIAGRAM, encoding="utf-8"
    )
    return workflow_path, entity_relationship_path


def main() -> None:
    workflow_path, entity_relationship_path = generate_diagrams()
    print(f"Generated agentic workflow diagram: {workflow_path}")
    print(f"Generated entity-relationship diagram: {entity_relationship_path}")


if __name__ == "__main__":
    main()
