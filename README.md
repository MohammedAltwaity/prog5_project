# Prime Challenge - Distributed Two-Person Game System

---

## Assignment Required Documentation Overview

This README covers:
- Technology summary for all microservices and clients
- Project and architecture description
- Service-to-service API documentation (REST schemas, responsibilities)
- WebSocket API communication (full schema and flows, client-server/client)
- Configuration/run/troubleshooting (info.txt, requirements.txt)

**Refer to the section headers or assignment checklist below for compliance confirmation.**

---

## Technology Summary

| Component         | Programming Language | Frameworks/Libraries                                |
|-------------------|---------------------|-----------------------------------------------------|
| Gateway Service   | Python 3.9+         | FastAPI, aiohttp, uvicorn, websockets, Pydantic     |
| User Service      | Python 3.9+         | FastAPI, Pydantic                                   |
| Room Service      | Python 3.9+         | FastAPI, Pydantic                                   |
| Game Service      | Python 3.9+         | FastAPI, Pydantic                                   |
| Web Client        | HTML/CSS/JS         | Served static/index.html by Gateway                 |
| CLI Client        | Python 3.9+         | aiohttp, websockets, prompt_toolkit                 |
| Mobile Client     | Java (Android)      | Android SDK, WebView (loads web interface)          |

---

## Project Description

Prime Challenge is a distributed, microservices-based, turn-based game where two players compete to reach exactly 31 by adding allowed prime numbers (2, 3, 5, 7, 11). The modular design provides user authentication, room/lobby management, game logic processing, and real-time communication for both CLI and web clients via a unified Gateway.

- **Gateway Service:** Entry point, API Gateway and WebSocket server, routes and authenticates all requests.
- **User Service:** Handles user creation (registration) and authentication.
- **Room Service:** Manages game rooms/lobbies—players create/join rooms for matches.
- **Game Service:** Maintains game rules, validates moves, detects win conditions.
- **Clients:** Browser-based web app, Python-based CLI, and an Android app using a WebView (work-in-progress).

---

## Service-to-Service APIs (REST via Gateway)
All inter-service communication flows through the Gateway. Microservices do **not** directly call each other—this simplifies security and scaling.

| Gateway Endpoint              | Forwards to         | Method | Payload (Example) | Response Example |
|-------------------------------|---------------------|--------|--------------------|------------------|
| /register                     | User /register      | POST   | { "username": ..., "password": ... } | { "message": "You are registered!" }
| /login                        | User /login         | POST   | { "username": ..., "password": ... } | { "message": "Login successful!" }
| WebSocket "create_room"       | Room /create        | POST   | { "username": ... } | { "room_id": "R0" }
| WebSocket "join_room"         | Room /join          | POST   | { "room_id": ..., "username": ... } | { "players": [U1, U2] }
| WebSocket "move"              | Game /move          | POST   | { "room_id": ..., "username": ..., "prime": N } | { "sum": N, "turn": "user" } or { "winner": "user" }
| WebSocket "restart_game"      | Game /restart       | POST   | { "room_id": ... } | { "message": ..., "turn": ... }
| WebSocket (room full event)    | Game /start         | POST   | { "room_id": ..., "players": [U1,U2] } | { "message": "started" }

*No direct calls between Room/User or Game/Room, etc—Gateway acts as sole orchestrator.*

---

## API Endpoints (Microservice Summary)

- **Gateway Service (8000):**
    - `GET /`: Serves UI
    - `POST /register`, `POST /login`: Proxy to User Service
    - `ws://localhost:8000/ws`: WebSocket endpoint (see messages below)
- **User Service (8001):**
    - `POST /register`, `POST /login`
- **Room Service (8002):**
    - `POST /create`, `POST /join`
- **Game Service (8003):**
    - `POST /start`, `POST /move`, `POST /restart`
- (See full run details/config in info.txt)

---

## Client-Server APIs: WebSocket JSON Message Schemas

**Format:** All messages are JSON (UTF-8). Field presence as shown below.

### Client → Gateway (WebSocket) Messages

| Type           | Fields             | Example |
|----------------|--------------------|---------|
| auth           | username, password | { "type": "auth", "username": "alice", "password": "secret" }
| create_room    |                    | { "type": "create_room" }
| join_room      | room_id            | { "type": "join_room", "room_id": "R0" }
| move           | prime              | { "type": "move", "prime": 7 }
| restart_game   |                    | { "type": "restart_game" }

### Gateway → Client (WebSocket) Messages

| Type            | Fields        | Example |
|-----------------|--------------|---------|
| logged_in       | username     | { "type": "logged_in", "username": "alice" }
| room_created    | room_id      | { "type": "room_created", "room_id": "R0" }
| game_start      | turn         | { "type": "game_start", "turn": "alice" }
| update          | sum, turn    | { "type": "update", "sum": 19, "turn": "bob" }
| game_over       | winner       | { "type": "game_over", "winner": "alice" }
| game_restarted  | turn         | { "type": "game_restarted", "turn": "alice" }
| error           | message      | { "type": "error", "message": "...
