"""ui.windows.explorer_panel

Explorador de archivos estilo VS Code.
"""
from dearpygui import dearpygui as dpg


def build_explorer_panel() -> int:
    with dpg.window(label="Explorer", width=280, pos=(0, 60)) as win_id:
        dpg.add_text("ProyectoPrincipal")
        with dpg.tree_node(label="src", default_open=True):
            dpg.add_text("main.py")
            dpg.add_text("utils.py")
        with dpg.tree_node(label="web", default_open=True):
            dpg.add_text("index.html")
            dpg.add_text("styles.css")
        with dpg.tree_node(label="data"):
            dpg.add_text("dataset.csv")
    return win_id