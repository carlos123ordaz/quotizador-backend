from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler):
        from pydantic_core import core_schema
        
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    iniciales: str = Field(..., min_length=2, max_length=4)
    es_lider: bool = False
    webhook_bitrix: str = Field(..., min_length=10)
    @field_validator('iniciales')
    @classmethod
    def validar_iniciales(cls, v: str) -> str:
        if not v.isupper():
            raise ValueError('Las iniciales deben estar en mayúsculas')
        if not v.isalpha():
            raise ValueError('Las iniciales solo pueden contener letras')
        return v

    @field_validator('webhook_bitrix')
    @classmethod
    def validar_webhook(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('El webhook debe ser una URL válida')
        return v


class UsuarioCreate(UsuarioBase):
    contrasena: str = Field(..., min_length=6, max_length=100)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Juan",
                "apellido": "Pérez",
                "iniciales": "JP",
                "es_lider": True,
                "webhook_bitrix": "https://bitrix.example.com/webhook/abc123",
                "contrasena": "password123"
            }
        }
    )

class UsuarioLogin(BaseModel):
    """Modelo para login"""
    iniciales: str = Field(..., min_length=2, max_length=4)
    contrasena: str = Field(..., min_length=6)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "iniciales": "JP",
                "contrasena": "password123"
            }
        }
    )

class UsuarioInDB(UsuarioBase):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    contrasena_hash: str
    activo: bool = True
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "nombre": "Juan",
                "apellido": "Pérez",
                "iniciales": "JP",
                "es_lider": True,
                "webhook_bitrix": "https://bitrix.example.com/webhook/abc123",
                "contrasena_hash": "hashed_password",
                "activo": True,
                "fecha_creacion": "2024-01-01T00:00:00",
                "fecha_actualizacion": "2024-01-01T00:00:00"
            }
        }
    )

class UsuarioResponse(UsuarioBase):
    """Modelo de respuesta de Usuario (sin contraseña)"""
    id: str = Field(alias="_id")
    activo: bool
    fecha_creacion: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "nombre": "Juan",
                "apellido": "Pérez",
                "iniciales": "JP",
                "es_lider": True,
                "webhook_bitrix": "https://bitrix.example.com/webhook/abc123",
                "activo": True,
                "fecha_creacion": "2024-01-01T00:00:00"
            }
        }
    )


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    webhook_bitrix: Optional[str] = Field(None, min_length=10)
    es_lider: Optional[bool] = None

    @field_validator('webhook_bitrix')
    @classmethod
    def validar_webhook(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('El webhook debe ser una URL válida')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Juan Carlos",
                "webhook_bitrix": "https://bitrix.example.com/webhook/nuevo123"
            }
        }
    )

class CambiarContrasena(BaseModel):
    contrasena_actual: str = Field(..., min_length=6)
    contrasena_nueva: str = Field(..., min_length=6)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contrasena_actual": "password123",
                "contrasena_nueva": "newpassword456"
            }
        }
    )

