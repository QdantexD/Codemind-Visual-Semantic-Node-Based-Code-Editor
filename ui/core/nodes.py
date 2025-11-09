"""ui.core.nodes

Basic node type and model definitions for Omega-Visual.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Node:
    id: str
    type: str
    title: Optional[str] = None
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)


class NodeType:
    def __init__(self, name: str, inputs: List[str], outputs: List[str], color: str = "#A0A0A0"):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.color = color


class NodeRegistry:
    def __init__(self):
        self._types: Dict[str, NodeType] = {}

    def register(self, node_type: NodeType):
        self._types[node_type.name] = node_type

    def get(self, name: str) -> Optional[NodeType]:
        return self._types.get(name)

    def list(self) -> List[str]:
        return list(self._types.keys())