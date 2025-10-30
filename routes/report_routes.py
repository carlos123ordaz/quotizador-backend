from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import List
from controllers.report_controller import report_controller

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.post("/generate")
async def generate_report(files: List[UploadFile] = File(...)):
    for file in files:
        if not file.filename.endswith(('.xlsx', '.xls', '.xlsm')):
            raise HTTPException(
                status_code=400,
                detail=f"Archivo {file.filename} no es un archivo Excel válido"
            )
    return await report_controller.generate_report(files)

@router.get("/history")
async def get_reports_history(
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0)
):
    return await report_controller.get_reports_history(limit=limit, skip=skip)

@router.get("/stats")
async def get_report_stats():
    return await report_controller.get_stats()

@router.get("/{report_id}")
async def get_report_by_id(report_id: str):
    return await report_controller.get_report_by_id(report_id)

@router.delete("/{report_id}")
async def delete_report(report_id: str):
    return await report_controller.delete_report(report_id)