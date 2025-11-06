import uuid
from typing import Dict, List, Any

class NodeModel:
    def __init__(self,
                 id: str = None,
                 type: str = "generic",
                 title: str = "Node",
                 x: float = 0.0,
                 y: float = 0.0,
                 content: str = "",
                 inputs: List[Dict[str, Any]] = None,
                 outputs: List[Dict[str, Any]] = None,
                 meta: Dict[str, Any] = None):
        self.id = id or str(uuid.uuid4())
        self.type = type
        self.title = title
        self.x = float(x)
        self.y = float(y)
        self.content = content or ""
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.meta = meta or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'x': self.x,
            'y': self.y,
            'content': self.content,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'meta': self.meta,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeModel':
        return cls(
            id=data.get('id'),
            type=data.get('type', 'generic'),
            title=data.get('title', 'Node'),
            x=data.get('x', 0.0),
            y=data.get('y', 0.0),
            content=data.get('content', ''),
            inputs=data.get('inputs', []),
            outputs=data.get('outputs', []),
            meta=data.get('meta', {}),
        )

def project_to_dict(nodes: List[NodeModel], meta: Dict[str, Any] = None) -> Dict[str, Any]:
    return {
        'version': 1,
        'meta': meta or {},
        'nodes': [n.to_dict() for n in nodes]
    }

def project_from_dict(data: Dict[str, Any]) -> List[NodeModel]:
    nodes = data.get('nodes', [])
    return [NodeModel.from_dict(n) for n in nodes]
