from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import time

# === Setup ===
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# === MongoDB ===
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.fastAPI
blacklist_collection = db.blacklist

# === Security Setup ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

# === Password & Token Utama (Login) ===

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials

    if await blacklist_collection.find_one({"token": token}):
        raise HTTPException(status_code=401, detail="Token tidak valid (sudah logout)")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid")

def create_token(data: dict, expires_in_minutes: int):
    expire = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    data.update({"exp": expire})
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return token

async def get_current_user(token_data: dict = Depends(verify_token)):
    return token_data

# === Tambahan: Dependency untuk user yang sudah verifikasi email ===

async def get_verified_user(user: dict = Depends(get_current_user)):
    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun Anda belum memverifikasi email. Silakan verifikasi terlebih dahulu."
        )
    return user

# === Token untuk Verifikasi Email ===

def create_email_verification_token(email: str, expires_delta: timedelta = timedelta(days=1)):
    expire = int(time.time()) + int(expires_delta.total_seconds())
    payload = {
        "sub": email,
        "exp": expire,
        "type": "verify"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_email_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "verify":
            raise HTTPException(status_code=400, detail="Token tidak valid untuk verifikasi email")
        return payload.get("sub")
    except JWTError as e:
        print("❌ JWT ERROR:", e)
        raise HTTPException(status_code=400, detail="Token verifikasi email tidak valid atau kadaluarsa")

# === Token untuk Reset Password ===

def create_reset_password_token(email: str, expires_delta: timedelta = timedelta(minutes=30)):
    expire = int(time.time()) + int(expires_delta.total_seconds())
    payload = {
        "sub": email,
        "exp": expire,
        "type": "reset"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_reset_password_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Token tidak valid untuk reset password")
        return payload.get("sub")
    except JWTError as e:
        print("❌ JWT ERROR:", e)
        raise HTTPException(status_code=400, detail="Token reset password tidak valid atau kadaluarsa")

# === Token Verifikasi Umum dari String (misalnya dari URL query param) ===

def verify_token_from_string(token: str, token_type: str = None):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if token_type and payload.get("type") != token_type:
            raise HTTPException(status_code=400, detail=f"Token tidak valid untuk tipe: {token_type}")
        return payload
    except JWTError:
        raise HTTPException(status_code=400, detail="Token tidak valid atau sudah kedaluwarsa")

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah kedaluwarsa")
