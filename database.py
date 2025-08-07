# database.py
from motor.motor_asyncio import AsyncIOMotorClient  # Import ini wajib ada
from dotenv import load_dotenv
import os  # Import ini juga wajib ada

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.fastAPI

users_collection = db.users
blacklist_collection = db.blacklist

fakultas_collection = db.fakultas
prodi_collection = db.prodi
