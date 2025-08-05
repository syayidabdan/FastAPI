from fastapi import APIRouter, Depends, HTTPException, Query, Request
from bson import ObjectId
from urllib.parse import quote

from jose import JWTError

from models.user_models import (
    UserCreate,
    UserLoginRequest,
    UserOut,
    UserUpdate,
    UserSelfUpdate,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
    EmailChangeRequest
)

from utils.email_utils import send_email, send_verification_email

from auth.token import (
    SECRET_KEY,
    create_email_verification_token,
    create_token,
    verify_email_token,
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_verified_user,
    verify_token,
    create_reset_password_token,
    verify_reset_password_token,
    blacklist_collection,
    verify_token_from_string
)

from database import users_collection

router = APIRouter()

# == Utilities ==
async def get_user_by_email(email: str):
    return await users_collection.find_one({"email": email})

async def get_user_by_id(user_id: str):
    try:
        return await users_collection.find_one({"_id": ObjectId(user_id)})
    except:
        return None

# == Routes ==
@router.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    existing = await get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar.")

    hashed_password = hash_password(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    user_dict["is_verified"] = False

    result = await users_collection.insert_one(user_dict)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Gagal menyimpan user ke database.")

    verification_token = create_email_verification_token(user.email)
    send_verification_email(user.email, verification_token)

    return UserOut(
        message="Registrasi berhasil",
        id=str(result.inserted_id),
        username=user.username,
        email=user.email,
        role=user.role
    )

@router.put("/users/change-email")
async def change_email(
    payload: EmailChangeRequest,
    current_user: dict = Depends(get_current_user)
):
    print("DEBUG current_user:", current_user)

    user_id = current_user.get("user_id")   # fix di sini
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID tidak ditemukan")

    try:
        user_obj_id = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="User ID tidak valid")

    new_email = payload.new_email

    # cek apakah email baru sudah ada
    existing_user = await users_collection.find_one({"email": new_email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email sudah digunakan")

    # bikin token verifikasi untuk email baru
    token_data = {
        "sub": new_email,
        "type": "verify_new_email"
    }
    verification_token = create_token(token_data, expires_in_minutes=60 * 24)

    verification_link = f"http://localhost:8000/users/verify-new-email?token={verification_token}"
    email_body = f"""
        <p>Klik link berikut untuk memverifikasi email baru Anda:<br>
        <a href="{verification_link}">{verification_link}</a></p>
    """
    send_email(new_email, "Verifikasi Email Baru Anda", email_body)

    # update user
    await users_collection.update_one(
        {"_id": user_obj_id},
        {
            "$set": {
                "is_verified": False,
                "pending_email": new_email,
                "email_verification_token": verification_token
            }
        }
    )

    return {"message": "Silakan cek email baru Anda untuk verifikasi"}

@router.get("/users/verify-new-email")
async def verify_new_email(token: str, request: Request):
    try:
        # ✅ Gunakan fungsi khusus ini
        payload = verify_token_from_string(token)

        if payload["type"] != "verify_new_email":
            raise HTTPException(status_code=400, detail="Token tidak valid untuk verifikasi email baru")

        new_email = payload["sub"]

        user = await users_collection.find_one({"email_verification_token": token})
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan atau token tidak valid")

        await users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "email": new_email,
                    "is_verified": True
                },
                "$unset": {
                    "pending_email": "",
                    "email_verification_token": ""
                }
            }
        )

        return {"message": "Email berhasil diverifikasi"}

    except JWTError:
        raise HTTPException(status_code=400, detail="Token tidak valid atau sudah kedaluwarsa")

@router.post("/login")
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
        "role": user.get("role", "user"),
        "is_verified": user.get("is_verified", False)
    }

    access_token = create_access_token(data=token_data)

    return {
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        },
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/request-password-reset")
async def request_password_reset(data: PasswordResetRequest):
    user = await users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Email tidak ditemukan.")

    token = create_reset_password_token(data.email)
    encoded_token = quote(token)

    reset_link = f"http://localhost:8000/reset-password?token={encoded_token}"
    email_content = f"""
    Anda meminta reset password.
    Silakan klik link berikut untuk mengganti password:
    {reset_link}

    Abaikan jika Anda tidak meminta ini.
    """

    send_email(
    receiver_email=data.email,
    subject="Permintaan Reset Password",
    content=email_content
    )


    return {"message": "Link reset password telah dikirim ke email Anda."}

@router.post("/reset-password")
async def reset_password(data: PasswordResetConfirm):
    email = verify_reset_password_token(data.token)
    hashed_pw = hash_password(data.new_password)

    result = await users_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed_pw}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Gagal mengganti password.")

    return {"message": "Password berhasil diperbarui. Silakan login kembali."}

@router.get("/me")
async def read_me(current_user: dict = Depends(get_verified_user)):
    return {
        "id": str(current_user["user_id"]),
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user.get("role", "user")
    }

@router.get("/users")
async def get_users(
    skip: int = 0, limit: int = 10,
    username: str = Query(None),
    email: str = Query(None),
    role: str = Query(None),
    current_user: dict = Depends(get_verified_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang boleh mengakses ini.")

    query = {}
    if username: query["username"] = username
    if email: query["email"] = email
    if role: query["role"] = role

    total = await users_collection.count_documents(query)

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

@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str, update_data: UserUpdate,
    current_user: dict = Depends(get_verified_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang dapat mengupdate user lain")

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}

    if "password" in update_dict:
        update_dict["password"] = hash_password(update_dict["password"])

    if (
        current_user["user_id"] == user_id and
        "role" in update_dict and
        update_dict["role"] != user["role"]
    ):
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

@router.patch("/update-user/{user_id}")
async def update_self(
    user_id: str, data: UserSelfUpdate,
    current_user: dict = Depends(get_verified_user)
):
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Kamu hanya dapat mengubah data dirimu sendiri.")

    update_data = {}
    if data.username: update_data["username"] = data.username
    if data.email: update_data["email"] = data.email
    if data.password: update_data["password"] = hash_password(data.password)

    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada data yang diupdate.")

    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        return {"message": "Tidak ada perubahan data."}

    return {"message": "Data user berhasil diupdate."}

@router.put("/change-password", tags=["Users"])
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_verified_user)
):
    user = await users_collection.find_one({"_id": ObjectId(current_user["user_id"])})

    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if not verify_password(password_data.old_password, user["password"]):
        raise HTTPException(status_code=400, detail="Password lama salah")

    new_hashed = hash_password(password_data.new_password)
    await users_collection.update_one(
        {"_id": ObjectId(current_user["user_id"])},
        {"$set": {"password": new_hashed}}
    )

    return {"message": "Password berhasil diubah"}

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_verified_user)):
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
