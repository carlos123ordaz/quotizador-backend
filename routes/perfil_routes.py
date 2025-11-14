from fastapi import APIRouter, HTTPException, status
from models.usuario_model import UsuarioUpdate, CambiarContrasena
from controllers.auth_controller import auth_controller

router = APIRouter(prefix="/api/perfil", tags=["perfil"])

@router.get("/{usuario_id}")
async def obtener_perfil(usuario_id: str):
    """Obtener información del perfil del usuario"""
    try:
        usuario = await auth_controller.obtener_usuario_por_id(usuario_id)
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return {
            "_id": str(usuario["_id"]),
            "nombre": usuario["nombre"],
            "apellido": usuario["apellido"],
            "iniciales": usuario["iniciales"],
            "es_lider": usuario["es_lider"],
            "webhook_bitrix": usuario["webhook_bitrix"],
            "activo": usuario["activo"],
            "fecha_creacion": usuario["fecha_creacion"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener perfil: {str(e)}"
        )

@router.put("/{usuario_id}")
async def actualizar_perfil(usuario_id: str, datos: UsuarioUpdate):
    """Actualizar datos del perfil"""
    try:
        usuario_actualizado = await auth_controller.actualizar_perfil(usuario_id, datos)
        
        return {
            "message": "Perfil actualizado exitosamente",
            "usuario": {
                "_id": str(usuario_actualizado["_id"]),
                "nombre": usuario_actualizado["nombre"],
                "apellido": usuario_actualizado["apellido"],
                "iniciales": usuario_actualizado["iniciales"],
                "es_lider": usuario_actualizado["es_lider"],
                "webhook_bitrix": usuario_actualizado["webhook_bitrix"],
                "activo": usuario_actualizado["activo"],
                "fecha_creacion": usuario_actualizado["fecha_creacion"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar perfil: {str(e)}"
        )

@router.post("/{usuario_id}/cambiar-contrasena")
async def cambiar_contrasena(usuario_id: str, datos: CambiarContrasena):
    """Cambiar contraseña del usuario"""
    try:
        success = await auth_controller.cambiar_contrasena(usuario_id, datos)
        
        if success:
            return {"message": "Contraseña cambiada exitosamente"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo cambiar la contraseña"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar contraseña: {str(e)}"
        )