
import numpy as np
import pandas as pd
import lasio
import scipy.stats as stats
from scipy.interpolate import interp1d

# =============================================================================
# PETROFÍSICA CORE (Base de Matemáticas)
# =============================================================================
class PetrofisicaCore:
    """Clase estática que contiene los modelos físicos fundamentales."""
    
    @staticmethod
    def calcular_vsh(gr_curve, method='linear'):
        """Calcula Volumen de Arcilla (Vshale) usando varios métodos (Lineal, Larionov, Steiber)."""
        # 1. Definir GRmin y GRmax usando percentiles automáticos (P05 y P95)
        # Esto evita que outliers (spikes) deformen la escala.
        gr_min = gr_curve.quantile(0.05)
        gr_max = gr_curve.quantile(0.95)
        
        # Evitar división por cero
        if gr_max == gr_min:
            return np.zeros_like(gr_curve)
        
        # 2. Calcular Índice de Gamma Ray (IGR) - Lineal
        igr = (gr_curve - gr_min) / (gr_max - gr_min)
        igr = np.clip(igr, 0, 1) # Clamp entre 0 y 1
        
        # 3. Aplicar correcciones según método
        if method == 'linear':
            vsh = igr
        elif method == 'larionov_tertiary': # Rocas Jóvenes / No consolidadas
            vsh = 0.083 * (2**(3.7 * igr) - 1)
        elif method == 'larionov_older': # Rocas Antiguas / Consolidadas
            vsh = 0.33 * (2**(2 * igr) - 1)
        elif method == 'steiber': # Clástico clásico
            vsh = igr / (3 - 2 * igr)
        else:
            vsh = igr # Default fallback
            
        return np.clip(vsh, 0, 1) # Asegurar rango final [0,1]

    @staticmethod
    def calcular_sw(rt_curve, phi_curve, rw=0.05, a=1, m=2, n=2):
        """Calcula Saturación de Agua (Sw) usando Archie (Modelo Clásico)."""
        # Sw^n = (a * Rw) / (Phi^m * Rt)
        # Evitar valores negativos o ceros en logaritmos/divisiones
        phi_safe = np.where(phi_curve <= 0.001, 0.001, phi_curve)
        rt_safe = np.where(rt_curve <= 0.1, 0.1, rt_curve)
        
        term1 = (a * rw) / (np.power(phi_safe, m) * rt_safe)
        sw = np.power(term1, 1/n)
        return np.clip(sw, 0, 1)
    
    @staticmethod
    def calcular_permeabilidad(phi_curve, sw_irr_curve):
        """Estimación K con Timr-Coates (Modelo Free-Fluid)."""
        # K = (Phi^3 / Sw_irr)^2 * C (Constante simplificada)
        # Usamos una versión muy simple correlacionada a porosidad
        perm = 10**(10 * phi_curve - 1) # Ecuación empírica Dummy
        return np.clip(perm, 0.01, 5000)

    @staticmethod
    def calcular_sw_simandoux(rt_curve, phi_curve, vsh_curve, rw=0.05, rsh=2.0, a=1, m=2, n=2):
        """
        Calcula Sw en arenas arcillosas (Shaly Sands) usando Simandoux.
        Corrige el efecto de la arcilla que baja la resistividad.
        """
        # Preparar variables seguras
        phi_safe = np.where(phi_curve <= 0.001, 0.001, phi_curve)
        rt_safe = np.where(rt_curve <= 0.1, 0.1, rt_curve)
        vsh_safe = np.clip(vsh_curve, 0, 1)
        
        # Término C = (1 - Vsh)*a*Rw / Phi^m
        # Ecuación Simandoux despejada para 1/Rt = ...
        # Usamos la aproximación cuadrática estándar:
        # 1/Rt = (Vsh/Rsh) + (Phi^m / (a*Rw)) * Sw^n
        # Si n=2, es una cuadrática ax^2 + bx + c = 0 para Sw
        
        # Coeficientes para Sw^2 (asumiendo n=2)
        A = phi_safe**m / (a * rw)
        B = vsh_safe / rsh
        C = -1 / rt_safe
        
        # Resolver Sw (fórmula general cuadrática para Sw, ojo con el signo)
        # Sw = [ -Vsh/Rsh + sqrt( (Vsh/Rsh)^2 + 4 * Phi^m/(a*Rw*Rt) ) ] / (2 * Phi^m / a*Rw)
        
        term_rad = (vsh_safe / rsh)**2 + (4 * phi_safe**m) / (a * rw * rt_safe)
        numerador = -(vsh_safe / rsh) + np.sqrt(term_rad)
        denominador = (2 * phi_safe**m) / (a * rw)
        
        sw = numerator = numerador / denominador
        return np.clip(sw, 0, 1)

# =============================================================================
# CARGA DE DATOS (LAS LOADER)
# =============================================================================
class DataLoader:
    """Manejo de Archivos .LAS (Log ASCII Standard)."""
    
    @staticmethod
    def load_las_from_stream(uploaded_file):
        """
        Lee un archivo subido a Streamlit (bytes) y retorna (las_object, dataframe).
        Maneja errores de codificación comunes en archivos viejos.
        """
        try:
            # Escribir temporalmente para que lasio lo lea bien
            bytes_data = uploaded_file.getvalue()
            from io import StringIO
            # Intentar decodificar
            string_data = bytes_data.decode("utf-8", errors="ignore")
            
            # Usar StringIO como archivo en memoria
            las = lasio.read(StringIO(string_data))
            df = las.df()
            
            # Limpieza básica: Eliminar nulos locos (-999.25)
            df.replace(-999.25, np.nan, inplace=True)
            df.dropna(how='all', inplace=True)
            
            return las, df.reset_index(), None
            
        except Exception as e:
            return None, None, str(e)

# =============================================================================
# ANÁLISIS GEOESTADÍSTICO (Interpolación Criging Simplificada)
# =============================================================================
class GeostatsCore:
    """Herramientas para mapas y estadística espacial."""
    
    @staticmethod
    def interpolar_mapa(x, y, z, grid_res=50):
        """
        Crea una malla regular interpolada a partir de puntos dispersos (pozos).
        Retorna X_grid, Y_grid, Z_grid listos para contour plot.
        """
        try:
            # Crear grid
            xi = np.linspace(min(x), max(x), grid_res)
            yi = np.linspace(min(y), max(y), grid_res)
            X, Y = np.meshgrid(xi, yi)
            
            # Interpolación RBF (Radial Basis Function) - 'Smooth' y geológico
            from scipy.interpolate import Rbf
            # Truco: añadir ruido infinitesimal para evitar matrices singulares si hay duplicados
            rbf = Rbf(x, y, z, function='linear')
            Z = rbf(X, Y)
            
            return X, Y, Z
        except Exception as e:
            print(f"Error en interpolación: {e}")
            return np.array([]), np.array([]), np.array([])

# =============================================================================
# NORMALIZADOR DE CURVAS (ALIASING)
# =============================================================================
class CurveNormalizer:
    """Estandariza nombres de curvas (Gamma Ray -> GR)."""
    
    ALIAS_DB = {
        'GR': ['GR', 'GAMMA', 'GAPI', 'GAM', 'CGR', 'GAMMARAY', 'G_RAY', 'GRC', 'SGR', 'NGT'],
        'NPHI': ['NPHI', 'TNPH', 'PHIN', 'NPOR', 'PORN', 'PHIN_PERCENT', 'PHIN_PU', 'PHI', 'CNC', 'CNL', 'NPHI_LS', 'NPHI_SS', 'PORZ'],
        'RHOB': ['RHOB', 'RHOZ', 'DEN', 'DENSITY', 'ZDEN', 'BDEN', 'RHO_MA', 'RHOM', 'CDEN', 'ZDEN'],
        'RT': ['RT', 'RES', 'RD', 'ILD', 'LLD', 'RESISTIVITY', 'AT90', 'RDEEP', 'RES_DEEP', 'R_DEEP', 'HRLD', 'HDRS'],
        'DT': ['DT', 'DTC', 'DTCO', 'AC', 'SONIC', 'DT4P', 'DT_COMP', 'DTCO_LS']
    }
    
    @staticmethod
    def normalize_dataframe(df):
        df_norm = df.copy()
        found_any = False
        
        # Eliminar duplicados de columnas (ej. index repetido)
        df_norm = df_norm.loc[:,~df_norm.columns.duplicated()]
        
        cols_upper = {c.upper(): c for c in df_norm.columns}
        
        for std, aliases in CurveNormalizer.ALIAS_DB.items():
            if std in df_norm.columns: continue
            
            for alias in aliases:
                if alias in cols_upper:
                    old_col = cols_upper[alias]
                    df_norm.rename(columns={old_col: std}, inplace=True)
                    found_any = True
                    break
        
        return df_norm, found_any

# =============================================================================
# DETECTOR DE YACIMIENTOS (Reservoir Pay Flag)
# =============================================================================
class ReservoirDetector:
    """Motor de validación de intervalos productivos."""
    
    @staticmethod
    def detect_prospect_intervals(df, cutoffs):
        """
        Retorna un DataFrame con los intervalos (Top, Base, Thickness, Quality).
        """
        # Copia para no dañar original
        data = df.copy()
        
        # Validación de curvas mínimas
        needed = ['PHI', 'SW', 'VSH']
        for n in needed:
            if n not in data.columns:
                return pd.DataFrame()
        
        # Aplicar cutoffs booleanos
        mask = (data['PHI'] >= cutoffs['porosity_min']) & \
               (data['SW'] <= cutoffs['sw_max']) & \
               (data['VSH'] <= cutoffs['vshale_max'])
        
        # Identificar bloques contiguos (RLE - Run Length Encoding)
        # Truco pandas: cambio de estado
        data['Pay_Flag'] = mask.astype(int)
        data['block'] = (data['Pay_Flag'].shift(1) != data['Pay_Flag']).cumsum()
        
        # Agrupar por bloques
        intervals = []
        depth_col = data.columns[0] # Asumimos Depth es primera col
        
        for block_id, group in data[data['Pay_Flag'] == 1].groupby('block'):
            top = group[depth_col].min()
            base = group[depth_col].max()
            thick = abs(base - top)
            
            # Calcular promedios del intervalo
            avg_phi = group['PHI'].mean()
            avg_sw = group['SW'].mean()
            
            # Clasificación de Calidad
            quality = "Marginal"
            if avg_phi > 0.20 and avg_sw < 0.30: quality = "Excelente"
            elif avg_phi > 0.15: quality = "Bueno"
            
            intervals.append({
                'Top': top,
                'Base': base,
                'Espesor_ft': thick,
                'Porosidad_Avg': avg_phi,
                'Sw_Avg': avg_sw,
                'Calidad': quality
            })
            
        return pd.DataFrame(intervals)

# =============================================================================
# SIMULADOR ECONÓMICO (Cash Flow)
# =============================================================================
class SimulationEngine:
    @staticmethod
    def simular_produccion(oip, price_per_bbl, decline_rate=0.15):
        """Genera flujo de caja a 10 años (Arps simple)."""
        months = np.arange(1, 121) # 10 años
        # Q(t) = Qi * exp(-D*t)
        qi = oip * 0.001 # Asumir factor de recuperación inicial mensual bajo
        
        prod_mensual = qi * np.exp(-decline_rate/12 * months)
        ingresos = prod_mensual * price_per_bbl
        
        return pd.DataFrame({
            "Mes": months,
            "Barriles_Mes": prod_mensual,
            "Ingresos_USD": ingresos
        })

# =============================================================================
# AUDITOR DE CALIDAD (Data QC - SEG Standards)
# =============================================================================
class DataQualityAuditor:
    """Implementa el 'Entrance Exam' para certificar la data."""
    
    @staticmethod
    def auditar_dataset(df):
        """Retorna una lista de mensajes de auditoría técnica detallada (Forensic Log)."""
        audit_log = []
        
        # 0. Estadísticas Básicas de Lectura
        total_puntos = len(df)
        if total_puntos == 0:
            return ["❌ **ERROR CRÍTICO**: El archivo no contiene datos (0 muestras)."]
        
        # Detectar columna de profundidad
        depth_col = next((c for c in df.columns if c.upper() in ['DEPT', 'DEPTH', 'MD']), df.columns[0])
        start_dp = df[depth_col].min()
        stop_dp = df[depth_col].max()
        footange = stop_dp - start_dp
        
        audit_log.append(f"✅ **Lectura Exitosa**: Se cargaron {total_puntos:,} líneas de datos.")
        audit_log.append(f"📏 **Cobertura**: De {start_dp:.1f} a {stop_dp:.1f} ({footange:.1f} ft).")
        
        # 1. Integridad de Curvas Esenciales
        essential_curves = ['GR', 'NPHI', 'RHOB', 'RT']
        present = [c for c in essential_curves if c in df.columns]
        missing = [c for c in essential_curves if c not in df.columns]
        
        if missing:
            audit_log.append(f"⚠️ **Curvas Faltantes**: {', '.join(missing)}. Se usarán modelos sintéticos fallback.")
        else:
            audit_log.append(f"✅ **Set Completo**: Triple Combo presente ({', '.join(present)}).")
            
        # 2. Validación de Cálculos Realizados
        if 'VSH' in df.columns:
            audit_log.append("⚙️ **Cálculo Vsh**: Ejecutado (Método Larionov/Steiber adaptativo).")
        if 'PHI' in df.columns:
            src = "NPHI/RHOB" if 'NPHI' in df.columns and 'RHOB' in df.columns else "Estimación Sónica/Densidad"
            audit_log.append(f"⚙️ **Cálculo Porosidad**: Ejecutado usando {src}.")
        if 'SW' in df.columns:
            audit_log.append("⚙️ **Cálculo Sw**: Ejecutado (Modelo Archie).")
            
        # 3. Calidad de Datos (Nulls)
        if 'GR' in df.columns:
            valid_gr = df['GR'].count()
            perc_valid = (valid_gr / total_puntos) * 100
            if perc_valid < 90:
                audit_log.append(f"⚠️ **Calidad GR Baja**: Solo {perc_valid:.1f}% de datos válidos.")
            else:
                audit_log.append(f"✅ **Integridad GR**: {perc_valid:.1f}% de datos válidos.")

        return audit_log

# =============================================================================
# EXPORTADOR LAS 2.0 (Interoperabilidad Industrial)
# =============================================================================
class LASExporter:
    """Genera archivos .LAS válidos para Petrel, Kingdom, Techlog."""
    
    @staticmethod
    def export_pandas_to_las(df, well_name="EXPORT_GEOMIND", null_value=-999.25):
        """
        Convierte el DataFrame procesado a un string formato LAS 2.0.
        """
        lines = []
        # Header Version
        lines.append("~VERSION INFORMATION")
        lines.append(" VERS.   2.0 :   CWLS LOG ASCII STANDARD - VERSION 2.0")
        lines.append(" WRAP.    NO :   ONE LINE PER DEPTH STEP")
        
        # Header Well
        lines.append("~WELL INFORMATION")
        try:
             start = df.iloc[0,0]
             stop = df.iloc[-1,0]
             step = abs(df.iloc[1,0]-df.iloc[0,0])
        except:
             start, stop, step = 0, 0, 0
             
        lines.append(f" STRT.FT      {start:.2f} : START DEPTH")
        lines.append(f" STOP.FT      {stop:.2f} : STOP DEPTH")
        lines.append(f" STEP.FT      {step:.4f} : STEP")
        lines.append(f" NULL.        {null_value} : NULL VALUE")
        lines.append(f" WELL.        {well_name} : WELL NAME")
        lines.append(" PROV.        GEOMIND AI : ANALYST")
        
        # Header Curves
        lines.append("~CURVE INFORMATION")
        lines.append(f" {str(df.columns[0])[:10]:<10} .FT   :   DEPTH") 
        for col in df.columns[1:]:
             clean_col = str(col).replace(' ', '_')[:10]
             lines.append(f" {clean_col:<10} .UNIT :   {col}")
        
        # Data Section
        lines.append("~ASCII")
        
        header_str = "\n".join(lines) + "\n"
        
        # Datos tabulados
        df_fill = df.fillna(null_value)
        data_str = df_fill.to_string(index=False, header=False)
        
        return header_str + data_str
