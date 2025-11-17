# user_service/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="User Service")

# This dictionary stores usernames and passwords in memory
# Example: {"alice": "123", "bob": "secret"}
users_db = {}

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
    return {"message": "You are registered!"}

# Login with username + password
@app.post("/login")
async def login(user: UserData):
    if user.username not in users_db:
        raise HTTPException(401, "Wrong username or password")
    if users_db[user.username] != user.password:
        raise HTTPException(401, "Wrong username or password")
    return {"message": "Login successful!"}