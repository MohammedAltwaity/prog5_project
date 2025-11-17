# game_service/main.py - WINNER AT 30/31 FIXED!
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List

app = FastAPI(title="Game Rules Service")

PRIMES = [2, 3, 5, 7, 11]
TARGET = 31

games: Dict[str, dict] = {}

class MoveRequest(BaseModel):
    room_id: str
    username: str
    prime: int

@app.post("/start")
async def start_game(request: dict):
    room_id = request["room_id"]
    players = request["players"]
    games[room_id] = {
        "sum": 0,
        "turn": players[0],
        "players": players,
        "winner": None
    }
    print(f"Game started: {room_id} with {players}")
    return {"message": "started"}

@app.post("/move")
async def make_move(req: MoveRequest):
    if req.room_id not in games:
        raise HTTPException(404, "Game not found")
    
    game = games[req.room_id]
    
    if game["winner"]:
        raise HTTPException(400, "Game finished")
    
    if req.username != game["turn"]:
        raise HTTPException(400, "Not your turn!")
    
    if req.prime not in PRIMES:
        raise HTTPException(400, f"Invalid prime! Use: {PRIMES}")
    
    new_sum = game["sum"] + req.prime
    if new_sum > TARGET:
        raise HTTPException(400, f"Cannot exceed {TARGET}!")

    # UPDATE GAME
    game["sum"] = new_sum
    
    # WIN CONDITION 1: Exactly 31
    if new_sum == TARGET:
        game["winner"] = req.username
        print(f"🎉 WINNER by exact 31 in {req.room_id}: {req.username}")
        return {"winner": req.username}
    
    # WIN CONDITION 2: Opponent has NO MOVES LEFT (like 30/31)
    possible_moves = [p for p in PRIMES if game["sum"] + p <= TARGET]
    if not possible_moves:
        game["winner"] = req.username  # You win because opponent can't move!
        print(f"🎉 WINNER by trapping opponent in {req.room_id}: {req.username} (sum={new_sum})")
        return {"winner": req.username}
    
    # Switch turn
    game["turn"] = game["players"][1] if req.username == game["players"][0] else game["players"][0]
    
    print(f"Move: {req.prime} → sum={new_sum}, turn={game['turn']}, possible={possible_moves}")
    return {"sum": new_sum, "turn": game["turn"]}