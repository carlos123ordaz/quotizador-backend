# routes/processed_excel_routes.py

from typing import Optional
from fastapi import APIRouter, Query, Body, Path, HTTPException
from fastapi.responses import StreamingResponse
from controllers.processed_excel_controller import processed_excel_controller
from models.processed_products_model import ProcessedExcelModel, ProcessedExcelResponse
from datetime import datetime

router = APIRouter(prefix="/api/processed-excels", tags=["Processed Excels"])

@router.post("", response_model=ProcessedExcelResponse, status_code=201)
async def save_processed_excel(data: ProcessedExcelModel = Body(...)):
    return await processed_excel_controller.save_processed_excel(data)

@router.get("/history/{history_id}", response_model=ProcessedExcelResponse)
async def get_by_history_id(history_id: str = Path(...)):
    result = await processed_excel_controller.get_by_history_id(history_id)
    if not result:
        raise HTTPException(status_code=404, detail="Excel procesado no encontrado")
    return result

@router.get("/export/stats")
async def get_export_stats(
    fecha_inicio: Optional[str] = Query(None, description="Formato: YYYY-MM-DD"),
    fecha_fin: Optional[str] = Query(None, description="Formato: YYYY-MM-DD")
):
    return await processed_excel_controller.get_export_stats(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

@router.get("/export")
async def export_to_excel(
    fecha_inicio: Optional[str] = Query(None, description="Formato: YYYY-MM-DD"),
    fecha_fin: Optional[str] = Query(None, description="Formato: YYYY-MM-DD"),
    num_deal: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    departamento: Optional[str] = Query(None)
):
    output = await processed_excel_controller.export_to_excel(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        num_deal=num_deal,
        cliente=cliente,
        departamento=departamento
    )
    
    filename = f"consolidado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )