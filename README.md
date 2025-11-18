# Prime Challenge - Distributed Two-Person Game System

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
| error           | message      | { "type": "error", "message": "..." }

---

## Setup, Configuration, and Requirements

- **See info.txt** (root directory) for all critical configuration, environment, run commands, and troubleshooting. This file is the authoritative reference for correct environment/platform setup.
- All Python dependencies are listed in `requirements.txt` and must be installed in your activated virtualenv with `pip install -r requirements.txt`.

---

## Mobile Android App: WebView-Based Approach

The mobile client for Prime Challenge is implemented using Java and the Android SDK. The app utilizes a `WebView` component that loads the full-featured web client UI, which is served by the Gateway service. This approach ensures:

- **Feature Parity:** Mobile users experience the exact same game features as desktop web users, including real-time play and account management.
- **Efficiency & Maintainability:** All improvements to the web client are instantly reflected on mobile without requiring duplicate native app logic.
- **Future Extensibility:** The current app acts as a robust proof of concept. It can readily be extended with native Android UX, notifications, or deeper integration if desired.

By utilizing WebView, the Android app provides a seamless, cross-platform gaming experience with rapid updates and minimal mobile-specific maintenance.

---

## Building and Running the Android App (APK)

To use the mobile app on a real device or emulator, you must generate and build the Android installation package (**APK**):

1. **Open the project in Android Studio**:
   - Navigate to the `mobile_app_android` directory and open the project using Android Studio (free and industry-standard IDE).
2. **Prepare a device or emulator**:
   - Connect your Android phone with a USB cable and enable developer mode (or use Android Studio's built-in emulator).
3. **Build the APK:**
   - Use the top menu: `Build > Build APK(s)`, or simply press the green 'Run' triangle to compile and launch directly on the device/emulator.
   - After building, the APK files will be found under `app/build/outputs/apk/` in your project structure.
4. **Install the APK:**
   - You can manually copy/install the APK to your Android device, or let Android Studio deploy it automatically.

**Notes:**
- Building the APK is required each time you want to install a new version on your device, or after changing any Java/Android-side code.
- Thanks to the WebView approach, updates to the web client UI and game logic become available on mobile instantly, without needing to repackage the APK unless the native code itself is modified.
- These steps follow industry best practices and ensure smooth deployment and evaluation for all stakeholders, including those new to Android development.
