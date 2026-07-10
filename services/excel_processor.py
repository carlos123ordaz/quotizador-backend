import pandas as pd
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
import time
from services.excel_utils import convert_df_to_db_format

logger = logging.getLogger(__name__)

_TEMPLATE_CONFIGS = [
    # Plantilla 2 (más reciente) — anclas en filas 350-352
    {
        'anchors': [(350, 112), (351, 112), (352, 112)],
        'num_deal': (350, 112),
        'cliente':  (355, 70),
        'coti':     (351, 112),
    },
    # Plantilla 1 (legado) — anclas en filas 233-235
    {
        'anchors': [(233, 112), (234, 112), (235, 112)],
        'num_deal': (233, 112),
        'cliente':  (238, 70),
        'coti':     (234, 112),
    },
]

def _detect_template(df: pd.DataFrame) -> dict:
    def score(cfg):
        return sum(
            1 for r, c in cfg['anchors']
            if pd.notna(df.iloc[r, c]) and str(df.iloc[r, c]).strip() not in ('', 'nan')
        )
    return max(_TEMPLATE_CONFIGS, key=score)

def get_df(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, engine='openpyxl')
    tpl = _detect_template(df)
    num_deal   = df.iloc[tpl['num_deal'][0], tpl['num_deal'][1]]
    cliente    = df.iloc[tpl['cliente'][0],  tpl['cliente'][1]]
    coti_split = str(df.iloc[tpl['coti'][0], tpl['coti'][1]]).split('-')
    num_coti = coti_split[1] if len(coti_split) > 1 else ''
    num_revi = coti_split[2] if len(coti_split) > 2 else ''
    top = df[df['Factor STD'] == "Precio Lista"].index[0] if (df['Factor STD'] == "Precio Lista").any() else 0
    new_header = df.iloc[top]
    df = df.iloc[top+1:].copy()
    df.columns = range(len(df.columns))  # temp numeric columns to avoid issues
    df.reset_index(drop=True, inplace=True)
    header_values = [str(v) if pd.notna(v) else f"col_{i}" for i, v in enumerate(new_header)]
    seen = {}
    unique_cols = []
    for name in header_values:
        if name in seen:
            seen[name] += 1
            unique_cols.append(f"{name}_{seen[name]}")
        else:
            seen[name] = 0
            unique_cols.append(name)
    df.columns = unique_cols
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
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
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
            for err in errors:
                logger.error(f"Error procesando {err['file']}: {err['error']}")
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