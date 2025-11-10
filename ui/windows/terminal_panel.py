"""ui.windows.terminal_panel

Terminal básica integrada estilo VS Code.
"""
from dearpygui import dearpygui as dpg


def build_terminal_panel() -> int:
    with dpg.window(label="Output Log", width=900, height=220, pos=(0, 540)) as win_id:
        dpg.add_text("> Compilando...")
        dpg.add_input_text(tag="terminal_input", multiline=True, height=160, width=-1)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Limpiar", callback=lambda: dpg.set_value("terminal_input", ""))
            dpg.add_button(label="Ejecutar", callback=lambda: dpg.set_value("terminal_input", dpg.get_value("terminal_input")+"\n> Ejecutado"))
    # Theme for near-black background
    try:
        with dpg.theme() as _log_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (27, 27, 27, 255))  # #1B1B1B
                dpg.add_theme_color(dpg.mvThemeCol_Text, (230, 230, 230, 255))
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 2.0)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8.0, 8.0)
        dpg.bind_item_theme(win_id, _log_theme)
    except Exception:
        pass
    return win_id