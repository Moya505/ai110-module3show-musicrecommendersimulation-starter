from src.generate_agentic_workflow import (
    ENTITY_RELATIONSHIP_DIAGRAM,
    WORKFLOW_DIAGRAM,
    generate_diagrams,
)


def test_generate_diagrams_writes_workflow_and_entity_relationship_sources(tmp_path):
    workflow_path, entity_relationship_path = generate_diagrams(tmp_path)

    assert workflow_path.name == "agentic_music_workflow.mmd"
    assert entity_relationship_path.name == "agentic_music_entities.mmd"
    assert workflow_path.read_text(encoding="utf-8") == WORKFLOW_DIAGRAM
    assert (
        entity_relationship_path.read_text(encoding="utf-8")
        == ENTITY_RELATIONSHIP_DIAGRAM
    )


def test_entity_relationship_diagram_captures_workflow_and_recommendation_entities():
    assert "erDiagram" in ENTITY_RELATIONSHIP_DIAGRAM
    assert "USER_PREFERENCES" in ENTITY_RELATIONSHIP_DIAGRAM
    assert "AGENT_STEP" in ENTITY_RELATIONSHIP_DIAGRAM
    assert "TOOL o|--o{ AGENT_STEP" in ENTITY_RELATIONSHIP_DIAGRAM
    assert "WORKFLOW_RUN ||--o{ RECOMMENDATION" in ENTITY_RELATIONSHIP_DIAGRAM
    assert "SONG ||--o{ RECOMMENDATION" in ENTITY_RELATIONSHIP_DIAGRAM