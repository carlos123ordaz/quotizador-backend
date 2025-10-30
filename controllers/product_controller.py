from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException
from database import get_database
from models.product_model import ProductModel, ProductUpdate, ProductResponse

class ProductController:
    def __init__(self):
        self.db = None
        self.collection_name = "productos"

    def get_collection(self):
        if self.db is None:
            self.db = get_database()
        return self.db[self.collection_name]

    async def get_all_products(
        self,
        skip: int = 0,
        limit: int = 300,
        search: Optional[str] = None
    ) -> dict:
        collection = self.get_collection()
        query = {}
        
        if search:
            query["$or"] = [
                {"code": {"$regex": search, "$options": "i"}},
                {"name_excel": {"$regex": search, "$options": "i"}},
                {"name_bitrix": {"$regex": search, "$options": "i"}},
                {"unidad_negocio": {"$regex": search, "$options": "i"}},
            ]
        
        total = await collection.count_documents(query)
        productos = []
        
        cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            productos.append(doc)
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "productos": productos
        }

    async def get_product_by_id(self, id: str) -> ProductResponse:
        collection = self.get_collection()    
        try:
            producto = await collection.find_one({"_id": ObjectId(id)})
        except Exception:
            raise HTTPException(status_code=400, detail="ID de producto inválido")

        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        producto["_id"] = str(producto["_id"])
        return ProductResponse(**producto)

    async def get_product_by_code(self, code: str) -> Optional[ProductResponse]:
        collection = self.get_collection() 
        producto = await collection.find_one({"code": code})
        if not producto:
            return None
        producto["_id"] = str(producto["_id"])
        return ProductResponse(**producto)

    async def create_product(self, data: ProductModel) -> ProductResponse:
        collection = self.get_collection()

        # Verificar si ya existe un producto con ese código
        existing = await collection.find_one({"code": data.code})
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un producto con el código {data.code}"
            )

        # Preparar datos para inserción
        product_dict = data.model_dump()  # Sin by_alias ni exclude
        product_dict["created_at"] = datetime.utcnow()
        product_dict["updated_at"] = datetime.utcnow()

        # Insertar en la base de datos
        result = await collection.insert_one(product_dict)

        # Recuperar el documento creado
        created = await collection.find_one({"_id": result.inserted_id})
        created["_id"] = str(created["_id"])
        return ProductResponse(**created)

    async def update_product(self, id: str, data: ProductUpdate) -> ProductResponse:
        collection = self.get_collection()
        
        try:
            object_id = ObjectId(id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID de producto inválido")

        # Verificar que el producto existe
        existing = await collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        # Preparar datos de actualización
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        
        # Si se está actualizando el código, verificar que no exista
        if "code" in update_data and update_data["code"] != existing.get("code"):
            code_exists = await collection.find_one({
                "code": update_data["code"],
                "_id": {"$ne": object_id}
            })
            if code_exists:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe otro producto con el código {update_data['code']}"
                )
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Actualizar
        result = await collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        # Recuperar documento actualizado
        updated = await collection.find_one({"_id": object_id})
        updated["_id"] = str(updated["_id"])

        return ProductResponse(**updated)

    async def delete_product(self, id: str) -> dict:
        collection = self.get_collection()
        
        try:
            object_id = ObjectId(id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID de producto inválido")

        existing = await collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        result = await collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        return {
            "success": True,
            "message": "Producto eliminado exitosamente",
            "deleted_id": id
        }


product_controller = ProductController()