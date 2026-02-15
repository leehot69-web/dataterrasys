import lasio

def cargar_las(ruta_archivo):
    """
    Carga un archivo LAS y devuelve el objeto lasio.
    """
    try:
        las = lasio.read(ruta_archivo)
        print(f"Archivo {ruta_archivo} cargado con éxito.")
        return las
    except Exception as e:
        print(f"Error al cargar archivo LAS: {e}")
        return None
