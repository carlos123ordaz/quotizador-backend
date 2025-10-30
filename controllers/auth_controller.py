from datetime import datetime
from typing import Optional
import bcrypt
from fastapi import HTTPException, status
from models.usuario_model import UsuarioCreate
from database import get_database

class AuthController:
    def __init__(self):
        self.db = None
        self.collection_name = "usuarios"
    
    @staticmethod
    def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                contrasena_plana.encode('utf-8'),
                contrasena_hash.encode('utf-8') if isinstance(contrasena_hash, str) else contrasena_hash
            )
        except Exception as e:
            print(f"Error verificando contraseña: {e}")
            return False
    
    @staticmethod
    def hashear_contrasena(contrasena: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(contrasena.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    async def obtener_usuario_por_iniciales(self, iniciales: str) -> Optional[dict]:
        db = get_database()
        usuario = await db[self.collection_name].find_one({"iniciales": iniciales.upper()})
        return usuario
    
    async def obtener_usuario_por_id(self, usuario_id: str) -> Optional[dict]:
        from bson import ObjectId
        db = get_database()
        
        try:
            usuario = await db[self.collection_name].find_one({"_id": ObjectId(usuario_id)})
            return usuario
        except Exception:
            return None
    
    async def crear_usuario(self, usuario: UsuarioCreate) -> dict:
        db = get_database()
        usuario_existente = await self.obtener_usuario_por_iniciales(usuario.iniciales)
        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las iniciales ya están en uso"
            )
        
        usuario_dict = {
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "iniciales": usuario.iniciales.upper(),
            "es_lider": usuario.es_lider,
            "webhook_bitrix": usuario.webhook_bitrix,
            "contrasena_hash": self.hashear_contrasena(usuario.contrasena),
            "activo": True,
            "fecha_creacion": datetime.utcnow(),
            "fecha_actualizacion": datetime.utcnow()
        }
        result = await db[self.collection_name].insert_one(usuario_dict)
        usuario_creado = await db[self.collection_name].find_one({"_id": result.inserted_id})
        
        return usuario_creado
    
    async def autenticar_usuario(self, iniciales: str, contrasena: str) -> Optional[dict]:
        usuario = await self.obtener_usuario_por_iniciales(iniciales)
        
        if not usuario:
            return None
        
        if not usuario.get("activo", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )
        
        if not self.verificar_contrasena(contrasena, usuario["contrasena_hash"]):
            return None
        
        return usuario

auth_controller = AuthController()