# routes/product_routes.py

from typing import Optional
from fastapi import APIRouter, Query, Body, Path
from controllers.product_controller import product_controller
from models.product_model import ProductModel, ProductUpdate, ProductResponse

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("", response_model=dict)
async def get_all_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    search: Optional[str] = Query(default=None)
):
    return await product_controller.get_all_products(
        skip=skip,
        limit=limit,
        search=search
    )

@router.get("/code/{code}", response_model=ProductResponse)
async def get_product_by_code(
    code: str = Path(..., description="Código del producto")
):
    product = await product_controller.get_product_by_code(code)
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    product_id: str = Path(..., description="ID del producto")
):
    return await product_controller.get_product_by_id(product_id)

@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductModel = Body(..., description="Datos del producto a crear")
):
    return await product_controller.create_product(product)

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str = Path(..., description="ID del producto a actualizar"),
    product_update: ProductUpdate = Body(..., description="Datos a actualizar")
):
    return await product_controller.update_product(product_id, product_update)

@router.delete("/{product_id}", response_model=dict)
async def delete_product(
    product_id: str = Path(..., description="ID del producto a eliminar")
):
    return await product_controller.delete_product(product_id)