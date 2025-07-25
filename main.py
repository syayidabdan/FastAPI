from fastapi import FastAPI, HTTPException, APIRouter, Depends, Query, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional, List
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv
from auth import hash_password, verify_password, create_access_token, get_current_user, verify_token, blacklist_collection
import os

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

app = FastAPI()
router = APIRouter()

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
    username: str = Field(examples=["John Doe"])
    email: EmailStr
    role: Optional[RoleEnum] = None

class UserPassword(UserBase):
    password: str

class UserCreate(UserPassword):
    pass

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserOut(UserBase):
    id: str
    message: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[RoleEnum] = None

class Token(BaseModel):
    access_token: str
    token_type: str

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

    hashed_password = hash_password(user.password)
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

@app.post("/login", response_model=Token)
async def login(form_data: UserLoginRequest = Depends()):
    user = await users_collection.find_one({
        "$or": [
            {"email": form_data.username},
            {"username": form_data.username}
        ]
    })

    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Login gagal")

    token_data = {
        "user_id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user.get("role", "user")
    }

    access_token = create_access_token(data=token_data)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/me")
async def read_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": str(current_user["user_id"]),
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user.get("role", "user")
    }

@app.get("/users")
async def get_users(
    skip: int = 0,
    limit: int = 10,
    username: str = Query(None),
    email: str = Query(None),
    role: str = Query(None)
):
    # Buat query dictionary
    query = {}
    if username:
        query["username"] = username
    if email:
        query["email"] = email
    if role:
        query["role"] = role

    # Hitung total yang sesuai filter
    total = await users_collection.count_documents(query)

    # Ambil data sesuai filter
    users = []
    cursor = users_collection.find(query).skip(skip).limit(limit)
    async for user in cursor:
        users.append({
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "role": user.get("role", None),
            "message": "Data ditemukan"
        })

    return {
        "total_users": total,
        "skip": skip,
        "limit": limit,
        "data": users
    }

@app.patch("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: str, update_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    # Hanya admin yang boleh akses endpoint ini
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang dapat mengupdate user lain")

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}

    # Hash password jika diupdate
    if "password" in update_dict:
        update_dict["password"] = hash_password(update_dict["password"])

    # Cegah admin mengubah role dirinya sendiri
    if current_user["user_id"] == user_id and "role" in update_dict:
        raise HTTPException(status_code=403, detail="Admin tidak dapat mengubah role dirinya sendiri")

    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_dict}
    )

    updated_user = await get_user_by_id(user_id)

    return UserOut(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user["email"],
        role=updated_user.get("role", None),
        message="User berhasil diupdate"
    )

@app.patch("/update-user")
async def update_self(data: UserUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {}

    if data.username:
        update_data["username"] = data.username
    if data.email:
        update_data["email"] = data.email
    if data.password:
        update_data["password"] = hash_password(data.password)
    
    # Jangan izinkan user ubah rolenya sendiri!
    # if data.role:
    #     update_data["role"] = data.role

    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada data yang diupdate.")

    result = await users_collection.update_one(
        {"_id": ObjectId(current_user["user_id"])}, {"$set": update_data}
    )

    if result.modified_count == 0:
        return {"message": "Tidak ada perubahan data."}

    return {"message": "Data user berhasil diupdate."}

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    await users_collection.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User berhasil dihapus", "id": user_id}

@router.post("/logout")
async def logout(request: Request, token: dict = Depends(verify_token)):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header tidak ditemukan")

    token_str = auth_header.replace("Bearer ", "")
    await blacklist_collection.insert_one({"token": token_str})

    return {"message": "Logout berhasil. Token telah di-blacklist"}

# <- Tambahkan ini supaya router aktif
app.include_router(router)
