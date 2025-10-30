from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional

from models.employee_model import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse
)
from controllers.employee_controller import employee_controller

router = APIRouter(
    prefix="/api/employees",
    tags=["Employees"]
)


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo empleado",
    description="Crea un nuevo empleado con código y nombre únicos"
)
async def create_employee(employee: EmployeeCreate):
    try:
        return await employee_controller.create_employee(employee)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el empleado: {str(e)}"
        )


@router.get(
    "/",
    response_model=dict,
    summary="Obtener todos los empleados",
    description="Obtiene una lista paginada de empleados con filtros opcionales"
)
async def get_all_employees(
    skip: int = Query(default=0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(default=100, ge=1, le=500, description="Número máximo de registros a retornar"),
    activo: Optional[bool] = Query(default=None, description="Filtrar por estado (true/false)"),
    search: Optional[str] = Query(default=None, description="Buscar por nombre o código")
):
    try:
        return await employee_controller.get_all_employees(
            skip=skip,
            limit=limit,
            activo=activo,
            search=search
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener empleados: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=dict,
    summary="Obtener estadísticas de empleados",
    description="Obtiene el total de empleados, activos e inactivos"
)
async def get_employee_stats():
    try:
        return await employee_controller.get_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Obtener un empleado por ID",
    description="Obtiene los detalles de un empleado específico"
)
async def get_employee(employee_id: str):
    employee = await employee_controller.get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con ID {employee_id} no encontrado"
        )
    return employee


@router.get(
    "/codigo/{codigo}",
    response_model=EmployeeResponse,
    summary="Obtener un empleado por código",
    description="Obtiene los detalles de un empleado por su código único"
)
async def get_employee_by_codigo(codigo: str):
    employee = await employee_controller.get_employee_by_codigo(codigo)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con código {codigo} no encontrado"
        )
    return employee


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Actualizar un empleado",
    description="Actualiza los datos de un empleado existente"
)
async def update_employee(employee_id: str, employee: EmployeeUpdate):
    try:
        updated_employee = await employee_controller.update_employee(employee_id, employee)
        if not updated_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empleado con ID {employee_id} no encontrado"
            )
        return updated_employee
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el empleado: {str(e)}"
        )


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un empleado",
    description="Elimina permanentemente un empleado del sistema"
)
async def delete_employee(employee_id: str):
    try:
        deleted = await employee_controller.delete_employee(employee_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empleado con ID {employee_id} no encontrado"
            )
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el empleado: {str(e)}"
        )