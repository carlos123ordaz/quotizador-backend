# routes/excel_routes.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from services.excel_processor import excel_processor
import os
import shutil
from config import settings

router = APIRouter(prefix="/api/process-excel-for-db", tags=["Excel Processing"])

@router.post("")
async def process_excel_for_db(file: UploadFile = File(...)):
    temp_path = None
    try:
        temp_path = os.path.join(settings.TEMP_FOLDER, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        result = excel_processor.process_file_for_db(temp_path)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Error al procesar archivo"))
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar archivo: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)