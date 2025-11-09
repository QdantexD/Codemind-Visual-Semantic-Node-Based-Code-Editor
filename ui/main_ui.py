import threading
import asyncio
import json
import websockets
from dearpygui import dearpygui as dpg

from .windows.toolbar import build_toolbar
from .windows.main_window import build_main_window
from .windows.properties_panel import build_properties_panel
from .core.graph import Graph
from .core.nodes import Node, NodeType, NodeRegistry
from .core.links import Link

WS_URL = "ws://127.0.0.1:8000/ws"

# Runtime state
GRAPH = Graph()
REGISTRY = NodeRegistry()
_NODE_COUNTER = 0
_EDITOR_ID = None


def _set_text(item, value):
    dpg.set_value(item, value)


def start_ui():
    dpg.create_context()
    dpg.create_viewport(title="Omega-Visual", width=1200, height=800)
    dpg.setup_dearpygui()

    # Build windows
    toolbar_id = build_toolbar()
    main_win_id, editor_id = build_main_window()
    global _EDITOR_ID
    _EDITOR_ID = editor_id
    props_id = build_properties_panel()

    # Status labels from toolbar: use alias directly
    ws_label = "ws_status"
    log_label = dpg.add_text("Waiting for messages...", parent=toolbar_id)

    # Register default node types
    _register_default_node_types()

    # Wire toolbar actions
    dpg.set_item_callback("btn_new", lambda: _create_node("Compute"))
    dpg.set_item_callback("btn_save", lambda: _send_graph_snapshot())

    # Configure node editor callbacks (link create/destroy)
    dpg.configure_item(editor_id, callback=_on_link_created, delink_callback=_on_link_deleted)

    # Start WebSocket client thread
    threading.Thread(target=_start_ws_client, args=(ws_label, log_label), daemon=True).start()

    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


# --- WebSocket client ---
def _start_ws_client(ws_label, log_label):
    async def run():
        try:
            async with websockets.connect(WS_URL) as ws:
                _set_text(ws_label, "WS: connected")
                print("Connected to WebSocket Server")
                await ws.send("Hello from GUI!")
                while True:
                    try:
                        msg = await ws.recv()
                        print("Server:", msg)
                        _set_text(log_label, f"Server: {msg}")
                    except Exception as e:
                        _set_text(ws_label, f"WS error: {e}")
                        break
        except Exception as e:
            _set_text(ws_label, f"WS error: {e}")

    asyncio.run(run())


def _send_graph_snapshot():
    payload = {
        "action": "graph.snapshot",
        "data": GRAPH.snapshot(),
    }

    async def run():
        try:
            async with websockets.connect(WS_URL) as ws:
                await ws.send(json.dumps(payload))
        except Exception as e:
            print("WS send error:", e)

    threading.Thread(target=lambda: asyncio.run(run()), daemon=True).start()
# --- Node registry and creation ---
def _register_default_node_types():
    REGISTRY.register(NodeType("Compute", inputs=["in"], outputs=["out"], color="#66CCFF"))
    REGISTRY.register(NodeType("Data", inputs=[], outputs=["out"], color="#9CCC65"))
    REGISTRY.register(NodeType("Op", inputs=["a", "b"], outputs=["result"], color="#FFCA28"))


def _create_node(type_name: str):
    global _NODE_COUNTER
    nt = REGISTRY.get(type_name)
    if not nt or _EDITOR_ID is None:
        return

    _NODE_COUNTER += 1
    node_id = f"node{_NODE_COUNTER}"

    with dpg.node(label=nt.name, parent=_EDITOR_ID, tag=node_id):
        # inputs
        for inp in nt.inputs:
            with dpg.node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Input, tag=f"{node_id}:in:{inp}"):
                dpg.add_text(inp)
        # outputs
        for outp in nt.outputs:
            with dpg.node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output, tag=f"{node_id}:out:{outp}"):
                dpg.add_text(outp)

    GRAPH.add_node(Node(id=node_id, type=nt.name, title=nt.name, inputs=nt.inputs, outputs=nt.outputs, meta={"color": nt.color}))
    _send_graph_snapshot()


# --- Link management ---
def _on_link_created(sender, app_data):
    try:
        start_attr, end_attr = app_data
        # Draw the link visually
        dpg.add_node_link(start_attr, end_attr, parent=sender)
        # Update graph model
        s_node, _, s_port = start_attr.split(":", 2)
        e_node, _, e_port = end_attr.split(":", 2)
        GRAPH.add_link(Link(start_node=s_node, start_port=s_port, end_node=e_node, end_port=e_port))
        _send_graph_snapshot()
    except Exception as e:
        print("Link create error:", e)


def _on_link_deleted(sender, app_data):
    try:
        # app_data is the list of link IDs to delete
        for link_id in app_data:
            conf = dpg.get_item_configuration(link_id)
            start_attr = conf.get("start_attr")
            end_attr = conf.get("end_attr")
            if start_attr and end_attr:
                s_node, _, s_port = str(start_attr).split(":", 2)
                e_node, _, e_port = str(end_attr).split(":", 2)
                # remove matching link from GRAPH
                GRAPH.links = [
                    l for l in GRAPH.links
                    if not (l.start_node == s_node and l.start_port == s_port and l.end_node == e_node and l.end_port == e_port)
                ]
        _send_graph_snapshot()
    except Exception as e:
        print("Link delete error:", e)