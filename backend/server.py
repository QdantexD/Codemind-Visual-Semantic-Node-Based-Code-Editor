from fastapi import FastAPI, WebSocket
import json
from typing import List, Dict, Any

app = FastAPI()


clients: List[WebSocket] = []
STATE: Dict[str, Any] = {
    "graph": {"nodes": [], "links": []}
}


async def broadcast(message: str, exclude: WebSocket | None = None):
    for ws in list(clients):
        if exclude is not None and ws is exclude:
            continue
        try:
            await ws.send_text(message)
        except Exception:
            try:
                clients.remove(ws)
            except ValueError:
                pass


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    print("Client connected")
    try:
        while True:
            data = await websocket.receive_text()
            # Try to parse JSON event
            try:
                evt = json.loads(data)
            except Exception:
                # Plain text echo fallback
                print(f"Received (text): {data}")
                await websocket.send_text(f"Server echo: {data}")
                continue

            evt_type = evt.get("type")
            payload = evt.get("payload", {})
            print(f"Event: {evt_type} -> {payload}")

            if evt_type == "node_created":
                # Update server-side state (basic append)
                STATE.setdefault("graph", {}).setdefault("nodes", []).append(payload)
                # Example processing: reply with a node_update value
                reply = {"type": "node_update", "payload": {"id": payload.get("id"), "value": 42}}
                await websocket.send_text(json.dumps(reply))

            elif evt_type == "link_created":
                STATE.setdefault("graph", {}).setdefault("links", []).append(payload)
                # Broadcast link creation to other clients
                await broadcast(json.dumps(evt), exclude=websocket)

            elif evt_type == "node_moved":
                # Update node position in server-side state if present
                node_id = payload.get("id")
                pos = payload.get("pos")
                for n in STATE.setdefault("graph", {}).setdefault("nodes", []):
                    if n.get("id") == node_id:
                        n["pos"] = pos
                        break
                # Optional: acknowledge
                ack = {"type": "node_move_ack", "payload": {"id": node_id, "pos": pos}}
                await websocket.send_text(json.dumps(ack))

            elif evt_type == "graph_snapshot":
                STATE["graph"] = payload
                # Broadcast snapshot to others
                await broadcast(json.dumps(evt), exclude=websocket)
                await websocket.send_text(json.dumps({"type": "snapshot_ack"}))

            else:
                # Unknown event, echo back
                await websocket.send_text(json.dumps({"type": "info", "payload": {"msg": "unknown event", "data": evt}}))
    except Exception as e:
        print("Client disconnected:", e)
    finally:
        try:
            clients.remove(websocket)
        except ValueError:
            pass