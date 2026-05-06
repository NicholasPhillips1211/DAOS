from dataclasses import dataclass
import json


@dataclass(slots=True)
class PipelineBlueprint:
    """Simple in-memory representation of a pipeline draft."""

    name: str
    steps: list[dict[str, str]]


class PipelineService:
    def normalize_step(self, step_type: str) -> str:
        """Normalize step names so pipeline definitions compare reliably."""

        return step_type.strip().lower()

    def validate_definition_json(self, definition_json: str) -> str:
        """Validate and canonicalize a pipeline definition JSON blob.

        The route layer stores normalized JSON so pipeline versioning and diffs
        stay predictable across edits.
        """

        definition = json.loads(definition_json)
        if not isinstance(definition, dict):
            raise ValueError("Pipeline definition must be a JSON object")
        nodes = definition.get("nodes")
        edges = definition.get("edges")
        if not isinstance(nodes, list) or not nodes:
            raise ValueError("Pipeline definition must include at least one node")
        if not isinstance(edges, list):
            raise ValueError("Pipeline definition edges must be a list")

        node_ids = {node.get("id") for node in nodes if isinstance(node, dict)}
        if None in node_ids:
            raise ValueError("Each pipeline node must include an id")
        for edge in edges:
            if not isinstance(edge, dict):
                raise ValueError("Each pipeline edge must be an object")
            if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
                raise ValueError("Pipeline edges must reference existing nodes")

        return json.dumps(definition, sort_keys=True)
