import threading
import asyncio
import websockets
from dearpygui import dearpygui as dpg

WS_URL = "ws://127.0.0.1:8000/ws"


def _set_text(item, value):
    dpg.set_value(item, value)


def start_ui():
    dpg.create_context()
    dpg.create_viewport(title="Realtime App", width=400, height=300)
    dpg.setup_dearpygui()

    with dpg.window(label="Realtime App", width=380, height=280):
        ws_label = dpg.add_text("Connecting...")
        log_label = dpg.add_text("Waiting for messages...")

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