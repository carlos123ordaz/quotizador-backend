from typing import Optional
from fastapi import APIRouter, Query, Body, Path
from controllers.history_controller import history_controller
from models.history_model import HistoryModel, HistoryResponse
router = APIRouter(prefix="/api/history", tags=["History"])
@router.get("", response_model=dict)  
async def get_all_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    num_deal: Optional[str] = Query(default=None),
    usuario_envio: Optional[str] = Query(default=None),
    tipo_operacion: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None)
):
    """Obtener todo el historial con filtros opcionales"""
    return await history_controller.get_all_history(
        skip=skip,
        limit=limit,
        num_deal=num_deal,
        usuario_envio=usuario_envio,
        tipo_operacion=tipo_operacion,
        estado=estado,
        search=search
    )

@router.get("/statistics", response_model=dict)
async def get_statistics():
    return await history_controller.get_statistics()

@router.get("/deal/{num_deal}", response_model=list)
async def get_history_by_deal(num_deal: str = Path(...)):
    return await history_controller.get_history_by_deal(num_deal)

@router.get("/{history_id}", response_model=HistoryResponse)
async def get_history_by_id(history_id: str = Path(...)):
    return await history_controller.get_history_by_id(history_id)

@router.post("", response_model=HistoryResponse, status_code=201)  # SIN barra
async def create_history_entry(history: HistoryModel = Body(...)):
    return await history_controller.create_history_entry(history)

@router.delete("/{history_id}", response_model=dict)
async def delete_history_entry(history_id: str = Path(...)):
    return await history_controller.delete_history_entry(history_id)