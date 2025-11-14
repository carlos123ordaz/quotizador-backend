from datetime import datetime
from typing import Optional
import bcrypt
from fastapi import HTTPException, status
from models.usuario_model import UsuarioCreate
from database import get_database
from models.usuario_model import UsuarioUpdate, CambiarContrasena

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
    
    async def actualizar_perfil(self, usuario_id: str, datos: UsuarioUpdate) -> dict:
        """Actualizar datos del perfil del usuario"""
        from bson import ObjectId
        db = get_database()

        try:
            # Preparar datos de actualización
            update_data = {}
            if datos.nombre is not None:
                update_data["nombre"] = datos.nombre
            if datos.apellido is not None:
                update_data["apellido"] = datos.apellido
            if datos.webhook_bitrix is not None:
                update_data["webhook_bitrix"] = datos.webhook_bitrix

            # Si hay iniciales nuevas, verificar que no estén en uso
            if datos.iniciales is not None:
                iniciales_upper = datos.iniciales.upper()
                usuario_existente = await db[self.collection_name].find_one({
                    "iniciales": iniciales_upper,
                    "_id": {"$ne": ObjectId(usuario_id)}
                })
                if usuario_existente:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Las iniciales ya están en uso por otro usuario"
                    )
                update_data["iniciales"] = iniciales_upper

            if datos.es_lider is not None:
                update_data["es_lider"] = datos.es_lider

            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No hay datos para actualizar"
                )

            update_data["fecha_actualizacion"] = datetime.utcnow()

            # Actualizar en la base de datos
            result = await db[self.collection_name].update_one(
                {"_id": ObjectId(usuario_id)},
                {"$set": update_data}
            )

            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado"
                )

            # Obtener usuario actualizado
            usuario_actualizado = await db[self.collection_name].find_one(
                {"_id": ObjectId(usuario_id)}
            )

            return usuario_actualizado
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar perfil: {str(e)}"
            )
    async def cambiar_contrasena(self, usuario_id: str, datos: CambiarContrasena) -> bool:
        from bson import ObjectId
        db = get_database()

        try:
            usuario = await db[self.collection_name].find_one({"_id": ObjectId(usuario_id)})

            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado"
                )
            if not self.verificar_contrasena(datos.contrasena_actual, usuario["contrasena_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La contraseña actual es incorrecta"
                )
            nueva_hash = self.hashear_contrasena(datos.contrasena_nueva)
            result = await db[self.collection_name].update_one(
                {"_id": ObjectId(usuario_id)},
                {
                    "$set": {
                        "contrasena_hash": nueva_hash,
                        "fecha_actualizacion": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al cambiar contraseña: {str(e)}"
            )
auth_controller = AuthController()