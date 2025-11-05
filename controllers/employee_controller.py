from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING
from fastapi import HTTPException, status

from models.employee_model import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)

class EmployeeController:
    def __init__(self):
        self.db = None
        self.collection = None

    def get_db(self):
        if self.db is None:
            from database import get_database
            self.db = get_database()
        return self.db

    def get_collection(self):
        if self.collection is None:
            db = self.get_db()
            self.collection = db["employees"]
            self.collection.create_index("codigo", unique=True)
            self.collection.create_index([("nombre", "text"), ("codigo", "text")])
        return self.collection

    async def create_employee(self, employee_data: EmployeeCreate) -> EmployeeResponse:
        try:
            collection = self.get_collection()

            existing = await self.get_employee_by_codigo(employee_data.codigo)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe un empleado con el código {employee_data.codigo}"
                )

            employee_dict = employee_data.model_dump()
            employee_dict["created_at"] = datetime.utcnow()
            employee_dict["updated_at"] = datetime.utcnow()

            result = await collection.insert_one(employee_dict)
            
            created_employee = await collection.find_one({"_id": result.inserted_id})
            return self._format_employee(created_employee)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear empleado: {str(e)}"
            )

    async def get_all_employees(
        self,
        skip: int = 0,
        limit: int = 100,
        activo: Optional[bool] = None,
        search: Optional[str] = None
    ) -> dict:
        try:
            collection = self.get_collection()
            query = {}
            if activo is not None:
                query["activo"] = activo
            if search:
                query["$or"] = [
                    {"nombre": {"$regex": search, "$options": "i"}},
                    {"codigo": {"$regex": search, "$options": "i"}}
                ]
            total = await collection.count_documents(query)
            cursor = collection.find(query).sort("nombre", ASCENDING).skip(skip).limit(limit)
            employees = await cursor.to_list(length=limit)
            employees_formatted = [self._format_employee(emp) for emp in employees]
            print(f'1: {employees_formatted}')
            return {
                "empleados": employees_formatted,
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener empleados: {str(e)}"
            )

    async def get_employee_by_id(self, employee_id: str) -> Optional[EmployeeResponse]:
        try:
            if not ObjectId.is_valid(employee_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ID de empleado inválido"
                )

            collection = self.get_collection()
            employee = await collection.find_one({"_id": ObjectId(employee_id)})
            
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Empleado con ID {employee_id} no encontrado"
                )
                
            return self._format_employee(employee)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener empleado: {str(e)}"
            )

    async def get_employee_by_codigo(self, codigo: str) -> Optional[EmployeeResponse]:
        try:
            collection = self.get_collection()
            employee = await collection.find_one({"codigo": codigo})
            
            if employee:
                return self._format_employee(employee)
            return None
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al buscar empleado: {str(e)}"
            )

    async def update_employee(
        self,
        employee_id: str,
        employee_data: EmployeeUpdate
    ) -> Optional[EmployeeResponse]:
        try:
            if not ObjectId.is_valid(employee_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ID de empleado inválido"
                )

            collection = self.get_collection()
            existing = await collection.find_one({"_id": ObjectId(employee_id)})
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Empleado con ID {employee_id} no encontrado"
                )
            if employee_data.codigo and employee_data.codigo != existing.get("codigo"):
                codigo_exists = await self.get_employee_by_codigo(employee_data.codigo)
                if codigo_exists:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ya existe un empleado con el código {employee_data.codigo}"
                    )
            update_data = {
                k: v for k, v in employee_data.model_dump(exclude_unset=True).items()
            }
            
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se proporcionaron datos para actualizar"
                )
                
            update_data["updated_at"] = datetime.utcnow()
            await collection.update_one(
                {"_id": ObjectId(employee_id)},
                {"$set": update_data}
            )
            updated_employee = await collection.find_one({"_id": ObjectId(employee_id)})
            return self._format_employee(updated_employee)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar empleado: {str(e)}"
            )

    async def delete_employee(self, employee_id: str) -> dict:
        try:
            if not ObjectId.is_valid(employee_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ID de empleado inválido"
                )

            collection = self.get_collection()
            employee = await collection.find_one({"_id": ObjectId(employee_id)})
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Empleado con ID {employee_id} no encontrado"
                )
            result = await collection.delete_one({"_id": ObjectId(employee_id)})
            
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No se pudo eliminar el empleado"
                )

            return {
                "success": True,
                "message": "Empleado eliminado correctamente"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al eliminar empleado: {str(e)}"
            )

    async def get_stats(self) -> dict:
        try:
            collection = self.get_collection()
            total = await collection.count_documents({})
            activos = await collection.count_documents({"activo": True})
            inactivos = await collection.count_documents({"activo": False})
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            this_month = await collection.count_documents({
                "created_at": {"$gte": start_of_month}
            })

            return {
                "total": total,
                "activos": activos,
                "inactivos": inactivos,
                "este_mes": this_month
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener estadísticas: {str(e)}"
            )

    def _format_employee(self, employee: dict) -> EmployeeResponse:
        if employee:
            employee["_id"] = str(employee["_id"])
            return EmployeeResponse(**employee)
        return None


employee_controller = EmployeeController()