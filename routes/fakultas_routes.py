from fastapi import APIRouter, HTTPException
from models.fakultas_models import FakultasCreate, FakultasUpdate, FakultasOut
from database import fakultas_collection
from bson import ObjectId
from typing import List

router = APIRouter(tags=["Fakultas"])

# Create
@router.post("/", response_model=FakultasOut)
async def create_fakultas(data: FakultasCreate):
    result = await fakultas_collection.insert_one(data.dict())
    created_fakultas = await fakultas_collection.find_one({"_id": result.inserted_id})
    # Ubah _id (ObjectId) jadi string id untuk response model
    return FakultasOut(
        id=str(created_fakultas["_id"]),
        nama=created_fakultas["nama"]
    )

# Read All
@router.get("/", response_model=List[FakultasOut])
async def get_all_fakultas():
    fakultas_cursor = fakultas_collection.find()
    fakultas_list = []
    async for fakultas in fakultas_cursor:
        fakultas["_id"] = str(fakultas["_id"])  # ✅ Konversi ObjectId ke string
        fakultas_list.append(FakultasOut(**fakultas))
    return fakultas_list


# Read by ID
@router.get("/{id}", response_model=FakultasOut)
async def get_fakultas(id: str):
    fakultas = await fakultas_collection.find_one({"_id": ObjectId(id)})
    if not fakultas:
        raise HTTPException(status_code=404, detail="Fakultas tidak ditemukan")
    return FakultasOut(id=str(fakultas["_id"]), nama=fakultas["nama"])

# Update
@router.put("/{id}", response_model=FakultasOut)
async def update_fakultas(id: str, data: FakultasUpdate):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    result = await fakultas_collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Fakultas tidak ditemukan atau tidak ada perubahan")

    fakultas = await fakultas_collection.find_one({"_id": ObjectId(id)})

    return FakultasOut(
        id=str(fakultas["_id"]),
        nama=fakultas["nama"]
    )

# Delete
@router.delete("/{id}")
async def delete_fakultas(id: str):
    result = await fakultas_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Fakultas tidak ditemukan")
    return {"message": "Fakultas berhasil dihapus"}
