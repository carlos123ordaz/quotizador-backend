from fastapi import APIRouter, Body, Path, Query
from controllers.template_version_controller import template_version_controller
from models.template_version_model import TemplateVersionCreate, TemplateVersionUpdate

router = APIRouter(prefix="/api/template-versions", tags=["Template Versions"])


@router.get("")
async def get_all_versions():
    return await template_version_controller.get_all()


@router.get("/{version_id}")
async def get_version(version_id: str = Path(...)):
    return await template_version_controller.get_by_id(version_id)


@router.post("", status_code=201)
async def create_version(
    data: TemplateVersionCreate = Body(...),
    usuario_id: str = Query(..., description="ID del usuario líder que realiza la acción"),
):
    return await template_version_controller.create(data, usuario_id)


@router.put("/{version_id}")
async def update_version(
    version_id: str = Path(...),
    data: TemplateVersionUpdate = Body(...),
    usuario_id: str = Query(..., description="ID del usuario líder que realiza la acción"),
):
    return await template_version_controller.update(version_id, data, usuario_id)


@router.delete("/{version_id}")
async def delete_version(
    version_id: str = Path(...),
    usuario_id: str = Query(..., description="ID del usuario líder que realiza la acción"),
):
    return await template_version_controller.delete(version_id, usuario_id)
