
def convert_df_to_db_format(df, file_path):
    import pandas as pd
    productos = []
    for _, row in df.iterrows():
        producto = {
            "num_item": str(row.get('Num. Item', '')) if pd.notna(row.get('Num. Item')) else '',
            "marca": str(row.get('Marca', '')) if pd.notna(row.get('Marca')) else '',
            "codigo_completo": str(row.get('Código Completo', '')) if pd.notna(row.get('Código Completo')) else '',
            "familia": str(row.get('Familia', '')) if pd.notna(row.get('Familia')) else '',
            "departamento": str(row.get('Departamento', '')) if pd.notna(row.get('Departamento')) else '',
            "cantidad": float(row.get('Cantidad', 0)) if pd.notna(row.get('Cantidad')) else 0,
            "descuento_stf": float(row.get('Descuento STF', 0)) if pd.notna(row.get('Descuento STF')) else 0,
            "descuento_cisac": float(row.get('Descuento CISAC', 0)) if pd.notna(row.get('Descuento CISAC')) else 0,
            "margen": float(row.get('Margen', 0)) if pd.notna(row.get('Margen')) else 0,
            "fact_importacion": float(row.get('Fact. De Importación', 0)) if pd.notna(row.get('Fact. De Importación')) else 0,
            "costo_importacion": float(row.get('Costo de Importación', 0)) if pd.notna(row.get('Costo de Importación')) else 0,
            "total_c_fijos": float(row.get('Total C. Fijos', 0)) if pd.notna(row.get('Total C. Fijos')) else 0,
            "total_c_extras": float(row.get('Total C. Extras', 0)) if pd.notna(row.get('Total C. Extras')) else 0,
            "dias_fabricacion": int(row.get('Días fabricación', 0)) if pd.notna(row.get('Días fabricación')) else 0,
            "peso_unva": float(row.get('Peso (UNVA)', 0)) if pd.notna(row.get('Peso (UNVA)')) else 0,
            "tiempo_unva": float(row.get('Tiempo (UNVA)', 0)) if pd.notna(row.get('Tiempo (UNVA)')) else 0,
            "moneda": str(row.get('Moneda', '')) if pd.notna(row.get('Moneda')) else '',
            "precio_compra": float(row.get('Precio Compra', 0)) if pd.notna(row.get('Precio Compra')) else 0,
            "precio_compra_2": float(row.get('Precio Compra 2', 0)) if pd.notna(row.get('Precio Compra 2')) else 0,
            "precio_venta": float(row.get('Precio venta', 0)) if pd.notna(row.get('Precio venta')) else 0,
            "total": float(row.get('Total', 0)) if pd.notna(row.get('Total')) else 0,
        }
        productos.append(producto)
    
    num_deal = str(df['Num. Deal'].iloc[0]) if len(df) > 0 and pd.notna(df['Num. Deal'].iloc[0]) else ''
    num_oferta = str(df['Num. Oferta'].iloc[0]) if len(df) > 0 and pd.notna(df['Num. Oferta'].iloc[0]) else ''
    revision = str(df['Revisión'].iloc[0]) if len(df) > 0 and pd.notna(df['Revisión'].iloc[0]) else ''
    cliente = str(df['Cliente'].iloc[0]) if len(df) > 0 and pd.notna(df['Cliente'].iloc[0]) else ''
    
    resumen = {
        "total_precio_venta": float(df['Precio venta'].sum()) if 'Precio venta' in df.columns else 0,
        "total_general": float(df['Total'].sum()) if 'Total' in df.columns else 0,
        "cantidad_total": float(df['Cantidad'].sum()) if 'Cantidad' in df.columns else 0,
        "margen_promedio": float(df['Margen'].mean()) if 'Margen' in df.columns else 0,
        "productos_por_departamento": df['Departamento'].value_counts().to_dict() if 'Departamento' in df.columns else {}
    }
    
    return {
        "num_deal": num_deal,
        "num_oferta": num_oferta,
        "revision": revision,
        "cliente": cliente,
        "productos": productos,
        "total_productos": len(productos),
        "resumen_estadistico": resumen
    }