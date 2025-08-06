from pydantic import BaseModel, Field
from typing import Optional

class FakultasBase(BaseModel):
    nama: str = Field(..., example="Fakultas Teknik")

class FakultasCreate(FakultasBase):
    pass

class FakultasUpdate(BaseModel):
    nama: Optional[str] = Field(None, example="Fakultas Kedokteran")

class FakultasOut(FakultasBase):
    id: str