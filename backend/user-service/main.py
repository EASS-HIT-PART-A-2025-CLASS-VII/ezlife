from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Reconfigure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["task_management"]

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# User model
class User(BaseModel):
    email: str
    password: str

@app.post("/register")
def register_user(user: User):
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    user_dict["created_at"] = datetime.utcnow()
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    # Add phone field if provided
    if hasattr(user, "phone") and user.phone:
        user_dict["phone"] = user.phone
    db.users.insert_one(user_dict)
    return {"message": "User registered successfully"}

@app.post("/token")
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": user["email"], "token_type": "bearer"}

# Update preflight handler to include CORS headers
@app.options("/{path:path}")
def preflight_handler(path: str):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(status_code=200, headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
