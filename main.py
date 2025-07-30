# File: main.py
from fastapi import FastAPI
from dotenv import load_dotenv
import os
from database import db
from routes import user_routes

# Load environment variables
load_dotenv()

app = FastAPI()

# MongoDB setup (already done in database.py)

# Routes
app.include_router(user_routes.router)

# Optional: Root endpoint
@app.get("/")
def root():
    return {"message": "FastAPI Backend is running."}
