# models/processed_products_model.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class ProductoDetalle(BaseModel):
    num_item: Optional[str] = None
    marca: Optional[str] = None
    codigo_completo: Optional[str] = None
    familia: Optional[str] = None
    departamento: Optional[str] = None
    cantidad: Optional[float] = None
    descuento_stf: Optional[float] = None
    descuento_cisac: Optional[float] = None
    margen: Optional[float] = None
    fact_importacion: Optional[float] = None
    costo_importacion: Optional[float] = None
    total_c_fijos: Optional[float] = None
    total_c_extras: Optional[float] = None
    dias_fabricacion: Optional[int] = None
    peso_unva: Optional[float] = None
    tiempo_unva: Optional[float] = None
    moneda: Optional[str] = None
    precio_compra: Optional[float] = None
    precio_compra_2: Optional[float] = None
    precio_venta: Optional[float] = None
    total: Optional[float] = None

class ProcessedExcelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    history_id: str  
    num_deal: str
    num_oferta: str
    revision: str
    cliente: str
    nombre_archivo: str
    productos: List[ProductoDetalle]
    total_productos: int
    resumen_estadistico: Optional[dict] = None 
    created_at: Optional[datetime] = None

class ProcessedExcelResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(alias="_id")
    history_id: str
    num_deal: str
    num_oferta: str
    revision: str
    cliente: str
    nombre_archivo: str
    productos: List[ProductoDetalle]
    total_productos: int
    resumen_estadistico: Optional[dict] = None
    created_at: datetime