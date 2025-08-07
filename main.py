# File: main.py
from fastapi import FastAPI
from dotenv import load_dotenv
import os
from database import db
from routes import user_routes, fakultas_routes, prodi_routes

# Load environment variables
load_dotenv()

app = FastAPI()

# MongoDB setup (already done in database.py)

# Include routes
app.include_router(user_routes.router, prefix="/users", tags=["Users"])
app.include_router(fakultas_routes.router, prefix="/fakultas", tags=["Fakultas"])
app.include_router(prodi_routes.router, prefix="/prodi", tags=["Prodi"])

# Optional: Root endpoint
@app.get("/")
def root():
    return {"message": "FastAPI Backend is running."}
