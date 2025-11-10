"""ui.windows.terminal_panel

Terminal básica integrada estilo VS Code.
"""
from dearpygui import dearpygui as dpg


def build_terminal_panel() -> int:
    with dpg.window(label="Terminal", width=900, height=220, pos=(0, 540)) as win_id:
        dpg.add_text("Terminal integrada (simulada)")
        dpg.add_input_text(tag="terminal_input", multiline=True, height=160, width=-1)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Limpiar", callback=lambda: dpg.set_value("terminal_input", ""))
            dpg.add_button(label="Ejecutar", callback=lambda: dpg.set_value("terminal_input", dpg.get_value("terminal_input")+"\n> Ejecutado"))
    return win_id