# models/product_model.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ProductModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    code: str
    name_excel: str
    name_bitrix: Optional[str] = None
    unidad_negocio: str
    area1: Optional[str] = None
    area2: Optional[str] = None
    activo: bool = True

class ProductUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    code: Optional[str] = None
    name_excel: Optional[str] = None
    name_bitrix: Optional[str] = None
    unidad_negocio: Optional[str] = None
    area1: Optional[str] = None
    area2: Optional[str] = None
    activo: Optional[bool] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(alias="_id")
    code: str
    name_excel: str
    name_bitrix: Optional[str] = None
    unidad_negocio: str
    area1: Optional[str] = None
    area2: Optional[str] = None
    activo: bool = True
    created_at: datetime
    updated_at: datetime