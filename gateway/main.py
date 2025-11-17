# gateway/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiohttp
import json
import os

app = FastAPI(title="API Gateway")

# Add CORS middleware (though not needed if same origin, but good practice)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins since gateway is the entry point
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    with open(os.path.join(STATIC_DIR, "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# Pydantic models for authentication
class UserData(BaseModel):
    username: str
    password: str

USER_URL = "http://localhost:8001"
ROOM_URL = "http://localhost:8002"
GAME_URL = "http://localhost:8003"

connected_players = {}  # username -> WebSocket
player_rooms = {}  # username -> room_id

# Authentication endpoints - proxy to user service
@app.post("/register")
async def register(user: UserData):
    """Register a new user through the gateway"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{USER_URL}/register", json={"username": user.username, "password": user.password}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                else:
                    error_data = await resp.json()
                    raise HTTPException(status_code=resp.status, detail=error_data.get("detail", "Registration failed"))
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/login")
async def login(user: UserData):
    """Login through the gateway"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{USER_URL}/login", json={"username": user.username, "password": user.password}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                else:
                    error_data = await resp.json()
                    raise HTTPException(status_code=resp.status, detail=error_data.get("detail", "Login failed"))
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=503, detail="User service unavailable")

async def send_to_room(room_id: str, message: dict):
    """Send message to all players in a room"""
    payload = json.dumps(message)
    for username, ws in list(connected_players.items()):
        if player_rooms.get(username) == room_id:
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
                    player_rooms[username] = room_id  # Track player's room
                    await ws.send_json({"type": "room_created", "room_id": room_id})

                elif msg["type"] == "join_room":
                    room_id = msg["room_id"]
                    player_rooms[username] = room_id  # Track player's room
                    resp = await session.post(f"{ROOM_URL}/join", json={"room_id": room_id, "username": username})
                    if resp.status != 200:
                        await ws.send_json({"type": "error", "message": "Cannot join room"})
                        continue
                    data = await resp.json()

                    if len(data["players"]) == 2:
                        first_player = data["players"][0]
                        # Track both players' rooms
                        for player in data["players"]:
                            if player in connected_players:
                                player_rooms[player] = room_id
                        await session.post(f"{GAME_URL}/start", json={"room_id": room_id, "players": data["players"]})
                        # THESE TWO LINES ARE CRITICAL — UI switches only because of this
                        await send_to_room(room_id, {"type": "game_start", "turn": first_player})
                        await send_to_room(room_id, {"type": "update", "sum": 0, "turn": first_player})

                elif msg["type"] == "restart_game":
                    # Get room_id from tracked rooms (more reliable than local variable)
                    current_room = player_rooms.get(username)
                    if not current_room:
                        await ws.send_json({"type": "error", "message": "Not in a room"})
                        continue
                    room_id = current_room  # Update local variable too
                    resp = await session.post(f"{GAME_URL}/restart", json={"room_id": room_id})
                    if resp.status == 200:
                        result = await resp.json()
                        first_player = result["turn"]
                        # Notify both players that game restarted
                        await send_to_room(room_id, {"type": "game_restarted", "turn": first_player})
                        await send_to_room(room_id, {"type": "update", "sum": 0, "turn": first_player})
                    else:
                        await ws.send_json({"type": "error", "message": "Cannot restart game"})

                elif msg["type"] == "move":
                    # Get room_id from tracked rooms (more reliable)
                    current_room = player_rooms.get(username) or room_id
                    if not current_room:
                        await ws.send_json({"type": "error", "message": "Not in a room"})
                        continue
                    room_id = current_room  # Update local variable
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
            if username in player_rooms:
                del player_rooms[username]