# cli_client.py – FINAL VERSION (NO INPUT MESS-UP EVER!)
import asyncio
import json
import websockets

async def main():
    print("Prime Lightning – First to 31")
    print("Allowed primes: 2, 3, 5, 7, 11\n")

    ws = await websockets.connect("ws://localhost:8000/ws")

    # === LOGIN ===
    username = input("Username: ")
    password = input("Password: ")
    await ws.send(json.dumps({"type": "auth", "username": username, "password": password}))

    # Wait for login confirmation
    while True:
        msg = json.loads(await ws.recv())
        if msg["type"] == "logged_in":
            print(f"\nLogged in as {username}\n")
            break

    # === CREATE OR JOIN ROOM ===
    choice = input("1) Create Room   2) Join Room → ")
    room_id = None

    if choice.strip() == "1":
        await ws.send(json.dumps({"type": "create_room"}))
        while True:
            msg = json.loads(await ws.recv())
            if msg["type"] == "room_created":
                room_id = msg["room_id"]
                print(f"\nRoom created! Share this ID → {room_id}")
                print("Waiting for opponent...\n")
                break
    else:
        room_id = input("\nEnter Room ID: ")
        await ws.send(json.dumps({"type": "join_room", "room_id": room_id}))
        print("Joining room...\n")

    # === GAME LOOP – THIS IS THE MAGIC PART ===
    while True:
        msg = json.loads(await ws.recv())

        # Only print game messages – ignore duplicates
        if msg["type"] == "game_start":
            print("Opponent joined! Game started!\n")

        elif msg["type"] == "update":
            print(f"Current sum: {msg['sum']} / 31")

            if msg["turn"] == username:
                possible = [p for p in [2,3,5,7,11] if msg['sum'] + p <= 31]
                if not possible:
                    print("No valid moves → You lose!")
                    break

                print("YOUR TURN! Possible moves:", " ".join(map(str, possible)))
                while True:
                    move = input(">> ").strip()
                    if move.isdigit() and int(move) in possible:
                        await ws.send(json.dumps({"type": "move", "prime": int(move)}))
                        print(f"→ You played {move}\n")
                        break
                    else:
                        print("Invalid! Choose from:", " ".join(map(str, possible)))
            else:
                print("Opponent's turn...\n")

        elif msg["type"] == "game_over":
            winner = msg["winner"]
            if winner == username:
                print("YOU WIN!")
            else:
                print(f"You lose → {winner} wins!")
            print("\nGame over!")
            break

    input("\nPress Enter to exit...")

# Run
asyncio.run(main())