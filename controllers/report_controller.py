import os
import shutil
from datetime import datetime
from typing import List
from fastapi import UploadFile, HTTPException
from config import settings
from database import get_database
from models.report_model import ReportModel, ErrorDetail
from services.excel_processor import excel_processor
from services.cloud_storage import cloud_storage

class ReportController:
    def __init__(self):
        self.db = None

    def get_db(self):
        if self.db is None:
            self.db = get_database()
        return self.db

    async def generate_report(self, files: List[UploadFile]) -> dict:
        temp_paths = []       
        try:
            for file in files:
                temp_path = os.path.join(settings.TEMP_FOLDER, file.filename)
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                temp_paths.append(temp_path)
            result = excel_processor.process_multiple_files(temp_paths)
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result.get("error", "Error al procesar archivos"))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"resultado_final_{timestamp}.xlsx"
            output_path = os.path.join(settings.TEMP_FOLDER, output_filename)
            result["dataframe"].to_excel(output_path, index=False, engine='openpyxl')
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            firebase_url = await cloud_storage.upload_file(output_path, output_filename)
            if os.path.exists(output_path):
                os.remove(output_path)
            report_data = ReportModel(
                filename=output_filename,
                files_processed=result["processed_files"],
                files_with_errors=result["files_with_errors"],
                total_records=result["total_records"],
                status="success" if result["files_with_errors"] == 0 else "partial",
                file_size=round(file_size_mb, 2),
                file_url=firebase_url,
                download_url=firebase_url,
                processing_time=result["processing_time"],
                errors=[ErrorDetail(**error) for error in result["errors"]]
            )
            db = self.get_db()
            inserted = await db.reports.insert_one(report_data.model_dump(by_alias=True, exclude={'id'}))
            report_data.id = inserted.inserted_id
            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)            
            return {
                "success": True,
                "report_id": str(report_data.id),
                "filename": output_filename,
                "processed_files": result["processed_files"],
                "files_with_errors": result["files_with_errors"],
                "total_records": result["total_records"],
                "errors": result["errors"],
                "download_url": firebase_url,
                "processing_time": result["processing_time"],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            error_report = ReportModel(
                filename="error_report",
                files_processed=0,
                files_with_errors=len(files),
                total_records=0,
                status="error",
                file_size=0,
                processing_time=0,
                error_message=str(e)
            )
            db = self.get_db()
            await db.reports.insert_one(error_report.model_dump(by_alias=True, exclude={'id'}))
            raise HTTPException(status_code=500, detail=f"Error al procesar archivos: {str(e)}")

    async def get_reports_history(self, limit: int = 50, skip: int = 0):
        db = self.get_db()
        cursor = db.reports.find().sort("created_at", -1).skip(skip).limit(limit)
        reports = await cursor.to_list(length=limit)
        for report in reports:
            if "_id" in report:
                report["_id"] = str(report["_id"])
        total = await db.reports.count_documents({})
        return {
            "total": total,
            "reports": reports
        }

    async def get_report_by_id(self, report_id: str):
        from bson import ObjectId
        db = self.get_db()
        try:
            report = await db.reports.find_one({"_id": ObjectId(report_id)})
            if not report:
                raise HTTPException(status_code=404, detail="Reporte no encontrado")
            return report
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"ID inválido: {str(e)}")

    async def delete_report(self, report_id: str):
        from bson import ObjectId
        db = self.get_db()
        try:
            report = await db.reports.find_one({"_id": ObjectId(report_id)})
            if not report:
                raise HTTPException(status_code=404, detail="Reporte no encontrado")
            if report.get("filename"):
                try:
                    await cloud_storage.delete_file(f"reports/{report['filename']}")
                except:
                    pass

            await db.reports.delete_one({"_id": ObjectId(report_id)})
            
            return {"success": True, "message": "Reporte eliminado"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar reporte: {str(e)}")

    async def get_stats(self):
        db = self.get_db()
        total = await db.reports.count_documents({})
        success = await db.reports.count_documents({"status": "success"})
        errors = await db.reports.count_documents({"status": "error"})
        from datetime import datetime, timedelta
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = await db.reports.count_documents({
            "created_at": {"$gte": start_of_month}
        })

        return {
            "total": total,
            "success": success,
            "errors": errors,
            "this_month": this_month
        }

report_controller = ReportController()