from fastapi import APIRouter, HTTPException
from models.prodi_models import ProdiCreate, ProdiUpdate, ProdiOut
from database import prodi_collection
from bson import ObjectId

router = APIRouter()

@router.post("/prodi", response_model=ProdiOut, tags=["Prodi"])
async def create_prodi(prodi: ProdiCreate):
    prodi_dict = prodi.dict()
    prodi_dict["fakultas_id"] = ObjectId(prodi_dict["fakultas_id"])
    result = await prodi_collection.insert_one(prodi_dict)
    created = await prodi_collection.find_one({"_id": result.inserted_id})
    created["_id"] = str(created["_id"])
    created["fakultas_id"] = str(created["fakultas_id"])
    return ProdiOut(**created)

@router.get("/prodi", response_model=list[ProdiOut], tags=["Prodi"])
async def get_all_prodi():
    prodi_list = []
    async for doc in prodi_collection.find():
        doc["_id"] = str(doc["_id"])
        doc["fakultas_id"] = str(doc.get("fakultas_id", ""))  # fallback kosong
        if "nama_prodi" not in doc:
            continue  # skip jika nama_prodi gak ada
        prodi_list.append(ProdiOut(**doc))
    return prodi_list

@router.get("/prodi/{prodi_id}", response_model=ProdiOut, tags=["Prodi"])
async def get_prodi(prodi_id: str):
    if not ObjectId.is_valid(prodi_id):
        raise HTTPException(status_code=400, detail="Invalid prodi_id")
    doc = await prodi_collection.find_one({"_id": ObjectId(prodi_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Prodi not found")
    doc["_id"] = str(doc["_id"])
    doc["fakultas_id"] = str(doc["fakultas_id"])
    return ProdiOut(**doc)

@router.put("/prodi/{prodi_id}", tags=["Prodi"])
async def update_prodi(prodi_id: str, data: ProdiUpdate):
    if not ObjectId.is_valid(prodi_id):
        raise HTTPException(status_code=400, detail="Invalid prodi_id")
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    if "fakultas_id" in update_data:
        if not ObjectId.is_valid(update_data["fakultas_id"]):
            raise HTTPException(status_code=400, detail="Invalid fakultas_id")
        update_data["fakultas_id"] = ObjectId(update_data["fakultas_id"])
    result = await prodi_collection.update_one({"_id": ObjectId(prodi_id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Prodi not found or no changes made")
    return {"message": "Prodi updated successfully"}

@router.delete("/prodi/{prodi_id}", tags=["Prodi"])
async def delete_prodi(prodi_id: str):
    if not ObjectId.is_valid(prodi_id):
        raise HTTPException(status_code=400, detail="Invalid prodi_id")
    result = await prodi_collection.delete_one({"_id": ObjectId(prodi_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prodi not found")
    return {"message": "Prodi deleted successfully"}
