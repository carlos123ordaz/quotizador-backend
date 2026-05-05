from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from database import get_database
from models.template_version_model import TemplateVersionCreate, TemplateVersionUpdate


class TemplateVersionController:
    def __init__(self):
        self.db = None
        self.collection_name = "template_versions"
        self.usuarios_collection = "usuarios"

    def get_collection(self):
        if self.db is None:
            self.db = get_database()
        return self.db[self.collection_name]

    def get_usuarios_collection(self):
        if self.db is None:
            self.db = get_database()
        return self.db[self.usuarios_collection]

    async def verify_lider(self, usuario_id: str):
        try:
            oid = ObjectId(usuario_id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID de usuario inválido")

        collection = self.get_usuarios_collection()
        user = await collection.find_one({"_id": oid})

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if not user.get("es_lider", False):
            raise HTTPException(status_code=403, detail="Solo los usuarios líderes pueden realizar esta acción")

    async def get_all(self) -> dict:
        collection = self.get_collection()
        versions = []
        cursor = collection.find({}).sort("created_at", -1)
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            versions.append(doc)
        return {"total": len(versions), "versiones": versions}

    async def get_by_id(self, version_id: str) -> dict:
        collection = self.get_collection()
        try:
            doc = await collection.find_one({"_id": ObjectId(version_id)})
        except Exception:
            raise HTTPException(status_code=400, detail="ID inválido")
        if not doc:
            raise HTTPException(status_code=404, detail="Versión no encontrada")
        doc["_id"] = str(doc["_id"])
        return doc

    async def create(self, data: TemplateVersionCreate, usuario_id: str) -> dict:
        await self.verify_lider(usuario_id)
        collection = self.get_collection()

        existing = await collection.find_one({"nombre": data.nombre})
        if existing:
            raise HTTPException(status_code=400, detail=f"Ya existe una versión con el nombre '{data.nombre}'")

        doc = data.model_dump()
        doc["activo"] = True
        doc["created_by"] = usuario_id
        doc["created_at"] = datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()

        result = await collection.insert_one(doc)
        created = await collection.find_one({"_id": result.inserted_id})
        created["_id"] = str(created["_id"])
        return created

    async def update(self, version_id: str, data: TemplateVersionUpdate, usuario_id: str) -> dict:
        await self.verify_lider(usuario_id)
        collection = self.get_collection()

        try:
            object_id = ObjectId(version_id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID inválido")

        existing = await collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Versión no encontrada")

        update_data = data.model_dump(exclude_unset=True, exclude_none=True)

        if "nombre" in update_data and update_data["nombre"] != existing.get("nombre"):
            name_exists = await collection.find_one({
                "nombre": update_data["nombre"],
                "_id": {"$ne": object_id}
            })
            if name_exists:
                raise HTTPException(status_code=400, detail=f"Ya existe una versión con el nombre '{update_data['nombre']}'")

        update_data["updated_at"] = datetime.utcnow()
        await collection.update_one({"_id": object_id}, {"$set": update_data})

        updated = await collection.find_one({"_id": object_id})
        updated["_id"] = str(updated["_id"])
        return updated

    async def delete(self, version_id: str, usuario_id: str) -> dict:
        await self.verify_lider(usuario_id)
        collection = self.get_collection()

        try:
            object_id = ObjectId(version_id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID inválido")

        existing = await collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Versión no encontrada")

        await collection.delete_one({"_id": object_id})
        return {"success": True, "message": "Versión eliminada", "deleted_id": version_id}


template_version_controller = TemplateVersionController()
