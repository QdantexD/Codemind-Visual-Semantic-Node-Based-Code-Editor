import threading
import asyncio
import json
import websockets
from dearpygui import dearpygui as dpg

from .windows.toolbar import build_toolbar
from .windows.main_window import build_main_window
from .windows.properties_panel import build_properties_panel
from .windows.explorer_panel import build_explorer_panel
from .windows.terminal_panel import build_terminal_panel
from .core.graph import Graph
from .core.nodes import Node, NodeType, NodeRegistry
from .core.links import Link

WS_URL = "ws://127.0.0.1:8000/ws"

# Runtime state
GRAPH = Graph()
REGISTRY = NodeRegistry()
_NODE_COUNTER = 0
_EDITOR_ID = None
_WS_STATUS_ALIAS = "ws_status"
_LAST_SELECTED_NODE_ID = None
_CTRL_DOWN = False
_TOOLBAR_ID = None
_MAIN_WIN_ID = None
_PROPS_WIN_ID = None
_STATUS_WIN_ID = None
_FS_MODE = False
_FS_PREV = {}
_EXPLORER_ID = None
_TERMINAL_ID = None
_ACTIVITYBAR_ID = None
_MINIMAP_WIN_ID = None
_MINIMAP_DRAW_ID = None
_SETTINGS = {"autosave": False, "wordWrap": "off"}


def _set_text(item, value):
    dpg.set_value(item, value)


def start_ui():
    dpg.create_context()
    dpg.create_viewport(title="Omega-Visual", width=1200, height=800)
    dpg.setup_dearpygui()

    # Apply global visual theme
    _build_global_theme()

    # Build windows
    toolbar_id = build_toolbar()
    main_win_id, editor_id = build_main_window()
    global _EDITOR_ID
    _EDITOR_ID = editor_id
    # Side panels
    explorer_id = build_explorer_panel()
    props_id = build_properties_panel()
    terminal_id = build_terminal_panel()
    # Store window ids for fullscreen toggle
    global _TOOLBAR_ID, _MAIN_WIN_ID, _PROPS_WIN_ID, _EXPLORER_ID, _TERMINAL_ID
    _TOOLBAR_ID = toolbar_id
    _MAIN_WIN_ID = main_win_id
    _PROPS_WIN_ID = props_id
    _EXPLORER_ID = explorer_id
    _TERMINAL_ID = terminal_id

    # Status labels from toolbar: use alias directly
    ws_label = _WS_STATUS_ALIAS
    # Bottom status bar for logs
    with dpg.window(label="Status", no_move=True, no_resize=True, height=28, pos=(0, 760), width=1200) as status_id:
        log_label = dpg.add_text("Ready", wrap=0)
    global _STATUS_WIN_ID
    _STATUS_WIN_ID = status_id

    # Activity bar (estrecha, opcional)
    with dpg.window(label="Activity", width=40, height=700, pos=(0, 60)) as act_id:
        btn_e = dpg.add_button(label="E")
        with dpg.tooltip(parent=btn_e):
            dpg.add_text("Explorer")
        btn_s = dpg.add_button(label="S")
        with dpg.tooltip(parent=btn_s):
            dpg.add_text("Search")
        btn_g = dpg.add_button(label="G")
        with dpg.tooltip(parent=btn_g):
            dpg.add_text("Git")
    global _ACTIVITYBAR_ID
    _ACTIVITYBAR_ID = act_id

    # Register default node types
    _register_default_node_types()

    # Wire toolbar actions
    dpg.set_item_callback("btn_new", _on_new_pressed)
    dpg.set_item_callback("btn_duplicate", _on_duplicate_pressed)
    dpg.set_item_callback("btn_save", _on_save_pressed)
    dpg.set_item_callback("btn_load", _on_load_pressed)

    # Configure node editor callbacks (link create/destroy)
    dpg.configure_item(editor_id, callback=_on_link_created, delink_callback=_on_link_deleted)

    # Keyboard handlers (Ctrl+M: fullscreen editor)
    with dpg.handler_registry():
        dpg.add_key_down_handler(dpg.mvKey_Control, callback=_on_ctrl_down)
        dpg.add_key_release_handler(dpg.mvKey_Control, callback=_on_ctrl_up)
        dpg.add_key_press_handler(dpg.mvKey_M, callback=_on_m_pressed)

    # Start WebSocket client thread
    threading.Thread(target=_start_ws_client, args=(ws_label, log_label), daemon=True).start()

    # Minimap desactivado: no crear overlay ni reconstruirlo

    # Aplicar configuración estilo VS Code solicitada
    _apply_vscode_like_configuration()

    # Registrar callback de resize independiente del minimapa
    try:
        dpg.set_viewport_resize_callback(_on_viewport_resize)
    except Exception:
        pass

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
                        # Try JSON
                        try:
                            evt = json.loads(msg)
                            _handle_server_event(evt)
                            _set_text(log_label, f"Server evt: {evt.get('type')}")
                        except Exception:
                            print("Server:", msg)
                            _set_text(log_label, f"Server: {msg}")
                    except Exception as e:
                        _set_text(ws_label, f"WS error: {e}")
                        break
        except Exception as e:
            _set_text(ws_label, f"WS error: {e}")

    asyncio.run(run())


def _send_graph_snapshot():
    # include positions from UI at save time
    snap = GRAPH.snapshot()
    for n in snap["nodes"]:
        nid = n["id"]
        try:
            pos = dpg.get_item_pos(nid)
            n.setdefault("meta", {})["pos"] = list(pos)
        except Exception:
            pass
    payload = {"type": "graph_snapshot", "payload": snap}

    async def run():
        try:
            async with websockets.connect(WS_URL) as ws:
                await ws.send(json.dumps(payload))
        except Exception as e:
            print("WS send error:", e)

    threading.Thread(target=lambda: asyncio.run(run()), daemon=True).start()


def _build_global_theme():
    try:
        with dpg.theme() as theme_id:
            with dpg.theme_component(dpg.mvAll):
                # Colors
                # Dark+ (default dark) palette
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (30, 30, 30, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (45, 45, 45, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (60, 60, 60, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (70, 70, 70, 255))
                # Accent #007acc
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 122, 204, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 132, 214, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 102, 184, 255))
                # Spacing & rounding
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8.0)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6.0)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8.0, 6.0)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 8.0, 8.0)
        dpg.bind_theme(theme_id)
    except Exception as e:
        print("Theme build error:", e)


def _send_event(event_type: str, payload: dict):
    data = {"type": event_type, "payload": payload}

    async def run():
        try:
            async with websockets.connect(WS_URL) as ws:
                await ws.send(json.dumps(data))
        except Exception as e:
            print("WS event send error:", e)

    threading.Thread(target=lambda: asyncio.run(run()), daemon=True).start()


# --- Fullscreen toggle helpers ---
def _on_ctrl_down(sender, app_data):
    global _CTRL_DOWN
    _CTRL_DOWN = True


def _on_ctrl_up(sender, app_data):
    global _CTRL_DOWN
    _CTRL_DOWN = False


def _on_m_pressed(sender, app_data):
    if _CTRL_DOWN:
        _toggle_editor_fullscreen()


def _viewport_size() -> tuple[int, int]:
    try:
        w = dpg.get_viewport_client_width()
        h = dpg.get_viewport_client_height()
        if w and h:
            return int(w), int(h)
    except Exception:
        pass
    return 1200, 800


def _on_viewport_resize(sender, app_data):
    # Recalcula el layout al cambiar tamaño de la ventana (minimizar/maximizar)
    try:
        _layout_apply_default()
    except Exception as e:
        print("Viewport resize error:", e)


def _toggle_editor_fullscreen():
    global _FS_MODE, _FS_PREV
    try:
        if not _FS_MODE:
            # Save current layout
            def _save_win(win_id, key):
                pos = dpg.get_item_pos(win_id)
                w = dpg.get_item_width(win_id)
                h = dpg.get_item_height(win_id)
                _FS_PREV[key] = {"pos": pos, "size": (w, h), "show": dpg.is_item_shown(win_id)}

            _save_win(_TOOLBAR_ID, "toolbar")
            _save_win(_MAIN_WIN_ID, "main")
            _save_win(_PROPS_WIN_ID, "props")
            _save_win(_STATUS_WIN_ID, "status")

            # Hide ancillary windows
            dpg.configure_item(_TOOLBAR_ID, show=False)
            dpg.configure_item(_PROPS_WIN_ID, show=False)
            dpg.configure_item(_STATUS_WIN_ID, show=False)

            # Maximize main window and editor
            vw, vh = _viewport_size()
            dpg.configure_item(_MAIN_WIN_ID, pos=(0, 0), width=vw, height=vh)
            try:
                dpg.configure_item(_EDITOR_ID, width=vw - 20, height=vh - 20)
            except Exception:
                pass
            _FS_MODE = True
        else:
            # Restore layout
            def _restore(win_id, key):
                prev = _FS_PREV.get(key, {})
                if not prev:
                    return
                pos = prev.get("pos")
                size = prev.get("size")
                show = prev.get("show", True)
                if pos:
                    dpg.configure_item(win_id, pos=tuple(pos))
                if size:
                    w, h = size
                    dpg.configure_item(win_id, width=int(w), height=int(h))
                dpg.configure_item(win_id, show=show)

            _restore(_TOOLBAR_ID, "toolbar")
            _restore(_MAIN_WIN_ID, "main")
            _restore(_PROPS_WIN_ID, "props")
            _restore(_STATUS_WIN_ID, "status")
            _FS_MODE = False
    except Exception as e:
        print("Fullscreen toggle error:", e)


def _handle_server_event(evt: dict):
    t = evt.get("type")
    payload = evt.get("payload", {})
    if t == "node_update":
        node_id = payload.get("id")
        value = payload.get("value")
        if node_id and value is not None:
            try:
                # Update node label to reflect value
                node = GRAPH.nodes.get(node_id)
                base_label = node.title if node else node_id
                dpg.configure_item(node_id, label=f"{base_label} ({value})")
            except Exception as e:
                print("Label update error:", e)
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
        # Click handler to select node
        with dpg.item_handler_registry() as hreg:
            dpg.add_item_clicked_handler(callback=_on_node_clicked, user_data=node_id)
        dpg.bind_item_handler_registry(node_id, hreg)

    GRAPH.add_node(Node(id=node_id, type=nt.name, title=nt.name, inputs=nt.inputs, outputs=nt.outputs, meta={"color": nt.color}))
    # Send event: node_created
    _send_event("node_created", {
        "id": node_id,
        "name": nt.name,
        "inputs": nt.inputs,
        "outputs": nt.outputs,
    })
    _send_graph_snapshot()
    # Auto-select new node
    _on_node_selected(node_id)


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
        # Send event: link_created
        _send_event("link_created", {
            "from": {"node": s_node, "port": s_port},
            "to": {"node": e_node, "port": e_port},
        })
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


def _on_node_drag(sender, app_data):
    try:
        node_id = app_data
        pos = dpg.get_item_pos(node_id)
        # Update graph node meta
        if node_id in GRAPH.nodes:
            GRAPH.nodes[node_id].meta["pos"] = pos
        # Send event: node_moved
        _send_event("node_moved", {"id": node_id, "pos": list(pos)})
    except Exception as e:
        print("Node drag error:", e)


# --- Selection and properties ---
def _on_node_clicked(sender, app_data, user_data):
    node_id = user_data
    _on_node_selected(node_id)


def _on_node_selected(node_id: str):
    global _LAST_SELECTED_NODE_ID
    _LAST_SELECTED_NODE_ID = node_id
    node = GRAPH.nodes.get(node_id)
    if node:
        dpg.set_value("prop_title", node.title or "")
        dpg.set_value("prop_type", node.type)
        dpg.set_value("prop_id", node.id)
        dpg.set_value("prop_inputs", f"Inputs: {', '.join(node.inputs)}")
        dpg.set_value("prop_outputs", f"Outputs: {', '.join(node.outputs)}")
        dpg.set_value("prop_hint", "")
    _rebuild_minimap()


# --- Toolbar actions ---
def _on_new_pressed():
    t = dpg.get_value("node_type") or "Compute"
    _create_node(str(t))


def _on_duplicate_pressed():
    if not _LAST_SELECTED_NODE_ID:
        return
    node = GRAPH.nodes.get(_LAST_SELECTED_NODE_ID)
    if not node:
        return
    _create_node(node.type)
    # offset new node position near last selected
    try:
        pos = dpg.get_item_pos(_LAST_SELECTED_NODE_ID)
        dpg.set_item_pos(f"node{_NODE_COUNTER}", (pos[0] + 40, pos[1] + 40))
    except Exception:
        pass
    _rebuild_minimap()


def _on_save_pressed():
    # write project.json to root
    snap = GRAPH.snapshot()
    for n in snap["nodes"]:
        nid = n["id"]
        try:
            pos = dpg.get_item_pos(nid)
            n.setdefault("meta", {})["pos"] = list(pos)
        except Exception:
            pass
    try:
        with open("project.json", "w", encoding="utf-8") as f:
            json.dump(snap, f, indent=2)
        _set_text(_WS_STATUS_ALIAS, "WS: saved project.json")
    except Exception as e:
        print("Save error:", e)


def _on_load_pressed():
    try:
        with open("project.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("Load error:", e)
        return

    # Clear current editor and graph
    try:
        dpg.delete_item(_EDITOR_ID, children_only=True)
    except Exception:
        pass
    GRAPH.nodes.clear()
    GRAPH.links.clear()

    # Reset counter
    global _NODE_COUNTER
    _NODE_COUNTER = 0

    # Rebuild nodes preserving IDs
    for n in data.get("nodes", []):
        tname = n.get("type", "Compute")
        _create_node(tname)
        nid_new = f"node{_NODE_COUNTER}"
        nid_target = n.get("id", nid_new)
        if nid_target != nid_new:
            try:
                dpg.configure_item(nid_new, tag=nid_target)
            except Exception:
                pass
        # set pos if available
        pos = n.get("meta", {}).get("pos")
        if pos:
            try:
                dpg.set_item_pos(nid_target, tuple(pos))
            except Exception:
                pass

    # Rebuild links
    for l in data.get("links", []):
        s = l.get("from", {})
        e = l.get("to", {})
        s_attr = f"{s.get('node')}:out:{s.get('port')}"
        e_attr = f"{e.get('node')}:in:{e.get('port')}"
        try:
            dpg.add_node_link(s_attr, e_attr, parent=_EDITOR_ID)
            GRAPH.add_link(Link(start_node=s.get('node'), start_port=s.get('port'), end_node=e.get('node'), end_port=e.get('port')))
        except Exception as ex:
            print("Link load error:", ex)
    _rebuild_minimap()

# --- Minimap overlay estilo VS Code ---
def _build_minimap_overlay():
    try:
        with dpg.window(label="", no_title_bar=True, no_move=True, no_resize=True, width=280, height=180, pos=(460, 340)) as win_id:
            dpg.add_text("", tag="minimap_title")
            with dpg.drawlist(width=280, height=160) as draw_id:
                pass
        global _MINIMAP_WIN_ID, _MINIMAP_DRAW_ID
        _MINIMAP_WIN_ID = win_id
        _MINIMAP_DRAW_ID = draw_id
        # Resize callback para re-centrar
        try:
            dpg.set_viewport_resize_callback(lambda s, a: (_layout_apply_default(), _center_minimap_in_main(), _rebuild_minimap()))
        except Exception:
            pass
    except Exception as e:
        print("Minimap build error:", e)


def _center_minimap_in_main():
    try:
        if not _MAIN_WIN_ID or not _MINIMAP_WIN_ID:
            return
        # Obtener rect del main
        pos = dpg.get_item_pos(_MAIN_WIN_ID)
        w = dpg.get_item_width(_MAIN_WIN_ID)
        h = dpg.get_item_height(_MAIN_WIN_ID)
        mw = dpg.get_item_width(_MINIMAP_WIN_ID)
        mh = dpg.get_item_height(_MINIMAP_WIN_ID)
        cx = pos[0] + (w - mw) // 2
        cy = pos[1] + (h - mh) // 2
        dpg.configure_item(_MINIMAP_WIN_ID, pos=(int(cx), int(cy)))
    except Exception as e:
        print("Minimap center error:", e)


def _rebuild_minimap():
    try:
        if not _MINIMAP_DRAW_ID:
            return
        dpg.delete_item(_MINIMAP_DRAW_ID, children_only=True)
        # Fondo semi-transparente
        dpg.draw_rectangle((4, 4), (276, 156), color=(0, 0, 0, 80), fill=(0, 0, 0, 60), parent=_MINIMAP_DRAW_ID, thickness=1)
        # Dibujar nodos como rectángulos escalados
        nodes = list(GRAPH.nodes.values())
        # Obtener bounds
        xs, ys = [], []
        for n in nodes:
            nid = n.id
            try:
                x, y = dpg.get_item_pos(nid)
                xs.append(x)
                ys.append(y)
            except Exception:
                pass
        if xs and ys:
            minx, maxx = min(xs), max(xs)
            miny, maxy = min(ys), max(ys)
            spanx = max(1, maxx - minx)
            spany = max(1, maxy - miny)
        else:
            minx = miny = 0
            spanx = spany = 1
        for n in nodes:
            nid = n.id
            try:
                x, y = dpg.get_item_pos(nid)
                # Normalizar a drawlist
                nx = 8 + int((x - minx) / spanx * 264)
                ny = 8 + int((y - miny) / spany * 144)
                dpg.draw_rectangle((nx, ny), (nx + 10, ny + 6), color=(0, 122, 204, 180), fill=(0, 122, 204, 80), parent=_MINIMAP_DRAW_ID)
            except Exception:
                pass
    except Exception as e:
        print("Minimap rebuild error:", e)


# --- API de configuración estilo VS Code ---
def _apply_vscode_like_configuration():
    try:
        # 1. Workspace
        _workspace_create("ProyectoPrincipal")
        _workspace_open("ProyectoPrincipal")
        # Layout por defecto
        _layout_apply_default()
        _layout_save("LayoutDefault")
        # 2. Control de paneles
        _panel_split("Editor", direction="vertical")
        _panel_split("Editor", direction="horizontal")
        _panel_move("Terminal", to="right")
        _panel_resize("Terminal", height="40%")
        _panel_focus("Explorador")
        _panel_toggle("Terminal")
        _panel_close("Propiedades")
        # 3. Archivos y pestañas
        _tab_open("main.py", in_="Editor")
        _tab_open("index.html", in_="Editor")
        _tab_switch("next")
        _tab_switch("previous")
        _tab_close("index.html")
        _tab_rename("main.py", "principal.py")
        _tab_arrange("vertical")
        _tab_arrange("horizontal")
        # 4. Apariencia y temas
        _theme_set("Dark+ (default dark)")
        _font_set("Fira Code", size=14)
        _statusbar_show()
        _activitybar_hide()
        # Desactivar minimapa por defecto
        _minimap_toggle("off")
        try:
            if _MINIMAP_WIN_ID:
                dpg.delete_item(_MINIMAP_WIN_ID)
        except Exception:
            pass
        # 5. Configuraciones
        _layout_reset("LayoutDefault")
        _workspace_save()
        _settings_set("autosave", True)
        _settings_set("wordWrap", "on")
        # 6. Control visual UI
        _ui_drag("Terminal", to="bottom")
        _ui_resize("Editor", width="60%")
        _ui_focus("CommandPalette")
        _ui_toggle("sidebar left")
        _ui_show_all_panels()
        # 7. Estilo global visual
        _style_apply("VSCodeLike", {
            "background": "#1e1e1e",
            "accentColor": "#007acc",
            "font": "Fira Code",
            "borderStyle": "subtle",
            "animation": "smooth"
        })
    except Exception as e:
        print("Apply VSCode config error:", e)


# --- Implementaciones de helpers de configuración ---
def _workspace_create(name: str):
    dpg.set_value(_WS_STATUS_ALIAS, f"WS: workspace '{name}' creado")


def _workspace_open(name: str):
    dpg.set_value(_WS_STATUS_ALIAS, f"WS: workspace '{name}' abierto")


def _layout_apply_default():
    vw, vh = _viewport_size()
    toolbar_h = 60
    status_h = 28
    activity_w = 40
    avail_w = max(0, vw - activity_w)
    avail_h = max(0, vh - toolbar_h - status_h)

    # Barra de herramientas y de estado
    try:
        dpg.configure_item(_TOOLBAR_ID, pos=(0, 0), width=vw, height=toolbar_h)
    except Exception:
        pass
    try:
        dpg.configure_item(_STATUS_WIN_ID, pos=(0, vh - status_h), width=vw, height=status_h)
    except Exception:
        pass

    # Explorer izquierda 25% del ancho disponible
    exp_w = int(avail_w * 0.25)
    exp_h = avail_h
    dpg.configure_item(_EXPLORER_ID, pos=(activity_w, toolbar_h), width=exp_w, height=exp_h)

    # Properties derecha 25% del ancho disponible
    props_w = int(avail_w * 0.25)
    dpg.configure_item(_PROPS_WIN_ID, pos=(activity_w + avail_w - props_w, toolbar_h), width=props_w, height=exp_h)

    # Activity bar estrecha
    dpg.configure_item(_ACTIVITYBAR_ID, pos=(0, toolbar_h), width=activity_w, height=exp_h)

    # Editor centro
    main_x = activity_w + exp_w
    main_w = avail_w - exp_w - props_w
    main_h = int(exp_h * 0.7)
    dpg.configure_item(_MAIN_WIN_ID, pos=(main_x, toolbar_h), width=main_w, height=main_h)
    try:
        dpg.configure_item(_EDITOR_ID, width=main_w - 20, height=main_h - 20)
    except Exception:
        pass

    # Terminal abajo 30%
    term_h = exp_h - main_h
    dpg.configure_item(_TERMINAL_ID, pos=(main_x, toolbar_h + main_h), width=main_w, height=term_h)

    # Minimapa desactivado: no centrar overlay


_SAVED_LAYOUTS = {}


def _layout_save(name: str):
    try:
        _SAVED_LAYOUTS[name] = {
            "explorer": {
                "pos": dpg.get_item_pos(_EXPLORER_ID),
                "size": (dpg.get_item_width(_EXPLORER_ID), dpg.get_item_height(_EXPLORER_ID))
            },
            "props": {
                "pos": dpg.get_item_pos(_PROPS_WIN_ID),
                "size": (dpg.get_item_width(_PROPS_WIN_ID), dpg.get_item_height(_PROPS_WIN_ID))
            },
            "main": {
                "pos": dpg.get_item_pos(_MAIN_WIN_ID),
                "size": (dpg.get_item_width(_MAIN_WIN_ID), dpg.get_item_height(_MAIN_WIN_ID))
            },
            "terminal": {
                "pos": dpg.get_item_pos(_TERMINAL_ID),
                "size": (dpg.get_item_width(_TERMINAL_ID), dpg.get_item_height(_TERMINAL_ID))
            }
        }
    except Exception as e:
        print("Layout save error:", e)


def _layout_reset(name: str):
    try:
        conf = _SAVED_LAYOUTS.get(name)
        if not conf:
            return
        for key, info in conf.items():
            wid = {
                "explorer": _EXPLORER_ID,
                "props": _PROPS_WIN_ID,
                "main": _MAIN_WIN_ID,
                "terminal": _TERMINAL_ID,
            }[key]
            dpg.configure_item(wid, pos=tuple(info["pos"]))
            w, h = info["size"]
            dpg.configure_item(wid, width=int(w), height=int(h))
        # Minimapa desactivado: no centrar overlay
    except Exception as e:
        print("Layout reset error:", e)


def _workspace_save():
    dpg.set_value(_WS_STATUS_ALIAS, "WS: workspace guardado")


def _panel_split(name: str, direction: str):
    # Simulación: no-op con log
    print(f"panel.split({name}, {direction})")


def _panel_move(name: str, to: str):
    try:
        if name == "Terminal" and to == "right":
            pos = dpg.get_item_pos(_TERMINAL_ID)
            w = dpg.get_item_width(_TERMINAL_ID)
            h = dpg.get_item_height(_TERMINAL_ID)
            vw, _ = _viewport_size()
            dpg.configure_item(_TERMINAL_ID, pos=(vw - w - 40, pos[1]), width=w, height=h)
    except Exception as e:
        print("Panel move error:", e)


def _panel_resize(name: str, height: str | int | None = None, width: str | int | None = None):
    try:
        if name == "Terminal" and isinstance(height, str) and height.endswith("%"):
            vh = _viewport_size()[1]
            perc = float(height[:-1]) / 100.0
            h = int((vh - 88) * perc)
            dpg.configure_item(_TERMINAL_ID, height=h)
    except Exception as e:
        print("Panel resize error:", e)


def _panel_focus(name: str):
    try:
        wid = {
            "Explorador": _EXPLORER_ID,
            "Editor": _MAIN_WIN_ID,
            "Terminal": _TERMINAL_ID,
            "Propiedades": _PROPS_WIN_ID,
        }.get(name)
        if wid:
            dpg.focus_item(wid)
    except Exception as e:
        print("Panel focus error:", e)


def _panel_toggle(name: str):
    try:
        wid = {
            "Explorador": _EXPLORER_ID,
            "Editor": _MAIN_WIN_ID,
            "Terminal": _TERMINAL_ID,
            "Propiedades": _PROPS_WIN_ID,
        }.get(name)
        if wid:
            dpg.configure_item(wid, show=not dpg.is_item_shown(wid))
    except Exception as e:
        print("Panel toggle error:", e)


def _panel_close(name: str):
    try:
        wid = {
            "Explorador": _EXPLORER_ID,
            "Editor": _MAIN_WIN_ID,
            "Terminal": _TERMINAL_ID,
            "Propiedades": _PROPS_WIN_ID,
        }.get(name)
        if wid:
            dpg.configure_item(wid, show=False)
    except Exception as e:
        print("Panel close error:", e)


def _tab_open(name: str, in_: str = "Editor"):
    try:
        with dpg.tab(label=name, parent="editor_tabbar"):
            dpg.add_text(f"Abierto: {name}")
    except Exception as e:
        print("Tab open error:", e)


def _tab_close(name: str):
    try:
        # Buscar tab por label
        children_map = dpg.get_item_children("editor_tabbar")
        children = children_map.get(1, []) if isinstance(children_map, dict) else []
        for child in children:
            if dpg.get_item_label(child) == name:
                dpg.delete_item(child)
                break
    except Exception as e:
        print("Tab close error:", e)


def _tab_switch(direction: str):
    try:
        # Simulación: focus a first/last tab
        children_map = dpg.get_item_children("editor_tabbar")
        children = children_map.get(1, []) if isinstance(children_map, dict) else []
        if not children:
            return
        target = children[0] if direction == "previous" else children[-1]
        dpg.focus_item(target)
    except Exception as e:
        print("Tab switch error:", e)


def _tab_rename(old: str, new: str):
    try:
        children_map = dpg.get_item_children("editor_tabbar")
        children = children_map.get(1, []) if isinstance(children_map, dict) else []
        for child in children:
            if dpg.get_item_label(child) == old:
                dpg.configure_item(child, label=new)
                break
    except Exception as e:
        print("Tab rename error:", e)


def _tab_arrange(mode: str):
    print(f"tab.arrange({mode})")


def _theme_set(name: str):
    # Ya aplicado por _build_global_theme
    dpg.set_value(_WS_STATUS_ALIAS, f"Theme: {name}")


def _font_set(name: str, size: int = 14):
    try:
        # Intento opcional de cargar fuente si existe en carpeta fonts/
        path = f"fonts/{name.replace(' ', '')}.ttf"
        with dpg.font_registry():
            font = dpg.add_font(path, size)
        dpg.bind_font(font)
    except Exception:
        # Ignora si no existe
        pass


def _statusbar_show():
    dpg.configure_item(_STATUS_WIN_ID, show=True)


def _activitybar_hide():
    dpg.configure_item(_ACTIVITYBAR_ID, show=False)


def _minimap_toggle(state: str):
    show = state.lower() == "on"
    if _MINIMAP_WIN_ID:
        dpg.configure_item(_MINIMAP_WIN_ID, show=show)


def _settings_set(key: str, value):
    _SETTINGS[key] = value


def _ui_drag(name: str, to: str):
    # Reubicar panel por nombre
    _panel_move(name, to)


def _ui_resize(name: str, width: str | int | None = None, height: str | int | None = None):
    # Redimensionar panel por nombre
    _panel_resize(name, height=height, width=width)


def _ui_focus(name: str):
    print(f"ui.focus({name})")


def _ui_toggle(name: str):
    print(f"ui.toggle({name})")


def _ui_show_all_panels():
    for wid in (_EXPLORER_ID, _MAIN_WIN_ID, _TERMINAL_ID, _PROPS_WIN_ID, _ACTIVITYBAR_ID):
        try:
            dpg.configure_item(wid, show=True)
        except Exception:
            pass


def _style_apply(name: str, style: dict):
    # Aplica cambios básicos de estilo VSCodeLike
    try:
        bg = style.get("background")
        accent = style.get("accentColor")
        with dpg.theme() as theme_id:
            with dpg.theme_component(dpg.mvAll):
                if isinstance(bg, str) and bg.startswith('#'):
                    r = int(bg[1:3], 16)
                    g = int(bg[3:5], 16)
                    b = int(bg[5:7], 16)
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (r, g, b, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220, 255))
                base_btn = (0, 122, 204, 255)
                if isinstance(accent, str) and accent.startswith('#'):
                    r = int(accent[1:3], 16)
                    g = int(accent[3:5], 16)
                    b = int(accent[5:7], 16)
                    base_btn = (r, g, b, 255)
                dpg.add_theme_color(dpg.mvThemeCol_Button, base_btn)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, base_btn)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, base_btn)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8.0)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6.0)
        dpg.bind_theme(theme_id)
    except Exception as e:
        print("Style apply error:", e)
