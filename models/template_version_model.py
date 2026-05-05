from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CampoPlantilla(BaseModel):
    campo_interno: str
    nombre_display: str
    hoja: str
    fila: int
    columna: int


class TemplateVersionCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    nombre: str
    descripcion: Optional[str] = None
    campos: List[CampoPlantilla] = []


class TemplateVersionUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None
    campos: Optional[List[CampoPlantilla]] = None


class TemplateVersionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    nombre: str
    descripcion: Optional[str] = None
    activo: bool
    campos: List[CampoPlantilla]
    created_by: str
    created_at: datetime
    updated_at: datetime
