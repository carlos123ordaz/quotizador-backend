# controllers/history_controller.py

from datetime import datetime
from typing import Optional
from bson import ObjectId
from fastapi import HTTPException
from database import get_database
from models.history_model import HistoryModel, HistoryResponse

class HistoryController:
    def __init__(self):
        self.db = None
        self.collection_name = "historial"
    def get_collection(self):
        if self.db is None:
            self.db = get_database()
        return self.db[self.collection_name]

    async def create_history_entry(self, data: HistoryModel) -> HistoryResponse:
        collection = self.get_collection()
        history_dict = data.model_dump(exclude_unset=True)
        history_dict["created_at"] = datetime.utcnow()
        result = await collection.insert_one(history_dict)
        created = await collection.find_one({"_id": result.inserted_id})
        created["_id"] = str(created["_id"])
        return HistoryResponse(**created)

    async def get_all_history(
        self,
        skip: int = 0,
        limit: int = 50,
        num_deal: Optional[str] = None,
        usuario_envio: Optional[str] = None,
        tipo_operacion: Optional[str] = None,
        estado: Optional[str] = None,
        search: Optional[str] = None
    ) -> dict:
        """Obtener historial con filtros"""
        collection = self.get_collection()
        query = {}
        
        if num_deal:
            query["num_deal"] = num_deal
        
        if usuario_envio:
            query["usuario_envio"] = {"$regex": usuario_envio, "$options": "i"}
        
        if tipo_operacion:
            query["tipo_operacion"] = tipo_operacion
        
        if estado:
            query["estado"] = estado
        
        if search:
            query["$or"] = [
                {"num_deal": {"$regex": search, "$options": "i"}},
                {"nombre_oferta": {"$regex": search, "$options": "i"}},
                {"usuario_envio": {"$regex": search, "$options": "i"}},
                {"nombre_archivo": {"$regex": search, "$options": "i"}},
            ]
        
        total = await collection.count_documents(query)
        
        historial = []
        cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            historial.append(doc)
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "historial": historial
        }

    async def get_history_by_id(self, id: str) -> HistoryResponse:
        collection = self.get_collection() 
        try:
            history = await collection.find_one({"_id": ObjectId(id)})
        except Exception:
            raise HTTPException(status_code=400, detail="ID de historial inválido")

        if not history:
            raise HTTPException(status_code=404, detail="Entrada de historial no encontrada")

        history["_id"] = str(history["_id"])
        return HistoryResponse(**history)

    async def get_history_by_deal(self, num_deal: str) -> list:
        collection = self.get_collection() 
        historial = []
        cursor = collection.find({"num_deal": num_deal}).sort("created_at", -1)
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            historial.append(doc)
        
        return historial

    async def get_statistics(self) -> dict:
        collection = self.get_collection()
        total = await collection.count_documents({})
        exitosos = await collection.count_documents({"estado": "exitoso"})
        errores = await collection.count_documents({"estado": "error"})
        creaciones = await collection.count_documents({"tipo_operacion": "crear"})
        actualizaciones = await collection.count_documents({"tipo_operacion": "actualizar"})

        return {
            "total_envios": total,
            "exitosos": exitosos,
            "errores": errores,
            "creaciones": creaciones,
            "actualizaciones": actualizaciones
        }

    async def get_dashboard(self, year: Optional[int] = None) -> dict:
        from datetime import timedelta
        collection = self.get_collection()

        # Filtro de fecha
        match = {}
        if year:
            match["created_at"] = {
                "$gte": datetime(year, 1, 1),
                "$lt": datetime(year + 1, 1, 1),
            }

        successful_match = {**match, "estado": "exitoso"}

        # Años disponibles (sin filtro, siempre todos)
        years_cursor = collection.aggregate([
            {"$group": {"_id": {"$year": "$created_at"}}},
            {"$sort": {"_id": -1}},
        ])
        available_years = [doc["_id"] async for doc in years_cursor if doc["_id"]]

        # Stats
        total = await collection.count_documents(match)
        exitosos = await collection.count_documents(successful_match)
        errores = await collection.count_documents({**match, "estado": "error"})
        creaciones = await collection.count_documents({**successful_match, "tipo_operacion": "crear"})
        actualizaciones = await collection.count_documents({**successful_match, "tipo_operacion": "actualizar"})
        stats = {
            "total_envios": total,
            "exitosos": exitosos,
            "errores": errores,
            "creaciones": creaciones,
            "actualizaciones": actualizaciones,
        }

        # Actividad: últimos 7 días (sin año) o mensual (con año)
        DAYS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        MONTHS_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

        if year:
            agg_cursor = collection.aggregate([
                {"$match": successful_match},
                {"$group": {"_id": {"$month": "$created_at"}, "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ])
            month_map = {doc["_id"]: doc["count"] async for doc in agg_cursor}
            activity = [
                {"label": MONTHS_ES[m - 1], "count": month_map.get(m, 0)}
                for m in range(1, 13)
            ]
        else:
            since = datetime.utcnow() - timedelta(days=6)
            since = since.replace(hour=0, minute=0, second=0, microsecond=0)
            agg_cursor = collection.aggregate([
                {"$match": {**successful_match, "created_at": {"$gte": since}}},
                {"$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "count": {"$sum": 1},
                }},
            ])
            day_map = {doc["_id"]: doc["count"] async for doc in agg_cursor}
            activity = []
            for i in range(6, -1, -1):
                d = datetime.utcnow() - timedelta(days=i)
                date_str = d.strftime("%Y-%m-%d")
                activity.append({"label": DAYS_ES[d.weekday()], "count": day_map.get(date_str, 0)})

        # Top usuarios
        top_users_cursor = collection.aggregate([
            {"$match": {**successful_match, "usuario_envio": {"$exists": True, "$nin": [None, ""]}}},
            {"$group": {"_id": "$usuario_envio", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 6},
            {"$project": {"_id": 0, "name": "$_id", "count": 1}},
        ])
        top_users = [doc async for doc in top_users_cursor]

        # Totales por área
        area_cursor = collection.aggregate([
            {"$match": {**successful_match, "totales_por_area": {"$exists": True, "$ne": None}}},
            {"$project": {"areas": {"$objectToArray": "$totales_por_area"}}},
            {"$unwind": "$areas"},
            {"$match": {"areas.v": {"$gt": 0}}},
            {"$group": {"_id": "$areas.k", "total": {"$sum": "$areas.v"}}},
            {"$sort": {"total": -1}},
            {"$project": {"_id": 0, "area": "$_id", "total": 1}},
        ])
        totales_por_area = [doc async for doc in area_cursor]

        return {
            "stats": stats,
            "activity": activity,
            "top_users": top_users,
            "totales_por_area": totales_por_area,
            "available_years": available_years,
        }

    async def delete_history_entry(self, id: str) -> dict:
        collection = self.get_collection()
        
        try:
            object_id = ObjectId(id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID de historial inválido")

        existing = await collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Entrada de historial no encontrada")
        
        result = await collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Entrada de historial no encontrada")
        
        return {
            "success": True,
            "message": "Entrada de historial eliminada exitosamente",
            "deleted_id": id
        }


history_controller = HistoryController()
