from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from models.usuario_model import UsuarioCreate, UsuarioLogin
from controllers.auth_controller import auth_controller

router = APIRouter(prefix="/api", tags=["autenticación"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

async def obtener_usuario_actual(token: str = Depends(oauth2_scheme)) -> dict:
    usuario = await auth_controller.verificar_token(token)
    return usuario

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def registrar_usuario(usuario: UsuarioCreate):
    try:
        usuario_creado = await auth_controller.crear_usuario(usuario)
        return {
            "message": "Usuario registrado exitosamente",
            "usuario": {
                "_id": str(usuario_creado["_id"]),
                "nombre": usuario_creado["nombre"],
                "apellido": usuario_creado["apellido"],
                "iniciales": usuario_creado["iniciales"],
                "es_lider": usuario_creado["es_lider"],
                "webhook_bitrix": usuario_creado["webhook_bitrix"],
                "activo": usuario_creado["activo"],
                "fecha_creacion": usuario_creado["fecha_creacion"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(e)}"
        )

@router.post("/login")
async def login(usuario_login: UsuarioLogin):
    usuario = await auth_controller.autenticar_usuario(
        usuario_login.iniciales,
        usuario_login.contrasena
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "_id": str(usuario["_id"]),
        "nombre": usuario["nombre"],
        "apellido": usuario["apellido"],
        "iniciales": usuario["iniciales"],
        "es_lider": usuario["es_lider"],
        "webhook_bitrix": usuario["webhook_bitrix"]
    }