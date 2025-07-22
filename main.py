from fastapi import FastAPI, HTTPException
from typing import Optional, List
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

app = FastAPI()

# MongoDB setup
client = AsyncIOMotorClient(MONGO_URI)
db = client.fastAPI
users_collection = db.users

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === Models ===

class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"

class UserBase(BaseModel):
    username: str = Field(examples=["John Doe", "Jane Doe"])
    email: EmailStr
    role: RoleEnum|None

class UserPassword(UserBase):
    password: str

class UserCreate(UserPassword, UserBase):
    pass

class UserOut(UserBase):
    id: str
    message: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[RoleEnum] = None

# === Utilities ===

async def get_user_by_email(email: str):
    return await users_collection.find_one({"email": email})

async def get_user_by_id(user_id: str):
    try:
        return await users_collection.find_one({"_id": ObjectId(user_id)})
    except:
        return None

# === Routes ===

@app.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    existing = await get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar.")

    hashed_password = pwd_context.hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password

    result = await users_collection.insert_one(user_dict)

    return UserOut(
        message="Registrasi berhasil",
        id=str(result.inserted_id),
        username=user.username,
        email=user.email,
        role=user.role
    )

@app.post("/login")
async def login(email: str, password: str):
    user = await get_user_by_email(email)
    if not user or not pwd_context.verify(password, user["password"]):
        raise HTTPException(status_code=401, detail="Login gagal")

    return {
        "message": "Login berhasil",
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        }
    }

@app.get("/users", response_model=List[UserOut])
async def get_users():
    users: List[UserOut] = []
    async for user in users_collection.find():
        print (user)
        users.append(UserOut(
            id=str(user["_id"]),
            username=user["username"],
            email=user["email"],
            role= user["role"] if "role" in user else None,
            message="Data ditemukan"
        ))
    return users

# === PATCH /users/{id} ===
@app.patch("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: str, update_data: UserUpdate):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}

    if "password" in update_dict:
        update_dict["password"] = pwd_context.hash(update_dict["password"])

    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_dict}
    )

    updated_user = await get_user_by_id(user_id)

    return UserOut(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user["email"],
        role=updated_user["role"],
        message="User berhasil diupdate"
    )

# === DELETE /users/{id} ===
@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    await users_collection.delete_one({"_id": ObjectId(user_id)})

    return {"message": "User berhasil dihapus", "id": user_id}
