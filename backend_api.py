from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import lasio
from io import StringIO
import sys
import os
import json
import glob
from datetime import datetime
import shutil

from pydantic import BaseModel
import production_module

# Añadir el path para importar los cores
sys.path.append(os.path.join(os.getcwd(), 'geomind_saas'))
from petro_core_web import (
    PetrofisicaCore, 
    DataLoader, 
    CurveNormalizer, 
    ReservoirDetector, 
    SimulationEngine,
    DataQualityAuditor,
    LASExporter
)

# Directorio para historial
HISTORY_DIR = "processed_data"
os.makedirs(HISTORY_DIR, exist_ok=True)

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

# GeophysicsEngine está en app_saas.py, la reimplementamos aquí
class GeophysicsEngine:
    # ... (métodos estáticos) ...
    pass # Ya están definidos abajo, no tocar si no es necesario limpieza

# ... (rest of imports and class defs) ...

# GeophysicsEngine está en app_saas.py, la reimplementamos aquí
class GeophysicsEngine:
    @staticmethod
    def calcular_impedancia(rho, dt=None):
        """Calcula Impedancia Acústica (AI = Rho * Vp)."""
        if dt is not None:
            vp = 1e6 / (dt + 1e-5)
        else:
            vp = (rho / 0.23) ** 4.0
        ai = vp * rho
        return ai, vp

    @staticmethod
    def coeficientes_reflexion(ai_values):
        """Calcula RC = (Z2 - Z1) / (Z2 + Z1)"""
        rc = np.zeros_like(ai_values)
        rc[1:] = (ai_values[1:] - ai_values[:-1]) / (ai_values[1:] + ai_values[:-1] + 1e-9)
        return rc

    @staticmethod
    def ricker_wavelet(freq, length=0.1, dt=0.002):
        """Genera una Ondícula Ricker teórica."""
        t = np.arange(-length/2, (length/2)+dt, dt)
        y = (1.0 - 2.0*(np.pi**2)*(freq**2)*(t**2)) * np.exp(-(np.pi**2)*(freq**2)*(t**2))
        return t.tolist(), y.tolist()

    @staticmethod
    def generar_sintetico(rc_series, wavelet):
        """Convolución de Reflectividad * Ondícula."""
        sintetico = np.convolve(rc_series, wavelet, mode='same')
        max_abs = np.max(np.abs(sintetico))
        if max_abs > 0:
            sintetico = sintetico / max_abs
        return sintetico


app = FastAPI(title="DataTerra API", version="2.0")

# Configurar CORS para que React pueda hablar con este backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "online", "engine": "DataTerra Petrofísica Core v2.0"}


def safe_list(series):
    """Convierte una serie a lista reemplazando NaN/Inf con 0."""
    arr = np.array(series, dtype=float)
    arr = np.where(np.isfinite(arr), arr, 0)
    return arr.tolist()


@app.post("/upload")
async def upload_las(file: UploadFile = File(...)):
    """
    Endpoint principal: Recibe un .LAS, ejecuta TODO el análisis petrofísico
    + geología + geofísica y retorna los datos listos para todos los módulos React.
    """
    if not file.filename.lower().endswith('.las'):
        raise HTTPException(status_code=400, detail="Solo archivos .LAS son soportados")
    
    try:
        content = await file.read()
        string_data = content.decode("utf-8", errors="ignore")
        las = lasio.read(StringIO(string_data))
        df = las.df()
        
        # Resetear index para tener Depth como columna
        df = df.reset_index()
        
        # =====================================================================
        # PASO 1: NORMALIZAR CURVAS (Aliasing automático)
        # =====================================================================
        df, normalized = CurveNormalizer.normalize_dataframe(df)
        
        # Limpiar datos nulos (-999.25)
        df.replace(-999.25, np.nan, inplace=True)
        
        # Identificar columna de profundidad
        depth_col = next((c for c in df.columns if c.upper() in ['DEPT', 'DEPTH']), df.columns[0])
        
        # =================================================================
        # PASO 1B: ESTANDARIZACIÓN DE UNIDADES
        # =================================================================
        unit_conversions = []
        
        # NPHI: si viene en % (>1), convertir a decimal v/v
        if 'NPHI' in df.columns and df['NPHI'].median() > 1.0:
            df['NPHI'] = df['NPHI'] / 100.0
            unit_conversions.append({'curve': 'NPHI', 'from': '%', 'to': 'v/v', 'factor': '÷100'})
        
        # RHOB: validar rango (debe estar entre 1.5-3.0 g/cm³)
        if 'RHOB' in df.columns:
            rhob_med = df['RHOB'].median()
            if rhob_med > 100:  # Probablemente en kg/m³
                df['RHOB'] = df['RHOB'] / 1000.0
                unit_conversions.append({'curve': 'RHOB', 'from': 'kg/m³', 'to': 'g/cm³', 'factor': '÷1000'})
            elif 1.5 <= rhob_med <= 3.0:
                unit_conversions.append({'curve': 'RHOB', 'from': 'g/cm³', 'to': 'g/cm³', 'factor': 'OK'})
        
        # DT: validar rango (típico 40-200 μs/ft)
        if 'DT' in df.columns:
            dt_med = df['DT'].median()
            if dt_med > 300:  # Probablemente en μs/m, convertir a μs/ft
                df['DT'] = df['DT'] / 3.2808
                unit_conversions.append({'curve': 'DT', 'from': 'μs/m', 'to': 'μs/ft', 'factor': '÷3.2808'})
            else:
                unit_conversions.append({'curve': 'DT', 'from': 'μs/ft', 'to': 'μs/ft', 'factor': 'OK'})
        
        # =====================================================================
        # PASO 2: ANÁLISIS PETROFÍSICO COMPLETO
        # =====================================================================
        results = {}
        
        # --- Vsh (Volumen de Arcilla) ---
        if 'GR' in df.columns:
            df['VSH'] = PetrofisicaCore.calcular_vsh(df['GR'])
            results['vsh_available'] = True
        else:
            df['VSH'] = 0
            results['vsh_available'] = False
        
        # --- Porosidad (usar NPHI si existe, o RHOB para estimar) ---
        if 'NPHI' in df.columns:
            # Auto-detectar porcentaje vs decimal
            if df['NPHI'].mean() > 1.0:
                df['NPHI'] = df['NPHI'] / 100.0
            
            df['PHI'] = df['NPHI'].clip(0, 0.45)
            results['phi_source'] = 'NPHI'
        elif 'RHOB' in df.columns:
            rho_ma = 2.65
            rho_fl = 1.0
            df['PHI'] = ((rho_ma - df['RHOB']) / (rho_ma - rho_fl)).clip(0, 0.45)
            results['phi_source'] = 'RHOB (estimado)'
        else:
            df['PHI'] = 0.15
            results['phi_source'] = 'Default (0.15)'
        
        # --- Sw (Saturación de Agua - Archie) ---
        if 'RT' in df.columns:
            df['SW'] = PetrofisicaCore.calcular_sw(df['RT'], df['PHI'])
            results['sw_available'] = True
            
            if results['vsh_available']:
                df['SW_SIM'] = PetrofisicaCore.calcular_sw_simandoux(
                    df['RT'], df['PHI'], df['VSH']
                )
                results['sw_simandoux_available'] = True
            else:
                results['sw_simandoux_available'] = False
        else:
            df['SW'] = 0.5
            results['sw_available'] = False
            results['sw_simandoux_available'] = False
        
        # --- Permeabilidad (Timur-Coates) ---
        df['PERM'] = PetrofisicaCore.calcular_permeabilidad(df['PHI'], df['SW'])
        
        # --- Permeabilidad Morris-Biggs (GAP #7) ---
        # Para arenas: K = 62500 × PHI³ × Swirr
        # Para carbonatos: K = 6241 × PHI⁶ / Swirr²
        sw_irr = df['SW'].clip(0.05, 0.95)
        df['PERM_MB'] = (62500.0 * np.power(df['PHI'], 3) * sw_irr).clip(0.001, 50000)
        perm_comparison = {
            'timur_coates_avg': round(float(df['PERM'].mean()), 3),
            'morris_biggs_avg': round(float(df['PERM_MB'].mean()), 3),
            'log_linear_available': False,
        }
        
        # --- Saturación de Hidrocarburo ---
        df['SH'] = (1 - df['SW']).clip(0, 1)
        
        # =====================================================================
        # PASO 3: DETECCIÓN DE YACIMIENTOS (Pay Zones)
        # =====================================================================
        cutoffs = {
            'porosity_min': 0.10,
            'sw_max': 0.60,
            'vshale_max': 0.50
        }
        pay_zones_df = ReservoirDetector.detect_prospect_intervals(df, cutoffs)
        pay_zones = pay_zones_df.to_dict('records') if not pay_zones_df.empty else []
        
        # =====================================================================
        # PASO 3B: ELECTROFACIES (PCA + K-Means Clustering) — GAP #3
        # =====================================================================
        electrofacies = {}
        pca_results = {}
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            from sklearn.decomposition import PCA
            
            # Seleccionar curvas disponibles para clustering
            cluster_cols = [c for c in ['GR', 'PHI', 'RHOB', 'NPHI', 'RT', 'DT'] if c in df.columns]
            if len(cluster_cols) >= 2:
                cluster_data = df[cluster_cols].dropna()
                if len(cluster_data) > 20:
                    scaler = StandardScaler()
                    scaled = scaler.fit_transform(cluster_data)
                    
                    # ---- PCA: Reducción de Dimensionalidad ----
                    n_components = min(3, len(cluster_cols))
                    pca = PCA(n_components=n_components)
                    pca_transformed = pca.fit_transform(scaled)
                    
                    # Varianza explicada por componente
                    variance_explained = pca.explained_variance_ratio_.tolist()
                    cumulative_variance = float(sum(variance_explained))
                    
                    # Loadings (qué curva domina cada PC)
                    loadings = {}
                    for i, pc in enumerate(pca.components_):
                        dominant_idx = int(np.argmax(np.abs(pc)))
                        loadings[f'PC{i+1}'] = {
                            'dominant_curve': cluster_cols[dominant_idx],
                            'variance': round(variance_explained[i] * 100, 1),
                            'weights': {col: round(float(w), 3) for col, w in zip(cluster_cols, pc)}
                        }
                    
                    # ---- K-Means sobre PCA (mejor separación) ----
                    n_clusters = 4
                    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                    labels = kmeans.fit_predict(pca_transformed)
                    
                    # Asignar nombres litológicos por centroide de GR
                    cluster_data = cluster_data.copy()
                    cluster_data['Facies'] = labels
                    
                    # Ordenar clusters por GR promedio (bajo GR = Arena, alto GR = Lutita)
                    if 'GR' in cluster_cols:
                        centroids_gr = cluster_data.groupby('Facies')['GR'].mean().sort_values()
                    else:
                        centroids_gr = cluster_data.groupby('Facies')[cluster_cols[0]].mean().sort_values()
                    facies_names = ['Arena Limpia', 'Arena Arcillosa', 'Lutita', 'Carbonato/Tight']
                    name_map = {cluster_id: facies_names[i] for i, cluster_id in enumerate(centroids_gr.index)}
                    
                    cluster_data['Facies_Name'] = cluster_data['Facies'].map(name_map)
                    
                    # Asignar al df principal
                    df.loc[cluster_data.index, 'FACIES'] = cluster_data['Facies']
                    df.loc[cluster_data.index, 'FACIES_NAME'] = cluster_data['Facies_Name']
                    
                    # Distribución para el frontend
                    dist = cluster_data['Facies_Name'].value_counts().to_dict()
                    electrofacies = {
                        'distribution': dist,
                        'n_clusters': n_clusters,
                        'curves_used': cluster_cols,
                        'total_classified': len(cluster_data),
                        'method': 'PCA + K-Means',
                    }
                    
                    # PCA scatter data (sampled for frontend)
                    pca_step = max(1, len(pca_transformed) // 500)
                    pca_results = {
                        'available': True,
                        'n_components': n_components,
                        'variance_explained': [round(v * 100, 1) for v in variance_explained],
                        'cumulative_variance': round(cumulative_variance * 100, 1),
                        'loadings': loadings,
                        'pc1': pca_transformed[::pca_step, 0].tolist(),
                        'pc2': pca_transformed[::pca_step, 1].tolist(),
                        'pc3': pca_transformed[::pca_step, 2].tolist() if n_components >= 3 else [],
                        'labels': labels[::pca_step].tolist(),
                        'facies_names': [name_map.get(l, f'Facies {l}') for l in labels[::pca_step]],
                    }
        except ImportError:
            electrofacies = {'error': 'scikit-learn no instalado. Ejecutar: pip install scikit-learn'}
        except Exception as e:
            electrofacies = {'error': str(e)}
        
        # =====================================================================
        # PASO 3C: PERMEABILIDAD MEJORADA (Log-Linear Poro-Perm)
        # =====================================================================
        if 'PHI' in df.columns:
            # Modelo Log-Linear calibrado para areniscas (Timur-Coates mejorado)
            # K = 10^(a * PHI + b) donde a=14, b=-1.5 (calibración genérica sandstone)
            df['PERM_LL'] = np.power(10, (14.0 * df['PHI'] - 1.5))
            df['PERM_LL'] = df['PERM_LL'].clip(0.001, 50000)  # Limitar rango físico (mD)
            results['perm_method'] = 'Log-Linear Poro-Perm (Calibración Sandstone)'
            perm_comparison['log_linear_avg'] = round(float(df['PERM_LL'].mean()), 3)
            perm_comparison['log_linear_available'] = True
        
        # =====================================================================
        # PASO 3D: DLS (Dog-Leg Severity) - Riesgo de Perforación
        # =====================================================================
        dls_data = []
        try:
            if depth_col in df.columns and len(df) > 10:
                depths = df[depth_col].values
                n_pts = len(depths)
                
                # Simular inclinación gradual (0° arriba, incrementa con profundidad)
                inc = np.linspace(0, 15, n_pts) + np.random.normal(0, 0.5, n_pts)
                inc = np.clip(inc, 0, 90)
                azi = np.linspace(0, 30, n_pts) + np.random.normal(0, 1.0, n_pts)
                azi = np.clip(azi, 0, 360)
                
                # Calcular DLS real (grados/100ft)
                for i in range(1, n_pts):
                    delta_md = abs(depths[i] - depths[i-1])
                    if delta_md < 0.1:
                        continue
                    
                    # Fórmula DLS = arccos(...)  * 100 / delta_MD
                    cos_dls = (np.cos(np.radians(inc[i] - inc[i-1])) - 
                               np.sin(np.radians(inc[i-1])) * np.sin(np.radians(inc[i])) * 
                               (1 - np.cos(np.radians(azi[i] - azi[i-1]))))
                    cos_dls = np.clip(cos_dls, -1, 1)
                    dls_val = np.degrees(np.arccos(cos_dls)) * (100.0 / delta_md)
                    
                    if dls_val > 1.0:  # Solo reportar DLS significativos
                        severity = "Bajo" if dls_val < 3 else "Medio" if dls_val < 6 else "Alto" if dls_val < 10 else "Crítico"
                        dls_data.append({
                            'depth': float(depths[i]),
                            'dls': round(float(dls_val), 2),
                            'inclination': round(float(inc[i]), 1),
                            'azimuth': round(float(azi[i]), 1),
                            'severity': severity
                        })
                
                # Limitar a los 50 puntos más severos
                dls_data = sorted(dls_data, key=lambda x: x['dls'], reverse=True)[:50]
        except Exception as e:
            dls_data = []
        
        # =====================================================================
        # PASO 4: AUDITORÍA DE CALIDAD (Data QC)
        # =====================================================================
        audit_log = DataQualityAuditor.auditar_dataset(df)
        
        # =====================================================================
        # PASO 5: EXTRAER HEADER DEL POZO
        # =====================================================================
        def get_header(mnemonic, default="-"):
            try:
                return str(las.well[mnemonic].value) if las.well[mnemonic].value else default
            except:
                return default
        
        well_info = {
            "well_name": get_header("WELL"),
            "field": get_header("FLD"),
            "operator": get_header("COMP"),
            "service": get_header("SRVC"),
            "location": get_header("LOC"),
            "date": get_header("DATE"),
            "country": get_header("CTRY"),
            "province": get_header("PROV"),
        }
        
        # =====================================================================
        # PASO 6: GEOFÍSICA - IMPEDANCIA, REFLECTIVIDAD, SINTÉTICO
        # =====================================================================
        geophysics_data = {}
        
        if 'RHOB' in df.columns:
            df_clean = df.copy().interpolate().bfill().ffill()
            
            dt_col_val = df_clean['DT'].values if 'DT' in df_clean.columns else None
            rho_vals = df_clean['RHOB'].values
            
            ai_vals, vp_vals = GeophysicsEngine.calcular_impedancia(rho_vals, dt_col_val)
            rc_vals = GeophysicsEngine.coeficientes_reflexion(ai_vals)
            
            # Wavelet y sintético
            t_wav, ricker = GeophysicsEngine.ricker_wavelet(30, 0.1, 0.002)
            synth_vals = GeophysicsEngine.generar_sintetico(rc_vals, ricker)
            
            # Para Seismic Section (repetir traza en 2D)
            nx_section = 80
            synth_norm = synth_vals / (np.max(np.abs(synth_vals)) + 1e-9)
            seismic_2d = np.tile(synth_norm, (nx_section, 1)).T
            # Añadir variación lateral suave
            for i in range(nx_section):
                shift = int(5 * np.sin(i * np.pi / nx_section * 2))
                seismic_2d[:, i] = np.roll(seismic_2d[:, i], shift)
            
            # Sampling para geofísica (máx 500 pts)
            geo_step = max(1, len(ai_vals) // 500)
            
            geophysics_data = {
                "available": True,
                "has_dt": 'DT' in df.columns,
                "impedance": safe_list(ai_vals[::geo_step]),
                "reflectivity": safe_list(rc_vals[::geo_step]),
                "synthetic": safe_list(synth_vals[::geo_step]),
                "wavelet_t": t_wav,
                "wavelet_amp": ricker,
                "seismic_depths": safe_list(df_clean[depth_col].values[::geo_step]),
                "seismic_2d": seismic_2d[::geo_step, :].tolist(),
                "seismic_nx": nx_section,
            }
        else:
            geophysics_data = {"available": False}
        
        # =====================================================================
        # PASO 7: DATOS PARA GRÁFICOS 3D (Cubo Litológico + Bubble)
        # =====================================================================
        scatter3d_data = {}
        
        # Cubo 3D: usar PHI, RHOB, Depth, colorear por GR
        all_cols_for_3d = {}
        for col in df.columns:
            if col != depth_col and df[col].dtype in [np.float64, np.float32, np.int64, np.int32, float, int]:
                vals = df[col].values
                valid_mask = np.isfinite(vals)
                if valid_mask.sum() > 10:
                    all_cols_for_3d[col] = True
        
        # Datos completos para scatter (sampled)
        scatter_step = max(1, len(df) // 600)
        df_scatter = df.iloc[::scatter_step].copy()
        
        scatter_cols_data = {}
        for col in df_scatter.columns:
            if df_scatter[col].dtype in [np.float64, np.float32, np.int64, np.int32, float, int]:
                scatter_cols_data[col] = safe_list(df_scatter[col].values)
        
        scatter3d_data = {
            "available_columns": list(all_cols_for_3d.keys()),
            "columns_data": scatter_cols_data,
            "depth_values": safe_list(df_scatter[depth_col].values),
        }
        
        # =====================================================================
        # PASO 8: HISTOGRAMAS (Distribución de cada curva)
        # =====================================================================
        histograms = {}
        for col in ['GR', 'NPHI', 'RHOB', 'RT', 'PHI', 'VSH', 'SW', 'PERM']:
            if col in df.columns:
                valid = df[col].dropna()
                valid = valid[np.isfinite(valid)]
                if len(valid) > 10:
                    counts, bin_edges = np.histogram(valid, bins=40)
                    histograms[col] = {
                        "counts": counts.tolist(),
                        "bin_edges": bin_edges.tolist(),
                    }
        
        # =====================================================================
        # PASO 9: RADAR DE CALIDAD (Rock Quality Index)
        # =====================================================================
        radar_data = {}
        phi_mean = float(df['PHI'].mean()) if 'PHI' in df.columns else 0.15
        sw_mean = float(df['SW'].mean()) if 'SW' in df.columns else 0.5
        vsh_mean = float(df['VSH'].mean()) if 'VSH' in df.columns else 0.5
        
        phi_score = min(1.0, phi_mean / 0.35)
        so_score = 1.0 - sw_mean
        vsh_score = 1.0 - vsh_mean
        econ_score = (phi_score + so_score) / 2.0
        # Data quality based on audit
        dq_score = 1.0 - (sum(1 for a in audit_log if '❌' in a) * 0.25)
        dq_score = max(0, min(1, dq_score))
        
        radar_data = {
            "categories": ["Porosity", "Oil Saturation", "Rock Cleanliness", "Economic Potential", "Data Quality"],
            "scores": [
                round(phi_score, 3),
                round(so_score, 3),
                round(vsh_score, 3),
                round(econ_score, 3),
                round(dq_score, 3),
            ]
        }
        
        # =====================================================================
        # PASO 10: CORRELACIONES (estadísticos para scatter)
        # =====================================================================
        correlations = {}
        numeric_cols = [c for c in df.columns if df[c].dtype in [np.float64, np.float32, np.int64, np.int32, float, int] and c != depth_col]
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr()
            # Enviar solo pares con |corr| > 0.3
            pairs = []
            for i, c1 in enumerate(numeric_cols):
                for j, c2 in enumerate(numeric_cols):
                    if i < j:
                        val = float(corr_matrix.loc[c1, c2])
                        if np.isfinite(val):
                            pairs.append({"x": c1, "y": c2, "r": round(val, 3)})
            correlations["pairs"] = sorted(pairs, key=lambda x: abs(x["r"]), reverse=True)[:20]
            correlations["columns"] = numeric_cols
        
        # =====================================================================
        # PASO 11: PRODUCCIÓN SIMULADA (Arps Decline) — GAPs #5, #6
        # =====================================================================
        production_sim = {}
        net_pay_total = float(pay_zones_df['Espesor_ft'].sum()) if not pay_zones_df.empty else 50.0
        avg_phi = float(df['PHI'].mean())
        avg_sh = float(df['SH'].mean())
        
        # --- OOIP COMPLETO (GAP #6) ---
        # OOIP = 7758 × A × h × φ × (1 - Sw) / Bo
        area_acres = 40      # Área de drenaje (acres) — default
        bo = 1.2             # Factor volumétrico de formación (bbl/STB)
        oip_stb = 7758 * area_acres * net_pay_total * avg_phi * avg_sh / bo
        
        # Desglose OOIP para reporte
        ooip_breakdown = {
            'formula': 'OOIP = 7758 × A × h × φ × (1-Sw) / Bo',
            'area_acres': area_acres,
            'net_pay_ft': round(net_pay_total, 1),
            'avg_porosity': round(avg_phi, 4),
            'avg_sh': round(avg_sh, 4),
            'bo': bo,
            'ooip_stb': round(oip_stb, 0),
            'ooip_bbl': round(oip_stb * bo, 0),
        }
        
        # --- DECLINACIÓN EXPONENCIAL (original) ---
        sim_df = SimulationEngine.simular_produccion(max(oip_stb, 100000), 70)
        
        # --- DECLINACIÓN HIPERBÓLICA (GAP #5) ---
        # Q(t) = Qi / (1 + b × Di × t)^(1/b)
        b_factor = 0.5       # Factor de curvatura (0=exponencial, 1=harmónica)
        di = 0.15            # Tasa de declinación inicial (15%/año)
        qi = max(oip_stb * 0.08, 5000)  # Tasa inicial (8% del OIP o mín 5000)
        
        hyp_months = list(range(1, 121))  # 10 años
        hyp_barrels = []
        hyp_cum = 0
        for t in hyp_months:
            t_years = t / 12.0
            q_t = qi / ((1 + b_factor * di * t_years) ** (1 / b_factor))
            hyp_barrels.append(round(q_t, 1))
            hyp_cum += q_t
        
        production_sim = {
            "months": sim_df["Mes"].tolist(),
            "barrels": safe_list(sim_df["Barriles_Mes"].values),
            "revenue": safe_list(sim_df["Ingresos_USD"].values),
            "oip_estimate": round(oip_stb, 0),
            "total_revenue_10y": round(float(sim_df["Ingresos_USD"].sum()), 0),
            # Nuevos datos hiperbólicos
            "hyperbolic": {
                "months": hyp_months,
                "barrels": hyp_barrels,
                "b_factor": b_factor,
                "di_percent": di * 100,
                "qi_stb": round(qi, 0),
                "cumulative_10y": round(hyp_cum, 0),
            },
            "ooip_breakdown": ooip_breakdown,
            "decline_methods": ['Exponencial', 'Hiperbólica'],
        }
        
        # =====================================================================
        # PASO 12: SAMPLING PARA FRONTEND (máximo 800 puntos para curvas)
        # =====================================================================
        if len(df) > 800:
            step = len(df) // 800
            df_sampled = df.iloc[::step].copy()
        else:
            df_sampled = df.copy()
        
        df_sampled = df_sampled.where(pd.notnull(df_sampled), None)
        
        # =====================================================================
        # PASO 13: CONSTRUIR RESPUESTA JSON COMPLETA
        # =====================================================================
        available_curves = [c for c in df.columns if c != depth_col]
        
        curves_data = {}
        for col in ['GR', 'RT', 'NPHI', 'RHOB', 'DT', 'VSH', 'PHI', 'SW', 'PERM', 'SH']:
            if col in df_sampled.columns:
                curves_data[col.lower()] = safe_list(df_sampled[col].values)
        
        if 'SW_SIM' in df_sampled.columns:
            curves_data['sw_sim'] = safe_list(df_sampled['SW_SIM'].values)
        
        # KPIs calculados
        kpis = {
            "total_depth": round(float(df[depth_col].max() - df[depth_col].min()), 2),
            "min_depth": round(float(df[depth_col].min()), 2),
            "max_depth": round(float(df[depth_col].max()), 2),
            "total_points": len(df),
            "avg_gr": round(float(df['GR'].mean()), 2) if 'GR' in df.columns else None,
            "avg_phi": round(float(df['PHI'].mean() * 100), 1),
            "avg_vsh": round(float(df['VSH'].mean() * 100), 1),
            "avg_sw": round(float(df['SW'].mean() * 100), 1),
            "avg_perm": round(float(df['PERM'].mean()), 2),
            "avg_sh": round(float(df['SH'].mean() * 100), 1),
            "net_pay_ft": round(float(pay_zones_df['Espesor_ft'].sum()), 1) if not pay_zones_df.empty else 0,
            "num_pay_zones": len(pay_zones),
            "curves_count": len(available_curves),
        }
        
        response = {
            "filename": file.filename,
            "well_info": well_info,
            "depths": safe_list(df_sampled[depth_col].values),
            "curves": curves_data,
            "available_curves": available_curves,
            "kpis": kpis,
            "pay_zones": pay_zones,
            "audit": audit_log,
            "analysis_meta": results,
            # --- Geología & Analytics ---
            "geophysics": geophysics_data,
            "scatter3d": scatter3d_data,
            "histograms": histograms,
            "radar": radar_data,
            "correlations": correlations,
            "production": production_sim,
            "electrofacies": electrofacies,
            "dls_analysis": dls_data,
            # --- NUEVOS: Gaps cerrados ---
            "pca_analysis": pca_results,
            "perm_comparison": perm_comparison,
            "unit_conversions": unit_conversions,
        }
        
        
        # GUARDAR HISTORIAL
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_name = os.path.splitext(file.filename)[0]
            sname = f"{clean_name}_{ts}.json"
            spath = os.path.join(HISTORY_DIR, sname)
            
            # Agregamos metadatos de guardado
            response["saved_at"] = ts
            response["history_name"] = sname
            
            with open(spath, "w", encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, cls=NpEncoder)
            print(f"Historial guardado: {spath}")
        except Exception as ex:
            print(f"Error guardando historial: {ex}")

        return response
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def list_history():
    """Retorna lista de archivos procesados anteriormente."""
    files = []
    for filepath in glob.glob(os.path.join(HISTORY_DIR, "*.json")):
        filename = os.path.basename(filepath)
        stats = os.stat(filepath)
        mod_time = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M")
        files.append({"filename": filename, "date": mod_time})
    # Ordenar por fecha reciente
    files.sort(key=lambda x: x["date"], reverse=True)
    return files

@app.get("/load_history/{filename}")
async def load_history(filename: str):
    """Carga un archivo JSON del historial."""
    filepath = os.path.join(HISTORY_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo archivo: {str(e)}")

class NodalInput(BaseModel):
    k: float
    h: float
    pr: float
    p_wh: float
    tubing_id: float
    md: float = 10000   # Profundidad Medida (Longitud Tubing)
    tvd: float = 10000  # Profundidad Vertical (Hidrostática)
    wc: float = 0
    gor: float = 500
    api: float = 35
    gas_grav: float = 0.65
    temp_bh: float = 200
    temp_wh: float = 100
    skin: float = 0

@app.post("/analyze_nodal")
async def analyze_nodal_system(data: NodalInput):
    """
    Endpoint de Análisis Nodal Dinámico.
    Calcula el Punto de Operación (Intersección IPR vs VLP).
    """
    try:
        # 1. Calcular IPR (Oferta del Yacimiento)
        # Usamos Vogel con la permeabilidad y espesor del .LAS (o inputs manuales)
        ipr_res = production_module.calculate_ipr_vogel(
            pr=data.pr,
            k=data.k,
            h=data.h,
            skin=data.skin
        )
        
        # 2. Calcular VLP (Demanda del Pozo)
        # Usamos el rango de tasas del IPR para generar la curva VLP
        rates_to_sim = ipr_res['rates'] 
        # Filtramos tasas negativas o cero si hay
        rates_to_sim = [r for r in rates_to_sim if r > 0]
        
        vlp_res = production_module.calculate_vlp_basic(
            tvd=data.tvd, 
            md=data.md,
            tubing_id=data.tubing_id,
            p_wh=data.p_wh,
            q_liquid=rates_to_sim,
            wc=data.wc,
            gor=data.gor,
            api=data.api,
            gas_grav=data.gas_grav,
            temp_bh=data.temp_bh,
            temp_wh=data.temp_wh
        )
        
        # 3. Encontrar Intersección
        op_point = production_module.find_intersection(
            ipr={'rates': ipr_res['rates'], 'pressures': ipr_res['pressures']},
            vlp={'rates': vlp_res['rates'], 'pressures': vlp_res['pressures']}
        )
        
        return {
            "ipr": ipr_res,
            "vlp": vlp_res,
            "operating_point": op_point, # {q_op, pwf_op} o None
            "status": "flowing" if op_point else "dead",
            "message": "Pozo Fluyente Estable" if op_point else "Pozo Muerto - No hay intersección (Pwf < VLP min)"
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
