# models/history_model.py

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class HistoryModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    num_deal: str
    nombre_oferta: str
    rubrica: Optional[str] = None
    preparado: str
    preparado_unva: Optional[str] = None
    preparado_unai: Optional[str] = None
    responsable: str
    visto_bueno: Optional[str] = None
    usuario_envio: str
    usuario_envio_id: Optional[str] = None
    utilidad: float
    costo_auma: float = 0
    costo_msa: float = 0
    costo_valmet: float = 0
    total_productos: int
    tipo_operacion: str  
    quote_id: Optional[str] = None
    fecha_correo: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_envio: Optional[str] = None
    fecha_cierre: Optional[str] = None
    fecha_cierre_modificada: bool = False
    nombre_archivo: str
    estado: str = "exitoso"
    error_mensaje: Optional[str] = None
    totales_por_area: Optional[Dict[str, float]] = None

class HistoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    num_deal: str
    nombre_oferta: str
    rubrica: Optional[str] = None
    preparado: str
    preparado_unva: Optional[str] = None
    preparado_unai: Optional[str] = None
    responsable: str
    visto_bueno: Optional[str] = None
    usuario_envio: str
    usuario_envio_id: Optional[str] = None
    utilidad: float
    costo_auma: float
    costo_msa: float
    costo_valmet: float
    total_productos: int
    tipo_operacion: str
    quote_id: Optional[str] = None
    fecha_correo: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_envio: Optional[str] = None
    fecha_cierre: Optional[str] = None
    fecha_cierre_modificada: bool
    nombre_archivo: str
    estado: str
    error_mensaje: Optional[str] = None
    created_at: datetime
    totales_por_area: Optional[Dict[str, float]] = None