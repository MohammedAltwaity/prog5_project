# gateway/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import aiohttp
import json
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    with open(os.path.join(STATIC_DIR, "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

USER_URL = "http://localhost:8001"
ROOM_URL = "http://localhost:8002"
GAME_URL = "http://localhost:8003"

connected_players = {}

async def send_to_room(room_id: str, message: dict):
    payload = json.dumps(message)
    for ws in list(connected_players.values()):
        try:
            await ws.send_text(payload)
        except:
            pass

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    username = None
    room_id = None

    async with aiohttp.ClientSession() as session:
        try:
            while True:
                data = await ws.receive_text()
                msg = json.loads(data)

                if msg["type"] == "auth":
                    username = msg["username"]
                    password = msg["password"]
                    try:
                        await session.post(f"{USER_URL}/register", json={"username": username, "password": password})
                    except: pass
                    await session.post(f"{USER_URL}/login", json={"username": username, "password": password})
                    connected_players[username] = ws
                    await ws.send_json({"type": "logged_in", "username": username})

                elif msg["type"] == "create_room":
                    resp = await session.post(f"{ROOM_URL}/create", json={"username": username})
                    room = await resp.json()
                    room_id = room["room_id"]
                    await ws.send_json({"type": "room_created", "room_id": room_id})

                elif msg["type"] == "join_room":
                    room_id = msg["room_id"]
                    resp = await session.post(f"{ROOM_URL}/join", json={"room_id": room_id, "username": username})
                    if resp.status != 200:
                        await ws.send_json({"type": "error", "message": "Cannot join room"})
                        continue
                    data = await resp.json()

                    if len(data["players"]) == 2:
                        first_player = data["players"][0]
                        await session.post(f"{GAME_URL}/start", json={"room_id": room_id, "players": data["players"]})
                        # THESE TWO LINES ARE CRITICAL — UI switches only because of this
                        await send_to_room(room_id, {"type": "game_start", "turn": first_player})
                        await send_to_room(room_id, {"type": "update", "sum": 0, "turn": first_player})

                elif msg["type"] == "move":
                    resp = await session.post(f"{GAME_URL}/move", json={
                        "room_id": room_id, "username": username, "prime": msg["prime"]
                    })
                    result = await resp.json()
                    if "winner" in result:
                        await send_to_room(room_id, {"type": "game_over", "winner": result["winner"]})
                    else:
                        await send_to_room(room_id, {"type": "update", "sum": result["sum"], "turn": result["turn"]})

        except WebSocketDisconnect:
            if username in connected_players:
                del connected_players[username]