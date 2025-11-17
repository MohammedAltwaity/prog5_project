#!/usr/bin/env python3
"""
Simple CLI Client for Prime Challenge Game
Terminal-based interface similar to web client
"""
import asyncio
import json
import websockets
import aiohttp
import sys

GATEWAY_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

async def async_input(prompt=""):
    """Non-blocking input"""
    return await asyncio.to_thread(input, prompt)

async def register_user(username: str, password: str) -> bool:
    """Register through gateway"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GATEWAY_URL}/register",
                json={"username": username, "password": password}
            ) as resp:
                return resp.status == 200
    except:
        return False

async def login_user(username: str, password: str) -> bool:
    """Login through gateway"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GATEWAY_URL}/login",
                json={"username": username, "password": password}
            ) as resp:
                return resp.status == 200
    except:
        return False

async def receiver(ws, queue):
    """Receive WebSocket messages"""
    while True:
        try:
            msg = json.loads(await ws.recv())
            await queue.put(msg)
        except:
            break

async def main():
    print("\n=== Prime Challenge - CLI Client ===\n")
    
    try:
        ws = await websockets.connect(WS_URL)
        queue = asyncio.Queue()
        asyncio.create_task(receiver(ws, queue))
        
        # Authentication
        print("Authentication:")
        has_account = await async_input("Do you have an account? (y/n): ")
        has_account = has_account.strip().lower()
        
        username = await async_input("Username: ")
        username = username.strip()
        password = await async_input("Password: ")
        password = password.strip()
        
        if has_account in ['n', 'no']:
            print("Registering...")
            if await register_user(username, password):
                print("Registered successfully!")
            else:
                print("Registration failed")
                return
        
        print("Logging in...")
        if await login_user(username, password):
            print("Login successful!")
        else:
            print("Login failed - wrong username or password")
            return
        
        # WebSocket auth
        await ws.send(json.dumps({
            "type": "auth",
            "username": username,
            "password": password
        }))
        
        # Wait for logged_in
        while True:
            msg = await queue.get()
            if msg["type"] == "logged_in":
                print(f"Connected as {username}\n")
                break
        
        # Room setup
        print("Room Setup:")
        choice = await async_input("1) Create Room   2) Join Room: ")
        choice = choice.strip()
        
        if choice == "1":
            await ws.send(json.dumps({"type": "create_room"}))
            while True:
                msg = await queue.get()
                if msg["type"] == "room_created":
                    room_id = msg["room_id"]
                    print(f"\nRoom created: {room_id}")
                    print("Share this ID with your opponent")
                    print("Waiting for opponent...\n")
                    break
        else:
            room_id = await async_input("Enter Room ID: ")
            room_id = room_id.strip()
            await ws.send(json.dumps({"type": "join_room", "room_id": room_id}))
            print("Joining room...\n")
        
        # Game loop
        print("Game started! Allowed primes: 2, 3, 5, 7, 11")
        print("Goal: Reach 31 or trap opponent\n")
        
        while True:
            msg = await queue.get()
            
            if msg["type"] == "update":
                current_sum = msg["sum"]
                turn = msg["turn"]
                
                print(f"Current: {current_sum} / 31")
                
                if turn == username:
                    possible = [p for p in [2, 3, 5, 7, 11] if current_sum + p <= 31]
                    print(f"YOUR TURN! Possible moves: {possible}")
                    
                    while True:
                        move_input = await async_input("Your move: ")
                        if move_input.isdigit():
                            move = int(move_input)
                            if move in possible:
                                break
                        print(f"Invalid. Choose from: {possible}")
                    
                    await ws.send(json.dumps({"type": "move", "prime": move}))
                    print(f"You played {move}\n")
                else:
                    print(f"Waiting for {turn}...\n")
            
            elif msg["type"] == "game_over":
                winner = msg["winner"]
                if winner == username:
                    print("YOU WIN!")
                else:
                    print(f"{winner} wins!")
                
                restart = await async_input("\nPlay again? (y/n): ")
                restart = restart.strip().lower()
                
                if restart in ['y', 'yes']:
                    await ws.send(json.dumps({"type": "restart_game"}))
                    print("Restarting game...\n")
                    # Wait for restart
                    while True:
                        restart_msg = await queue.get()
                        if restart_msg["type"] == "update":
                            break
                else:
                    print("Thanks for playing!")
                    break
            
            elif msg["type"] == "error":
                print(f"Error: {msg.get('message', 'Unknown error')}")
    
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except ConnectionRefusedError:
        print("Cannot connect to server. Make sure services are running.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            await ws.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
