from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Annotated
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ], serialization=core_schema.plain_serializer_function_ser_schema(
            lambda x: str(x)
        ))

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")


class EmployeeBase(BaseModel):
    codigo: int = Field(..., description="Código único del empleado")
    nombre: str = Field(..., description="Nombre completo del empleado")
    activo: bool = Field(default=True, description="Estado del empleado")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo": 123,
                "nombre": "Juan Pérez García",
                "activo": True
            }
        }
    )


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    codigo: Optional[int] = None
    nombre: Optional[str] = None
    activo: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Juan Pérez García",
                "activo": True
            }
        }
    )


class EmployeeInDB(EmployeeBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "codigo": "EMP001",
                "nombre": "Juan Pérez García",
                "activo": True,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )


class EmployeeResponse(BaseModel):
    _id: str
    codigo: int
    nombre: str
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "codigo": 123,
                "nombre": "Juan Pérez García",
                "activo": True,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )