# controllers/processed_excel_controller.py

from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from fastapi import HTTPException
from database import get_database
from models.processed_products_model import ProcessedExcelModel, ProcessedExcelResponse
import pandas as pd
from io import BytesIO

class ProcessedExcelController:
    def __init__(self):
        self.db = None
        self.collection_name = "processed_excels"
    
    def get_collection(self):
        if self.db is None:
            self.db = get_database()
        return self.db[self.collection_name]

    async def save_processed_excel(self, data: ProcessedExcelModel) -> ProcessedExcelResponse:
        """Guardar Excel procesado en la base de datos"""
        collection = self.get_collection()
        
        excel_dict = data.model_dump(exclude_unset=True)
        excel_dict["created_at"] = datetime.utcnow()
        
        result = await collection.insert_one(excel_dict)
        created = await collection.find_one({"_id": result.inserted_id})
        created["_id"] = str(created["_id"])
        
        return ProcessedExcelResponse(**created)

    async def get_by_history_id(self, history_id: str) -> Optional[ProcessedExcelResponse]:
        """Obtener Excel procesado por history_id"""
        collection = self.get_collection()
        
        excel = await collection.find_one({"history_id": history_id})
        if not excel:
            return None
        
        excel["_id"] = str(excel["_id"])
        return ProcessedExcelResponse(**excel)

    async def export_to_excel(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        num_deal: Optional[str] = None,
        cliente: Optional[str] = None,
        departamento: Optional[str] = None
    ) -> BytesIO:
        """Exportar datos filtrados a Excel"""
        collection = self.get_collection()
        
        # Construir query de filtros
        query = {}
        
        if fecha_inicio or fecha_fin:
            date_query = {}
            if fecha_inicio:
                date_query["$gte"] = datetime.fromisoformat(fecha_inicio)
            if fecha_fin:
                date_query["$lte"] = datetime.fromisoformat(fecha_fin)
            query["created_at"] = date_query
        
        if num_deal:
            query["num_deal"] = num_deal
        
        if cliente:
            query["cliente"] = {"$regex": cliente, "$options": "i"}
        
        # Obtener datos
        cursor = collection.find(query).sort("created_at", -1)
        excels = await cursor.to_list(length=None)
        
        if not excels:
            raise HTTPException(status_code=404, detail="No se encontraron datos para exportar")
        
        # Consolidar todos los productos
        all_products = []
        for excel in excels:
            for producto in excel.get("productos", []):
                # Filtrar por departamento si se especifica
                if departamento and producto.get("departamento") != departamento:
                    continue
                
                product_row = {
                    "Cliente": excel.get("cliente"),
                    "Num. Deal": excel.get("num_deal"),
                    "Num. Oferta": excel.get("num_oferta"),
                    "Revisión": excel.get("revision"),
                    "Fecha Procesamiento": excel.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if excel.get("created_at") else "",
                    "Num. Item": producto.get("num_item"),
                    "Marca": producto.get("marca"),
                    "Código Completo": producto.get("codigo_completo"),
                    "Familia": producto.get("familia"),
                    "Departamento": producto.get("departamento"),
                    "Cantidad": producto.get("cantidad"),
                    "Descuento STF": producto.get("descuento_stf"),
                    "Descuento CISAC": producto.get("descuento_cisac"),
                    "Margen": producto.get("margen"),
                    "Fact. De Importación": producto.get("fact_importacion"),
                    "Costo de Importación": producto.get("costo_importacion"),
                    "Total C. Fijos": producto.get("total_c_fijos"),
                    "Total C. Extras": producto.get("total_c_extras"),
                    "Días fabricación": producto.get("dias_fabricacion"),
                    "Peso (UNVA)": producto.get("peso_unva"),
                    "Tiempo (UNVA)": producto.get("tiempo_unva"),
                    "Moneda": producto.get("moneda"),
                    "Precio Compra": producto.get("precio_compra"),
                    "Precio Compra 2": producto.get("precio_compra_2"),
                    "Precio venta": producto.get("precio_venta"),
                    "Total": producto.get("total")
                }
                all_products.append(product_row)
        
        # Crear DataFrame
        df = pd.DataFrame(all_products)
        
        # Crear archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Productos Consolidados')
            
            # Agregar hoja de resumen
            summary_data = {
                "Métrica": [
                    "Total Registros",
                    "Total Archivos Procesados",
                    "Rango de Fechas",
                    "Deals Únicos",
                    "Clientes Únicos"
                ],
                "Valor": [
                    len(all_products),
                    len(excels),
                    f"{fecha_inicio or 'N/A'} - {fecha_fin or 'N/A'}",
                    len(set(p["Num. Deal"] for p in all_products)),
                    len(set(p["Cliente"] for p in all_products))
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, index=False, sheet_name='Resumen')
        
        output.seek(0)
        return output

    async def get_export_stats(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None
    ) -> dict:
        """Obtener estadísticas para preview antes de exportar"""
        collection = self.get_collection()
        
        query = {}
        if fecha_inicio or fecha_fin:
            date_query = {}
            if fecha_inicio:
                date_query["$gte"] = datetime.fromisoformat(fecha_inicio)
            if fecha_fin:
                date_query["$lte"] = datetime.fromisoformat(fecha_fin)
            query["created_at"] = date_query
        
        total_archivos = await collection.count_documents(query)
        
        cursor = collection.find(query)
        excels = await cursor.to_list(length=None)
        
        total_productos = sum(excel.get("total_productos", 0) for excel in excels)
        deals_unicos = len(set(excel.get("num_deal") for excel in excels))
        clientes_unicos = len(set(excel.get("cliente") for excel in excels))
        
        # Productos por departamento
        dept_count = {}
        for excel in excels:
            for producto in excel.get("productos", []):
                dept = producto.get("departamento", "Sin departamento")
                dept_count[dept] = dept_count.get(dept, 0) + 1
        
        return {
            "total_archivos": total_archivos,
            "total_productos": total_productos,
            "deals_unicos": deals_unicos,
            "clientes_unicos": clientes_unicos,
            "productos_por_departamento": dept_count,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        }

processed_excel_controller = ProcessedExcelController()