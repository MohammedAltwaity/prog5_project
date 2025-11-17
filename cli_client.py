# cli_client_async_fixed.py
import asyncio
import json
import websockets

async def async_input(prompt=""):
    return await asyncio.to_thread(input, prompt)

async def receiver(ws, queue):
    """Receives WebSocket messages without blocking."""
    while True:
        try:
            msg = json.loads(await ws.recv())
            await queue.put(msg)
        except:
            break

async def main():
    print("Prime Lightning – First to 31")
    print("Allowed primes: 2, 3, 5, 7, 11\n")

    ws = await websockets.connect("ws://localhost:8000/ws")
    queue = asyncio.Queue()
    asyncio.create_task(receiver(ws, queue))

    # Login
    username = await async_input("Username: ")
    password = await async_input("Password: ")

    await ws.send(json.dumps({
        "type": "auth",
        "username": username,
        "password": password
    }))

    while True:
        msg = await queue.get()
        if msg["type"] == "logged_in":
            print(f"\nLogged in as {username}\n")
            break

    # Create / Join room
    choice = await async_input("1) Create Room   2) Join Room → ")

    if choice.strip() == "1":
        await ws.send(json.dumps({"type": "create_room"}))
        while True:
            msg = await queue.get()
            if msg["type"] == "room_created":
                print(f"\nRoom created → {msg['room_id']}")
                print("Waiting for opponent...\n")
                break
    else:
        room_id = await async_input("\nEnter Room ID: ")
        await ws.send(json.dumps({"type": "join_room", "room_id": room_id}))
        print("Joining room...\n")

    # ==== GAME LOOP ====
    game_started = False

    while True:
        msg = await queue.get()

        if msg["type"] == "game_start":
            print("Opponent joined! Game started!\n")
            game_started = True
            continue  # wait for update BEFORE prompting

        if msg["type"] == "update":
            current_sum = msg["sum"]
            turn = msg["turn"]

            print(f"Current sum: {current_sum} / 31")

            if turn == username:
                possible = [p for p in [2,3,5,7,11] if current_sum + p <= 31]

                print("YOUR TURN! Possible moves:", possible)

                move = None
                while True:
                    move = await async_input(">> ")
                    if move.isdigit() and int(move) in possible:
                        break
                    print("Invalid. Choose:", possible)

                await ws.send(json.dumps({
                    "type": "move",
                    "prime": int(move)
                }))
                print(f"→ You played {move}\n")

            else:
                print(f"Opponent's turn ({turn})...\n")

        if msg["type"] == "game_over":
            winner = msg["winner"]
            if winner == username:
                print("YOU WIN!")
            else:
                print(f"You lose → {winner} wins!")
            break

    await async_input("\nPress Enter to exit...")

asyncio.run(main())
