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