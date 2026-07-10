import os
import shutil
import logging
import traceback
from datetime import datetime
from typing import List
import pandas as pd
from fastapi import UploadFile, HTTPException
from config import settings
from database import get_database
from models.report_model import ReportModel, ErrorDetail
from services.excel_processor import excel_processor
from services.cloud_storage import cloud_storage

logger = logging.getLogger(__name__)

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

            db = self.get_db()

            # Crear el reporte primero para obtener su ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"resultado_final_{timestamp}.xlsx"

            report_data = ReportModel(
                filename=output_filename,
                files_processed=result["processed_files"],
                files_with_errors=result["files_with_errors"],
                total_records=0,
                status="success" if result["files_with_errors"] == 0 else "partial",
                file_size=0,
                processing_time=result["processing_time"],
                errors=[ErrorDetail(**error) for error in result["errors"]]
            )
            inserted = await db.reports.insert_one(report_data.model_dump(by_alias=True, exclude={'id'}))
            report_id = inserted.inserted_id

            # Guardar los nuevos registros en la colección de acumulados con referencia al reporte
            new_records = result["dataframe"].to_dict(orient="records")
            if new_records:
                for record in new_records:
                    record["_accumulated_at"] = datetime.utcnow()
                    record["_report_id"] = report_id
                await db.accumulated_records.insert_many(new_records)

            # Obtener TODOS los registros acumulados para generar el Excel
            all_accumulated = await db.accumulated_records.find(
                {}, {"_id": 0, "_accumulated_at": 0, "_report_id": 0}
            ).to_list(length=None)

            df_accumulated = pd.DataFrame(all_accumulated) if all_accumulated else result["dataframe"]
            total_accumulated_records = len(df_accumulated)

            output_path = os.path.join(settings.TEMP_FOLDER, output_filename)
            df_accumulated.to_excel(output_path, index=False, engine='openpyxl')
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            firebase_url = await cloud_storage.upload_file(output_path, output_filename)
            if os.path.exists(output_path):
                os.remove(output_path)

            # Actualizar el reporte con los datos finales
            await db.reports.update_one(
                {"_id": report_id},
                {"$set": {
                    "total_records": total_accumulated_records,
                    "file_size": round(file_size_mb, 2),
                    "file_url": firebase_url,
                    "download_url": firebase_url,
                }}
            )
            report_data.id = report_id
            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            return {
                "success": True,
                "report_id": str(report_data.id),
                "filename": output_filename,
                "processed_files": result["processed_files"],
                "files_with_errors": result["files_with_errors"],
                "total_records": total_accumulated_records,
                "new_records": result["total_records"],
                "errors": result["errors"],
                "download_url": firebase_url,
                "processing_time": result["processing_time"],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error en generate_report: {str(e)}")
            logger.error(traceback.format_exc())
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

    async def get_reports_history(self, limit: int = 50, skip: int = 0, search: str | None = None, status: str | None = None):
        from bson import ObjectId
        db = self.get_db()
        query = {}

        if status and status != "all":
            query["status"] = status

        if search:
            search = search.strip()
            search_filters = [{"filename": {"$regex": search, "$options": "i"}}]

            if ObjectId.is_valid(search):
                search_filters.append({"_id": ObjectId(search)})

            query["$or"] = search_filters

        cursor = db.reports.find(query).sort("created_at", -1).skip(skip).limit(limit)
        reports = await cursor.to_list(length=limit)
        for report in reports:
            if "_id" in report:
                report["_id"] = str(report["_id"])
        total = await db.reports.count_documents(query)
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
            oid = ObjectId(report_id)
            report = await db.reports.find_one({"_id": oid})
            if not report:
                raise HTTPException(status_code=404, detail="Reporte no encontrado")
            if report.get("filename"):
                try:
                    await cloud_storage.delete_file(f"reports/{report['filename']}")
                except:
                    pass

            # Eliminar registros acumulados asociados a este reporte
            accumulated_result = await db.accumulated_records.delete_many({"_report_id": oid})

            await db.reports.delete_one({"_id": oid})

            return {
                "success": True,
                "message": "Reporte eliminado",
                "accumulated_deleted": accumulated_result.deleted_count
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar reporte: {str(e)}")

    async def get_stats(self):
        db = self.get_db()
        total = await db.reports.count_documents({})
        success = await db.reports.count_documents({"status": "success"})
        partial = await db.reports.count_documents({"status": "partial"})
        errors = await db.reports.count_documents({"status": "error"})
        from datetime import datetime, timedelta
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = await db.reports.count_documents({
            "created_at": {"$gte": start_of_month}
        })

        return {
            "total": total,
            "success": success,
            "partial": partial,
            "errors": errors,
            "this_month": this_month
        }

    async def get_accumulated_count(self):
        db = self.get_db()
        count = await db.accumulated_records.count_documents({})
        return {"accumulated_records": count}

    async def get_accumulated_records(self, limit: int = 50, skip: int = 0, search: str | None = None):
        db = self.get_db()
        query = {}
        if search:
            search = search.strip()
            query["$or"] = [
                {"Cliente": {"$regex": search, "$options": "i"}},
                {"Num. Deal": {"$regex": search, "$options": "i"}},
                {"Num. Oferta": {"$regex": search, "$options": "i"}},
                {"Marca": {"$regex": search, "$options": "i"}},
                {"Código Completo": {"$regex": search, "$options": "i"}},
                {"Familia": {"$regex": search, "$options": "i"}},
                {"Departamento": {"$regex": search, "$options": "i"}},
            ]

        cursor = db.accumulated_records.find(
            query, {"_accumulated_at": 0, "_report_id": 0}
        ).sort("_id", -1).skip(skip).limit(limit)

        records = await cursor.to_list(length=limit)
        for record in records:
            if "_id" in record:
                record["_id"] = str(record["_id"])
        total = await db.accumulated_records.count_documents(query)
        return {"total": total, "records": records}

    async def download_accumulated(self):
        db = self.get_db()
        all_records = await db.accumulated_records.find(
            {}, {"_id": 0, "_accumulated_at": 0, "_report_id": 0}
        ).to_list(length=None)

        if not all_records:
            raise HTTPException(status_code=404, detail="No hay registros acumulados para exportar")

        df = pd.DataFrame(all_records)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"reporte_acumulado_{timestamp}.xlsx"
        output_path = os.path.join(settings.TEMP_FOLDER, output_filename)
        df.to_excel(output_path, index=False, engine='openpyxl')
        return output_path, output_filename

    async def update_accumulated_record(self, record_id: str, data: dict):
        from bson import ObjectId
        db = self.get_db()
        oid = ObjectId(record_id)
        existing = await db.accumulated_records.find_one({"_id": oid})
        if not existing:
            raise HTTPException(status_code=404, detail="Registro no encontrado")

        # Excluir campos internos del update
        update_data = {k: v for k, v in data.items() if not k.startswith("_")}
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        await db.accumulated_records.update_one({"_id": oid}, {"$set": update_data})
        updated = await db.accumulated_records.find_one(
            {"_id": oid}, {"_accumulated_at": 0, "_report_id": 0}
        )
        updated["_id"] = str(updated["_id"])
        return updated

    async def delete_accumulated_record(self, record_id: str):
        from bson import ObjectId
        db = self.get_db()
        oid = ObjectId(record_id)
        result = await db.accumulated_records.delete_one({"_id": oid})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        return {"success": True, "message": "Registro eliminado"}

    async def clear_accumulated(self):
        db = self.get_db()
        result = await db.accumulated_records.delete_many({})
        return {
            "success": True,
            "deleted_count": result.deleted_count,
            "message": "Datos acumulados eliminados correctamente"
        }

report_controller = ReportController()
