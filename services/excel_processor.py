import pandas as pd
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple
import time
from services.excel_utils import convert_df_to_db_format

def get_df(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, engine='openpyxl')
    if pd.isna(df.iloc[233, 112]):
        num_deal =  df.iloc[350, 112]
        cliente = df.iloc[355, 70]
        coti_split = str(df.iloc[351, 112]).split('-')
    else:
        num_deal = df.iloc[233, 112]
        cliente = df.iloc[238, 70]
        coti_split = str(df.iloc[234, 112]).split('-')
    num_coti = coti_split[1] if len(coti_split) > 1 else ''
    num_revi = coti_split[2] if len(coti_split) > 2 else ''
    top = df[df['Factor STD'] == "Precio Lista"].index[0] if (df['Factor STD'] == "Precio Lista").any() else 0
    new_header = df.iloc[top]
    df = df.iloc[top+1:].copy()
    df.columns = new_header
    df.reset_index(drop=True, inplace=True)
    df.columns = df.columns.astype(str)
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        dup_indices = cols[cols == dup].index.tolist()
        cols.iloc[dup_indices] = [f"{dup}_{i}" for i in range(len(dup_indices))]
    df.columns = cols
    df.dropna(axis=1, how='all', inplace=True)
    mask = (
        pd.notna(df['Precio Compra Unitario']) & 
        (df['Precio Compra Unitario'] != 0) & 
        (df['Precio Compra Unitario'] != '*')
    )
    df_filtered = df[mask].copy()
    unva_mask = df_filtered['Departamento'] == 'UN VA'
    df_filtered.loc[unva_mask, 'Peso (UNVA)'] = df_filtered.loc[unva_mask].apply(
        lambda row: df.at[row.name + 2, 'Precio Neto'] if row.name + 2 < len(df) else 0, axis=1
    )
    df_filtered.loc[unva_mask, 'Tiempo (UNVA)'] = df_filtered.loc[unva_mask].apply(
        lambda row: df.at[row.name + 6, 'Precio Neto'] if row.name + 6 < len(df) else 0, axis=1
    )
    df_filtered.loc[~unva_mask, 'Peso (UNVA)'] = 0
    df_filtered.loc[~unva_mask, 'Tiempo (UNVA)'] = 0
    df_filtered['Cliente'] = cliente
    df_filtered['Num. Deal'] = num_deal
    df_filtered['Num. Oferta'] = num_coti
    df_filtered['Revisión'] = num_revi
    idx = df.columns.get_loc('Precio Neto')
    if idx + 1 < len(df.columns):
        next_col = df.columns[idx + 1]
        df_filtered['Descuento CISAC'] = df_filtered[next_col] if next_col in df_filtered.columns else None

    filtered_items = [
        'Cliente', 'Num. Deal', 'Num. Oferta', 'Revisión', '#Item',
        'Marca_0', 'Código', 'Familia', 'Departamento', 'Qty_1', 
        'STF_0', 'Descuento CISAC', 'Margen Total %', 'F.Importación',
        'Costo importación', 'Total Costos Fijos', 'Aplicativos',
        'WD', 'Peso (UNVA)', 'Tiempo (UNVA)', 'Moneda1', 
        'Precio Lista Unitario', 'Precio Compra Unitario', 
        'Precio Unitario Final', 'Precio Total Final'
    ]

    existing_cols = [col for col in filtered_items if col in df_filtered.columns]
    df_filtered = df_filtered[existing_cols]
    rename_dict = {
        '#Item': 'Num. Item', 'Marca_0': 'Marca',
        'Código': 'Código Completo', 'Qty_1': 'Cantidad',
        'STF_0': 'Descuento STF', 'Margen Total %': 'Margen',
        'F.Importación': 'Fact. De Importación',
        'Costo importación': 'Costo de Importación',
        'Total Costos Fijos': 'Total C. Fijos',
        'Aplicativos': 'Total C. Extras',
        'WD': 'Días fabricación', 'Moneda1': 'Moneda',
        'Precio Lista Unitario': 'Precio Compra',
        'Precio Compra Unitario': 'Precio Compra 2',
        'Precio Unitario Final': 'Precio venta',
        'Precio Total Final': 'Total'
    }
    df_filtered.rename(columns=rename_dict, inplace=True)
    return df_filtered


def process_file(file_path: str) -> Tuple[pd.DataFrame, str, str]:
    try:
        df = get_df(file_path)
        return df, None, os.path.basename(file_path)
    except Exception as e:
        return None, str(e), os.path.basename(file_path)


class ExcelProcessor:
    def __init__(self):
        self.max_workers = 2

    def process_multiple_files(self, file_paths: List[str]) -> dict:
        start_time = time.time()
        dataframes = []
        errors = []
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(process_file, file_path): file_path 
                for file_path in file_paths
            }
            
            for future in as_completed(future_to_file):
                df, error, filename = future.result()
                if df is not None:
                    dataframes.append(df)
                else:
                    errors.append({"file": filename, "error": error})

        if dataframes:
            df_final = pd.concat(dataframes, ignore_index=True)
            processing_time = time.time() - start_time
            return {
                "success": True,
                "dataframe": df_final,
                "processed_files": len(dataframes),
                "files_with_errors": len(errors),
                "total_files": len(file_paths),
                "total_records": len(df_final),
                "errors": errors,
                "processing_time": round(processing_time, 2)
            }
        else:
            return {
                "success": False,
                "error": "No se pudo procesar ningún archivo",
                "errors": errors
            }
    def process_file_for_db(self, file_path: str) -> dict:
        try:
            
            df = get_df(file_path)
            result = convert_df_to_db_format(df, file_path)
            return {
                "success": True,
                **result
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
            
excel_processor = ExcelProcessor()