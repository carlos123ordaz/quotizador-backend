import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body
from fastapi.responses import FileResponse
from typing import List, Dict, Any
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
    skip: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None)
):
    return await report_controller.get_reports_history(limit=limit, skip=skip, search=search, status=status)

@router.get("/stats")
async def get_report_stats():
    return await report_controller.get_stats()

@router.get("/accumulated")
async def get_accumulated_records(
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
):
    return await report_controller.get_accumulated_records(limit=limit, skip=skip, search=search)

@router.get("/accumulated/count")
async def get_accumulated_count():
    return await report_controller.get_accumulated_count()

@router.get("/accumulated/download")
async def download_accumulated():
    output_path, output_filename = await report_controller.download_accumulated()
    return FileResponse(
        path=output_path,
        filename=output_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=None,
    )

@router.post("/accumulated/from-file")
async def accumulate_from_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls', '.xlsm')):
        raise HTTPException(
            status_code=400,
            detail=f"Archivo {file.filename} no es un archivo Excel válido"
        )
    return await report_controller.accumulate_from_file(file)

@router.delete("/accumulated/clear")
async def clear_accumulated():
    return await report_controller.clear_accumulated()

@router.put("/accumulated/{record_id}")
async def update_accumulated_record(record_id: str, data: Dict[str, Any] = Body(...)):
    return await report_controller.update_accumulated_record(record_id, data)

@router.delete("/accumulated/{record_id}")
async def delete_accumulated_record(record_id: str):
    return await report_controller.delete_accumulated_record(record_id)

@router.get("/{report_id}")
async def get_report_by_id(report_id: str):
    return await report_controller.get_report_by_id(report_id)

@router.delete("/{report_id}")
async def delete_report(report_id: str):
    return await report_controller.delete_report(report_id)
