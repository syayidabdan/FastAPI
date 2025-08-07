from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            python_schema=core_schema.no_info_after_validator_function(
                cls.validate,
                core_schema.str_schema()
            ),
            json_schema=core_schema.str_schema(),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class FakultasBase(BaseModel):
    nama: str = Field(..., example="Fakultas Teknik")

class FakultasCreate(FakultasBase):
    pass

class FakultasUpdate(BaseModel):
    nama: Optional[str] = Field(None, example="Fakultas Kedokteran")

class FakultasOut(FakultasBase):
    id: PyObjectId = Field(..., alias="_id")

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "arbitrary_types_allowed": True,
    }
