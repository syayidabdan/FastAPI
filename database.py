# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# === MongoDB Connection ===
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.fastAPI

# === Collections ===
users_collection = db.users
blacklist_collection = db.blacklist  # digunakan untuk logout (JWT blacklist)

fakultas_collection = db["fakultas"]