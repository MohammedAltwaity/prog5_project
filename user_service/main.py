# user_service/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

app = FastAPI(title="User Service")

# Note: No CORS needed - this service is only called by the gateway (server-to-server)

# File to store users - saved in the user_service directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.txt")

# This dictionary stores usernames and passwords
# Example: {"alice": "123", "bob": "secret"}
users_db = {}

def load_users():
    """Load users from the text file"""
    global users_db
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and ":" in line:
                        username, password = line.split(":", 1)
                        users_db[username] = password
        except Exception as e:
            print(f"Error loading users: {e}")

def save_users():
    """Save users to the text file"""
    try:
        with open(USERS_FILE, "w") as f:
            for username, password in users_db.items():
                f.write(f"{username}:{password}\n")
    except Exception as e:
        print(f"Error saving users: {e}")

# Load users on startup
load_users()

# This defines the format of data we receive (username + password)
class UserData(BaseModel):
    username: str
    password: str

# Register a new user
@app.post("/register")
async def register(user: UserData):
    if user.username in users_db:
        raise HTTPException(400, "Username already taken!")
    users_db[user.username] = user.password
    save_users()  # Save to file
    return {"message": "You are registered!"}

# Login with username + password
@app.post("/login")
async def login(user: UserData):
    if user.username not in users_db:
        raise HTTPException(401, "Wrong username or password")
    if users_db[user.username] != user.password:
        raise HTTPException(401, "Wrong username or password")
    return {"message": "Login successful!"}