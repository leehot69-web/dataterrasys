import sqlite3
import json
import pandas as pd
from datetime import datetime
import os

DB_NAME = "geomind_local.db"

def init_db():
    """Inicializa la base de datos local si no existe."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabla de Proyectos (Pozos)
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_name TEXT,
            filename TEXT,
            upload_date TEXT,
            result_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_project(well_name, filename, df_results, params=None):
    """Guarda un análisis completo en la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Convertir DataFrame a JSON para almacenamiento ligero (o CSV string)
    # Para datasets masivos, lo ideal es guardar parquet en disco y linkear, 
    # pero para LAS típicos (10-50k filas) JSON comprimido o CSV string en BD aguanta bien.
    # Aquí guardaremos resultados clave resumidos y parámetros, y la data cruda.
    
    result_package = {
        "params": params or {},
        "data_csv": df_results.to_csv(index=False), # Guardamos data procesada
        "summary": df_results.describe().to_dict()
    }
    
    json_data = json.dumps(result_package)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute("INSERT INTO projects (well_name, filename, upload_date, result_json) VALUES (?, ?, ?, ?)",
              (well_name, filename, date_str, json_data))
    
    conn.commit()
    project_id = c.lastrowid
    conn.close()
    return project_id

def load_history():
    """Carga el historial de proyectos (solo metadatos)."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, well_name, filename, upload_date FROM projects ORDER BY id DESC", conn)
    conn.close()
    return df

def load_project_data(project_id):
    """Recupera la data completa de un proyecto."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT result_json FROM projects WHERE id=?", (project_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        package = json.loads(row[0])
        from io import StringIO
        df = pd.read_csv(StringIO(package["data_csv"]))
        return df, package["params"]
    return None, None
