
import asyncio
import websockets
import json

async def main():
    print("Prime Lightning – First to 31 (CLI Version)")
    print("Allowed primes: 2, 3, 5, 7, 11\n")

    # Connect to gateway
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        # 1. Login
        username = input("Username: ")
        password = input("Password: ")
        await ws.send(json.dumps({
            "type": "auth",
            "username": username,
            "password": password
        }))
        await ws.recv()  # wait for logged_in

        print(f"\nLogged in as {username}")
        print("1) Create Room")
        print("2) Join Room")
        choice = input("Choose (1 or 2): ")

        room_id = None

        if choice == "1":
            await ws.send(json.dumps({"type": "create_room"}))
            msg = json.loads(await ws.recv())
            room_id = msg["room_id"]
            print(f"\nRoom created! → Share this ID: {room_id}")
            print("Waiting for opponent to join...\n")
        else:
            room_id = input("Enter Room ID: ")
            await ws.send(json.dumps({"type": "join_room", "room_id": room_id}))
            print("Joining room...")

        # Game loop
        while True:
            message = json.loads(await ws.recv())

            if message["type"] == "game_start":
                print("GAME STARTED! Your turn first!\n" if message["turn"] == username else "Opponent starts!\n")

            elif message["type"] == "update":
                print(f"Current sum: {message['sum']} / 31")
                if message["turn"] == username:
                    print("YOUR TURN! Choose prime:")
                    possible = [p for p in [2,3,5,7,11] if message['sum'] + p <= 31]
                    print("Possible moves:", possible if possible else "NONE → You lose!")
                    if not possible:
                        print("You can't move → You lose!")
                        break
                    while True:
                        try:
                            move = int(input(">> "))
                            if move in possible:
                                await ws.send(json.dumps({"type": "move", "prime": move}))
                                break
                            else:
                                print("Invalid! Choose from:", possible)
                        except:
                            print("Type a number!")
                else:
                    print("Opponent is thinking...\n")

            elif message["type"] == "game_over":
                winner = message["winner"]
                if winner == username:
                    print(f"WINNER: YOU WIN! ({winner})")
                else:
                    print(f"WINNER: {winner} WINS! You lose.")
                break

        print("\nGame finished. Close window or run again!")

# Run it
asyncio.run(main())