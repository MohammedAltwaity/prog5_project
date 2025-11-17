# gateway/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import aiohttp
import json
import os

app = FastAPI()

# Fix the static folder path — works from anywhere!
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if not os.path.exists(STATIC_DIR):
    print(f"ERROR: 'static' folder not found at {STATIC_DIR}")
    print("Make sure you have: gateway/static/index.html")
else:
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"Static files serving from: {STATIC_DIR}")

# Optional: serve index.html directly at root for easier access
@app.get("/")
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Prime Lightning Server Running</h1><p>Open /static/index.html</p>")

# Service URLs
USER_URL = "http://localhost:8001"
ROOM_URL = "http://localhost:8002"
GAME_URL = "http://localhost:8003"

# Connected players: username → WebSocket
connected_players = {}

# Send message to both players in the same room (simple but works for 2 players)
async def send_to_room(room_id: str, message: dict):
    # We don't know who is in which room, so send to all and let client filter
    payload = json.dumps(message)
    for ws in list(connected_players.values()):
        try:
            await ws.send_text(payload)
        except:
            pass  # client disconnected

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

                # 1. Auth (register + login)
                if msg["type"] == "auth":
                    username = msg["username"]
                    password = msg["password"]

                    try:
                        # Try register (ignore if already exists)
                        await session.post(f"{USER_URL}/register", json={"username": username, "password": password})
                    except:
                        pass  # probably already exists

                    # Login
                    resp = await session.post(f"{USER_URL}/login", json={"username": username, "password": password})
                    if resp.status != 200:
                        await ws.send_json({"type": "error", "message": "Login failed"})
                        continue

                    connected_players[username] = ws
                    await ws.send_json({"type": "logged_in", "username": username})
                    print(f"Player logged in: {username}")

                # 2. Create Room
                elif msg["type"] == "create_room":
                    if not username:
                        continue
                    resp = await session.post(f"{ROOM_URL}/create", json={"username": username})
                    room = await resp.json()
                    room_id = room["room_id"]
                    await ws.send_json({"type": "room_created", "room_id": room_id})
                    print(f"{username} created room {room_id}")

                # 3. Join Room
                elif msg["type"] == "join_room":
                    if not username:
                        continue
                    room_id = msg["room_id"]
                    resp = await session.post(f"{ROOM_URL}/join", json={"room_id": room_id, "username": username})
                    if resp.status != 200:
                        await ws.send_json({"type": "error", "message": "Cannot join room"})
                        continue

                    data = await resp.json()
                    await send_to_room(room_id, {"type": "player_joined", "players": data["players"]})

                    if len(data["players"]) == 2:
                        await session.post(f"{GAME_URL}/start", json={"room_id": room_id, "players": data["players"]})
                        await send_to_room(room_id, {
                            "type": "game_start",
                            "turn": data["players"][0],
                            "message": "Game started!"
                        })
                        print(f"Game started in room {room_id}: {data['players']}")

                # 4. Make Move
                elif msg["type"] == "move":
                    if not username or not room_id:
                        continue
                    resp = await session.post(f"{GAME_URL}/move", json={
                        "room_id": room_id,
                        "username": username,
                        "prime": msg["prime"]
                    })

                    if resp.status != 200:
                        error = await resp.text()
                        await ws.send_json({"type": "error", "message": error})
                        continue

                    result = await resp.json()
                    if "winner" in result:
                        await send_to_room(room_id, {"type": "game_over", "winner": result["winner"]})
                        print(f"Game over in {room_id} → Winner: {result['winner']}")
                    else:
                        await send_to_room(room_id, {
                            "type": "update",
                            "sum": result["sum"],
                            "turn": result["turn"]
                        })

        except WebSocketDisconnect:
            print(f"Player disconnected: {username}")
            if username in connected_players:
                del connected_players[username]
        except Exception as e:
            print(f"WebSocket error: {e}")
            if username in connected_players:
                del connected_players[username]