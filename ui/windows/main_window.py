"""ui.windows.main_window

Main window layout with a node editor canvas.
"""
from dearpygui import dearpygui as dpg


def build_main_window() -> tuple[int, int]:
    """Construye la ventana principal con barra de pestañas arriba y editor abajo."""
    with dpg.window(label="Omega-Visual", width=900, height=700, pos=(0, 60)) as win_id:
        with dpg.group(horizontal=False):
            with dpg.tab_bar(tag="editor_tabbar"):
                # Pestaña inicial del editor
                with dpg.tab(label="Editor"):
                    dpg.add_text("Pestañas del editor estilo VS Code")
            # Editor de nodos
            editor_id = dpg.add_node_editor(tag="node_editor")
    return win_id, editor_id