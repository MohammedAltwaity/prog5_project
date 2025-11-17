# room_service/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI(title="Room Service")

# Stores all rooms: "R0": {"players": ["alice"], "status": "waiting"}
rooms: Dict[str, dict] = {}
counter = 0

class CreateRequest(BaseModel):
    username: str

class JoinRequest(BaseModel):
    room_id: str
    username: str

# Player creates a new room
@app.post("/create")
async def create_room(req: CreateRequest):
    global counter
    room_id = f"R{counter}"
    counter += 1
    rooms[room_id] = {"players": [req.username], "status": "waiting"}
    return {"room_id": room_id}

# Second player joins the room
@app.post("/join")
async def join_room(req: JoinRequest):
    if req.room_id not in rooms:
        raise HTTPException(404, "Room not found!")
    room = rooms[req.room_id]
    if len(room["players"]) >= 2:
        raise HTTPException(400, "Room is full!")
    if req.username in room["players"]:
        raise HTTPException(400, "You are already in this room!")
    
    room["players"].append(req.username)
    room["status"] = "full"
    return {"players": room["players"]}