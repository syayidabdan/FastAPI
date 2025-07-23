# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client["user_db"]
users_collection = db["users"]

# Fungsi ambil user by ID
async def get_user_by_id(user_id: str):
    return await users_collection.find_one({"_id": ObjectId(user_id)})
