from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from models.employee_model import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from controllers.employee_controller import employee_controller

router = APIRouter(prefix="/api/employees", tags=["Employees"])

@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)  # ✅ SIN barra
async def create_employee(employee: EmployeeCreate):
    try:
        return await employee_controller.create_employee(employee)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el empleado: {str(e)}"
        )

@router.get("", response_model=dict)  # ✅ SIN barra
async def get_all_employees(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    activo: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None)
):
    try:
        return await employee_controller.get_all_employees(
            skip=skip, limit=limit, activo=activo, search=search
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener empleados: {str(e)}"
        )

@router.get("/stats", response_model=dict)
async def get_employee_stats():
    try:
        return await employee_controller.get_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )

# ... resto de endpoints sin cambios