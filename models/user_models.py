from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# === Enum untuk Role User ===
class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"

# === Base User ===
class UserBase(BaseModel):
    username: str = Field(examples=["John Doe"])
    email: EmailStr
    role: Optional[RoleEnum] = None

# === Model User + Password ===
class UserPassword(UserBase):
    password: str

# === Model Saat Register ===
class UserCreate(UserPassword):
    pass

# === Model Saat Login ===
class UserLoginRequest(BaseModel):
    username: str
    password: str

# === Model Untuk Output ===
class UserOut(UserBase):
    id: str
    message: str

# === Model Untuk Admin Update User ===
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[RoleEnum] = None

# === Model JWT Token Response ===
class Token(BaseModel):
    access_token: str
    token_type: str

# === Model User Update Diri Sendiri ===
class UserSelfUpdate(BaseModel):
    username: Optional[str]
    email: Optional[str]
    password: Optional[str]

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=6)

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)

class EmailChangeRequest(BaseModel):
    new_email: EmailStr