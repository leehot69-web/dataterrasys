

import pandas as pd
import lasio
from io import BytesIO
import tempfile
import os

def cargar_las_streamlit(archivo_subido):
    """Carga un archivo LAS desde un objeto subido en Streamlit."""
    try:
        # Leer el contenido
        contenido = archivo_subido.getvalue()
        
        # Si es string, convertir a bytes
        if isinstance(contenido, str):
            contenido = contenido.encode('utf-8')
        
        # Usar BytesIO
        las_file = BytesIO(contenido)
        las_file.seek(0)
        
        # Leer con lasio
        las = lasio.read(las_file)
        return las
        
    except Exception as e:
        # Método alternativo: archivo temporal
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.las', mode='wb') as tmp_file:
                contenido = archivo_subido.getvalue()
                if isinstance(contenido, str):
                    contenido = contenido.encode('utf-8')
                tmp_file.write(contenido)
                tmp_file_path = tmp_file.name
            
            las = lasio.read(tmp_file_path)
            os.unlink(tmp_file_path)
            return las
            
        except Exception as e2:
            raise Exception(f"No se pudo cargar el archivo LAS: {str(e2)}")

def resumen_las(las):
    """Genera un resumen del header y curvas del archivo LAS."""
    try:
        # Extraer información del header
        data = []
        for section_name, section in las.header.items():
            for item in section:
                data.append([
                    f"{section_name}.{item.mnemonic}",
                    str(item.unit) if hasattr(item, 'unit') else '',
                    str(item.value) if hasattr(item, 'value') else '',
                    str(item.descr) if hasattr(item, 'descr') else ''
                ])
        
        header_df = pd.DataFrame(data, columns=["Campo", "Unidades", "Valor", "Descripción"])
        
        # Listar curvas disponibles con más información
        curvas_info = []
        for curve in las.curves:
            curvas_info.append([
                curve.mnemonic,
                curve.unit if hasattr(curve, 'unit') else '',
                curve.descr if hasattr(curve, 'descr') else '',
                curve.value if hasattr(curve, 'value') else ''
            ])
        
        curvas_df = pd.DataFrame(curvas_info, columns=["Nombre", "Unidades", "Descripción", "Valor"])
        
        return {"header_df": header_df, "curvas_df": curvas_df}
        
    except Exception as e:
        # Retornar DataFrames básicos en caso de error
        header_df = pd.DataFrame([["Error", str(e), "", ""]], 
                               columns=["Campo", "Valor", "Unidades", "Descripción"])
        curvas_df = pd.DataFrame([["Error al leer curvas"]], 
                               columns=["Nombre"])
        return {"header_df": header_df, "curvas_df": curvas_df}

def analizar_intervalos(las):
    """Función placeholder para análisis avanzado."""
    return pd.DataFrame()

def obtener_info_pozo(las):
    """Extrae información específica del pozo del header LAS."""
    info_pozo = {
        'Nombre del Pozo': 'No encontrado',
        'UWI/API': 'No encontrado', 
        'Compañía': 'No encontrado',
        'Campo': 'No encontrado',
        'Ubicación': 'No encontrado',
        'Fecha': 'No encontrado',
        'Profundidad Mínima': 'No encontrado',
        'Profundidad Máxima': 'No encontrado'
    }
    
    try:
        # Buscar en la sección WELL (W) que contiene info del pozo
        if 'WELL' in las.header:
            for item in las.header['WELL']:
                mnemonic = item.mnemonic.upper()
                value = str(item.value)
                
                if mnemonic in ['WELL', 'NAME']:
                    info_pozo['Nombre del Pozo'] = value
                elif mnemonic in ['UWI', 'API']:
                    info_pozo['UWI/API'] = value
                elif mnemonic in ['COMP', 'COMPANY']:
                    info_pozo['Compañía'] = value
                elif mnemonic in ['FLD', 'FIELD']:
                    info_pozo['Campo'] = value
                elif mnemonic in ['LOC', 'LOCATION', 'COUNTY', 'STATE']:
                    info_pozo['Ubicación'] = value
                elif mnemonic in ['DATE', 'CREATED']:
                    info_pozo['Fecha'] = value
        
        # Obtener información de profundidad
        if hasattr(las, 'df') and not las.df().empty:
            df = las.df()
            info_pozo['Profundidad Mínima'] = f"{df.index.min():.2f}"
            info_pozo['Profundidad Máxima'] = f"{df.index.max():.2f}"
            
    except Exception as e:
        print(f"Error extrayendo información del pozo: {e}")
    
    return info_pozo

# Función opcional para debug (si la necesitas)
def debug_header(las):
    """Muestra todo el header para diagnóstico"""
    debug_info = []
    for section_name, section in las.header.items():
        for item in section:
            debug_info.append([section_name, item.mnemonic, str(item.value), str(item.unit)])
    return debug_info