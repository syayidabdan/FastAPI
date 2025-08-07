from pydantic import BaseModel, Field, validator
from typing import Optional
from bson import ObjectId

class ProdiBase(BaseModel):
    nama_prodi: str
    fakultas_id: str

    @validator("fakultas_id")
    def fakultas_id_must_be_valid_objectid(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("fakultas_id must be a valid ObjectId string")
        return v

class ProdiCreate(ProdiBase):
    pass

class ProdiUpdate(BaseModel):
    nama_prodi: Optional[str]
    fakultas_id: Optional[str]

    @validator("fakultas_id")
    def fakultas_id_must_be_valid_objectid(cls, v):
        if v is not None and not ObjectId.is_valid(v):
            raise ValueError("fakultas_id must be a valid ObjectId string")
        return v

class ProdiOut(BaseModel):
    id: str = Field(..., alias="_id")
    nama_prodi: str
    fakultas_id: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        extra = "ignore"