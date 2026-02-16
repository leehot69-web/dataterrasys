
import os
import json
import google.generativeai as genai
from PIL import Image
import io
import base64

class GeminiGeophysicsCore:
    """Núcleo de Inteligencia Artificial para Geofísica usando Gemini Vision"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash') # Usamos flash por velocidad

    def detect_faults(self, image_bytes):
        """
        Analiza una imagen sísmica y detecta fallas estructurales.
        Retorna un JSON con las coordenadas de las fallas.
        """
        if not self.api_key:
            return {"error": "API Key de Gemini no configurada"}

        try:
            # Convertir bytes a imagen PIL
            img = Image.open(io.BytesIO(image_bytes))
            
            prompt = """
            Eres un geofísico experto en interpretación sísmica. 
            Analiza esta sección sísmica e identifica las fallas tectónicas (discontinuidades en los reflectores).
            
            Instrucciones:
            1. Identifica las fallas principales.
            2. Para cada falla, proporciona las coordenadas aproximadas [x, y] de los puntos inicial y final del segmento.
            3. Asume que la imagen es un plano cartesiano donde (0,0) es la esquina superior izquierda.
            4. Devuelve los resultados ESTRICTAMENTE en formato JSON plano con la siguiente estructura:
            {
              "faults": [
                {"id": 1, "points": [[x1, y1], [x2, y2]], "confidence": 0.95, "type": "normal"},
                ...
              ],
              "summary": "Breve descripción geológica de lo detectado"
            }
            No añadas texto extra fuera del JSON.
            """

            response = self.model.generate_content([prompt, img])
            
            # Limpiar la respuesta para extraer solo el JSON
            content = response.text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)

        except Exception as e:
            return {"error": str(e)}

    def analyze_well_log(self, log_data_json, well_name="Unknown"):
        """
        Analiza logs de pozo para buscar anomalías o zonas de interés.
        """
        if not self.api_key:
            return {"error": "API Key de Gemini no configurada"}

        try:
            prompt = f"""
            Analiza los siguientes datos petrofísicos del pozo {well_name}. 
            Busca zonas de interés (pay zones), anomalías de radioactividad o cruces de curvas sugerentes de hidrocarburos.
            
            Datos:
            {log_data_json}
            
            Proporciona un resumen ejecutivo técnico y recomendaciones.
            """
            
            response = self.model.generate_content(prompt)
            return {"analysis": response.text}

        except Exception as e:
            return {"error": str(e)}
