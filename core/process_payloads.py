"""
Process JSON payload builders for backend integration.

This module provides standard JSON structures to communicate
process-related actions and graph/node state with a backend.

All builder functions return plain Python dicts ready for
`json.dumps(...)` or direct transport.

Version: 1.5.0 Alpha
"""

from typing import Any, Dict, List, Optional
import time


# --- Constants (types and actions) -------------------------------------------------

PROCESS_ACTION_START = "process.start"
PROCESS_ACTION_STOP = "process.stop"
PROCESS_ACTION_STATUS = "process.status"
PROCESS_ACTION_RESULT = "process.result"

TERMINAL_ACTION_RUN = "terminal.run_command"
TERMINAL_ACTION_CHANGE_PROFILE = "terminal.change_profile"
TERMINAL_ACTION_CLOSE = "terminal.close"

GRAPH_ACTION_SNAPSHOT = "graph.snapshot"
GRAPH_ACTION_UPDATE = "graph.update"

NODE_ACTION_SAVE_CONTENT = "node.save_content"


# --- Core helpers -----------------------------------------------------------------

def _ts() -> int:
    """Return a UNIX timestamp in milliseconds."""
    return int(time.time() * 1000)


def envelope(action: str, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Standard transport envelope for requests to the backend.

    - action: the action type (e.g., PROCESS_ACTION_START)
    - data: payload-specific content
    - request_id: optional client-provided id to correlate responses
    """
    return {
        "action": action,
        "data": data,
        "request_id": request_id,
        "timestamp": _ts(),
        "version": "1.5.0-alpha",
    }


# --- Graph and Node schemas --------------------------------------------------------

def make_port(port_id: str, dtype: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": port_id,
        "dtype": dtype,
    }


def make_node(
    node_id: str,
    node_type: str,
    title: Optional[str] = None,
    inputs: Optional[List[Dict[str, Any]]] = None,
    outputs: Optional[List[Dict[str, Any]]] = None,
    content: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "id": node_id,
        "type": node_type,
        "title": title,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "content": content,
        "meta": meta or {},
    }


def make_connection(start_node: str, start_port: str, end_node: str, end_port: str) -> Dict[str, Any]:
    return {
        "from": {"node": start_node, "port": start_port},
        "to": {"node": end_node, "port": end_port},
    }


def make_graph(graph_id: str, nodes: List[Dict[str, Any]], connections: List[Dict[str, Any]], meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "graph_id": graph_id,
        "nodes": nodes,
        "connections": connections,
        "meta": meta or {},
    }


# --- Process requests --------------------------------------------------------------

def make_process_start(
    graph_id: str,
    entry_node_id: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    return envelope(
        PROCESS_ACTION_START,
        {
            "graph_id": graph_id,
            "entry_node_id": entry_node_id,
            "params": params or {},
            "env": env or {},
            "cwd": cwd,
        },
    )


def make_process_stop(process_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    return envelope(
        PROCESS_ACTION_STOP,
        {
            "process_id": process_id,
            "reason": reason,
        },
    )


def make_process_status(process_id: str) -> Dict[str, Any]:
    return envelope(
        PROCESS_ACTION_STATUS,
        {
            "process_id": process_id,
        },
    )


# --- Terminal requests -------------------------------------------------------------

def make_terminal_run_command(
    node_id: str,
    command: str,
    profile: Optional[str] = None,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    return envelope(
        TERMINAL_ACTION_RUN,
        {
            "node_id": node_id,
            "command": command,
            "profile": profile,
            "cwd": cwd,
        },
    )


def make_terminal_change_profile(node_id: str, profile: str) -> Dict[str, Any]:
    return envelope(
        TERMINAL_ACTION_CHANGE_PROFILE,
        {
            "node_id": node_id,
            "profile": profile,
        },
    )


def make_terminal_close(node_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    return envelope(
        TERMINAL_ACTION_CLOSE,
        {
            "node_id": node_id,
            "reason": reason,
        },
    )


# --- Graph transport ---------------------------------------------------------------

def make_graph_snapshot(graph: Dict[str, Any]) -> Dict[str, Any]:
    return envelope(GRAPH_ACTION_SNAPSHOT, {"graph": graph})


def make_graph_update(
    graph_id: str,
    nodes: Optional[List[Dict[str, Any]]] = None,
    connections: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return envelope(
        GRAPH_ACTION_UPDATE,
        {
            "graph_id": graph_id,
            "nodes": nodes or [],
            "connections": connections or [],
            "meta": meta or {},
        },
    )


# --- Node content -----------------------------------------------------------------

def make_node_save_content(node_id: str, content: str, content_type: Optional[str] = None) -> Dict[str, Any]:
    return envelope(
        NODE_ACTION_SAVE_CONTENT,
        {
            "node_id": node_id,
            "content": content,
            "content_type": content_type,
        },
    )


# --- Validation (optional lightweight) --------------------------------------------

def validate_envelope(payload: Dict[str, Any]) -> bool:
    """Basic validation to ensure envelope fields exist."""
    return all(k in payload for k in ("action", "data", "timestamp", "version"))


def validate_graph(graph: Dict[str, Any]) -> bool:
    """Basic validation for graph structure."""
    return (
        isinstance(graph.get("graph_id"), str)
        and isinstance(graph.get("nodes"), list)
        and isinstance(graph.get("connections"), list)
    )


def validate_node(node: Dict[str, Any]) -> bool:
    return (
        isinstance(node.get("id"), str)
        and isinstance(node.get("type"), str)
        and isinstance(node.get("inputs"), list)
        and isinstance(node.get("outputs"), list)
    )


def validate_connection(conn: Dict[str, Any]) -> bool:
    f = conn.get("from", {})
    t = conn.get("to", {})
    return (
        isinstance(f.get("node"), str)
        and isinstance(f.get("port"), str)
        and isinstance(t.get("node"), str)
        and isinstance(t.get("port"), str)
    )