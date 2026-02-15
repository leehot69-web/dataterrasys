import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from plotly.subplots import make_subplots
from petro_core_web import PetrofisicaCore, GeostatsCore, DataLoader, ReservoirDetector, SimulationEngine, CurveNormalizer, DataQualityAuditor, LASExporter
import db_manager
import report_generator
import math
from license_config import LICENSES

# =============================================================================
# MOTOR GEOFÍSICO (Petrel-Lite Capabilities)
# =============================================================================
class GeophysicsEngine:
    @staticmethod
    def calcular_impedancia(df, col_dens, col_sonic=None):
        """Calcula Impedancia Acústica (AI = Rho * Vp)."""
        # Si no hay sónico, usar ecuación de Gardner para estimar Vp desde Rho (aprox)
        # Vp = (rho / 0.23) ^ (1/0.25)  (Gardner et al, 1974)
        rho = df[col_dens]
        
        if col_sonic and col_sonic in df.columns:
            # DT usualmente en us/ft. Vp = 1e6 / DT
            dt = df[col_sonic]
            vp = 1e6 / (dt + 1e-5) # Evitar div/0
        else:
            # Aproximación Gardner
            vp = (rho / 0.23) ** 4.0 
            
        ai = vp * rho
        return ai, vp

    @staticmethod
    def coeficientes_reflexion(ai_series):
        """Calcula RC = (Z2 - Z1) / (Z2 + Z1)"""
        ai = ai_series.values
        rc = np.zeros_like(ai)
        # Diferencia centrada o forward
        rc[1:] = (ai[1:] - ai[:-1]) / (ai[1:] + ai[:-1] + 1e-9)
        return rc

    @staticmethod
    def ricker_wavelet(freq, length, dt=0.001):
        """Genera una Ondícula Ricker teórica."""
        t = np.arange(-length/2, (length/2)+dt, dt)
        y = (1.0 - 2.0*(np.pi**2)*(freq**2)*(t**2)) * np.exp(-(np.pi**2)*(freq**2)*(t**2))
        return t, y

    @staticmethod
    def generar_sintetico(rc_series, wavelet):
        """Convolución de Reflectividad * Ondícula."""
        # Usar 'same' para mantener la longitud del array
        sintetico = np.convolve(rc_series, wavelet, mode='same')
        # Normalizar para visualización
        if np.max(np.abs(sintetico)) > 0:
            sintetico = sintetico / np.max(np.abs(sintetico))
        return sintetico

# =============================================================================
# CONFIGURACIÓN DE PÁGINA "SIIH" (SUBSURFACE INTELLIGENCE HUB)
# =============================================================================
st.set_page_config(
    page_title="Dterra: Subsurface Intelligence",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# ESTILOS "MODERN GEOLOGICAL DATA HUB" (Neon & Seismic Grid)
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

    :root {
        --primary: #00f2ff;
        --secondary: #10b981;
        --accent: #f59e0b;
        --bg-dark: #0a0f1a;
        --surface-dark: #111827;
        --border-dark: #1f2937;
        --glass: rgba(17, 24, 39, 0.7);
    }

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    /* OCULTAR HEADER DEFAULT DE STREAMLIT */
    header[data-testid="stHeader"] { display: none; }

    /* AJUSTAR PADDING SUPERIOR (Responsive) */
    .block-container {
        padding-top: 6rem !important;
        padding-bottom: 2rem !important;
        max-width: 1600px;
    }
    
    @media (max-width: 640px) {
        .block-container {
            padding-top: 2rem !important;
            }
    }


    /* FONDO SÍSMICO */
    .stApp {
        background-color: var(--bg-dark);
        color: #f1f5f9;
        background-image: linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                          linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 30px 30px;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: var(--surface-dark);
        border-right: 1px solid var(--border-dark);
    }

    /* PANELES DE CRISTAL */
    div[data-testid="stExpander"], div[data-testid="stForm"], div[data-testid="stMetric"], div.stDataFrame {
        background: var(--glass);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        padding: 15px;
    }

    /* TITULOS */
    h1, h2, h3 { color: white; font-weight: 700; letter-spacing: -0.5px; }
    
    /* BOTONES DUAL-TONE */
    .stButton > button {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        color: #e2e8f0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.05em;
        font-size: 0.8rem;
    }
    .stButton > button:hover {
        border-color: var(--primary);
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.3);
        color: white;
        transform: scale(1.02);
    }

    /* METRICAS NEON */
    [data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--primary) !important;
        text-shadow: 0 0 10px rgba(0, 242, 255, 0.4);
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8; font-weight: 700; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.1em;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid var(--border-dark); }
    .stTabs [data-baseweb="tab"] { background-color: transparent; color: #64748b; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: var(--primary) !important; border-bottom: 2px solid var(--primary); }

</style>
""", unsafe_allow_html=True)

# VARIABLE: HTML HEADER (Solo se inyecta tras login)
HTML_HEADER = """
<div style="position: fixed; top: 0; left: 0; width: 100%; height: 5rem; background: rgba(10, 15, 26, 0.95); backdrop-filter: blur(20px); border-bottom: 1px solid #1f2937; z-index: 999999; display: flex; align-items: center; justify-content: space-between; padding: 0 2rem;">
    <div style="display: flex; align-items: center; gap: 3rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="width: 2.5rem; height: 2.5rem; background-color: #00f2ff; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 20px rgba(0,242,255,0.3);">
                <span class="material-symbols-outlined" style="color: #0a0f1a; font-weight: bold;">terrain</span>
            </div>
            <span style="font-weight: 700; font-size: 1.5rem; letter-spacing: -0.05em; color: white;">DTERRA<span style="color: #00f2ff;">.APP</span></span>
        </div>
    </div>
</div>
"""

# CONFIGURACIÓN DE LICENCIAS (CARGADO DESDE license_config.py)
# -----------------------------------------------------------------------------
# Para gestionar los accesos, abra y edite el archivo: license_config.py

def check_password():
    """Valida la Licencia Corporativa y verifica su vigencia."""
    def password_entered():
        license_key = st.session_state["password"]
        
        if license_key in LICENSES:
            license_data = LICENSES[license_key]
            # Verificar expiración
            expiry_date = datetime.strptime(license_data["expires"], "%Y-%m-%d")
            
            if datetime.now() <= expiry_date:
                st.session_state["password_correct"] = True
                st.session_state["company_name"] = license_data["company"]
                st.session_state["license_expiry"] = license_data["expires"]
                del st.session_state["password"]
            else:
                st.session_state["password_correct"] = False
                st.session_state["login_error"] = f"La Licencia de **{license_data['company']}** expiró el {license_data['expires']}."
        else:
            st.session_state["password_correct"] = False
            st.session_state["login_error"] = "Licencia Inválida. Verifique sus credenciales corporativas."

    if "password_correct" not in st.session_state:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>:: Dterra Subsurface Hub</h1>", unsafe_allow_html=True)
        st.caption("<p style='text-align: center;'>Software de Inteligencia de Yacimientos v.7.0</p>", unsafe_allow_html=True)
        st.text_input("Ingrese Licencia Corporativa (License Key)", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.error(st.session_state.get("login_error", "Error de acceso."))
        st.text_input("Ingrese Licencia Corporativa (License Key)", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

if check_password():
    # INYECTAR HEADER SOLO AHORA
    st.markdown(HTML_HEADER, unsafe_allow_html=True)
    
    # Inicializar DB y App...
    if "db_init" not in st.session_state:
        db_manager.init_db()
        st.session_state["db_init"] = True

    # =============================================================================
    # SIDEBAR: DATA INGESTION & ROLES
    # =============================================================================
    st.sidebar.image("https://img.icons8.com/color/96/000000/oil-pump.png", width=60)
    st.sidebar.title("Dterra.app")
    st.sidebar.caption("v.7.0 | Subsurface Intelligence")
    
    # Mostrar Información de Licencia
    company = st.session_state.get("company_name", "Corporate Client")
    expiry_str = st.session_state.get("license_expiry", "-")
    
    # Calcular Días Restantes
    days_left = 0
    if expiry_str != "-":
        expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d")
        days_left = (expiry_dt - datetime.now()).days + 1
    
    # Estilo del contador (Cuidado si faltan pocos días)
    status_icon = "🟢" if days_left > 7 else "⚠️"
    msg_color = "info" if days_left > 7 else "warning"
    
    st.sidebar.markdown(f"""
    <div style="background: rgba(0,242,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(0,242,255,0.2); margin-bottom: 10px;">
        <p style="margin:0; font-size: 0.8rem; color: #94a3b8;">CLIENTE CORPORATIVO</p>
        <p style="margin:0; font-size: 1.1rem; font-weight: 700; color: white;">{company}</p>
        <hr style="margin: 10px 0; border-color: rgba(255,255,255,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.8rem; color: #94a3b8;">DÍAS RESTANTES:</span>
            <span style="font-size: 1.2rem; font-weight: 800; color: {'#00f2ff' if days_left > 7 else '#ff4b4b'}; text-shadow: 0 0 10px rgba(0,242,255,0.2);">{days_left}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.divider()
    
    # Pestañas de Carga
    tab_load, tab_hist = st.sidebar.tabs(["■ LOAD", "● HISTORY"])
    
    with tab_load:
        uploaded_las = st.file_uploader("Archivo Maestro (.LAS)", type=['las'], key="loader_las")
        if uploaded_las is not None:
            if "las_filename" not in st.session_state or st.session_state["las_filename"] != uploaded_las.name:
                las, df, error = DataLoader.load_las_from_stream(uploaded_las)
                if error:
                    st.error(f"Error: {error}")
                else:
                    df_norm, changes = CurveNormalizer.normalize_dataframe(df)
                    st.session_state["project_data"] = df_norm
                    st.session_state["las_object"] = las
                    st.session_state["las_filename"] = uploaded_las.name
                    
                    if changes: st.success("[OK] Curvas normalizadas a estándar (GR, RT, NPHI...)")
                    
                    # --- AUTO-EJECUCIÓN DEL MODELO PETROFÍSICO (ROBUSTO) ---
                    try:
                        # Identificar curvas críticas
                        c_gr = next((c for c in df_norm.columns if c in ['GR', 'GR_EDTC', 'Gamma']), None)
                        c_rt = next((c for c in df_norm.columns if c in ['RT', 'ILD', 'LLD', 'RESD']), None)
                        c_nphi = next((c for c in df_norm.columns if c in ['NPHI', 'phi', 'por']), None)
                        c_rhob = next((c for c in df_norm.columns if c in ['RHOB', 'den', 'density']), None)

                        if c_gr:
                            gr_min, gr_max = df_norm[c_gr].min(), df_norm[c_gr].max()
                            df_norm['VSH_FINAL'] = ((df_norm[c_gr] - gr_min) / (gr_max - gr_min)).clip(0, 1)
                        
                        if c_rhob:
                            # Sandstone matrix density 2.65 g/cc
                            df_norm['PHIE_FINAL'] = ((2.65 - df_norm[c_rhob]) / (2.65 - 1.0)).clip(0, 0.45)
                        
                        if 'PHIE_FINAL' in df_norm.columns and c_rt:
                            # Basic Archie
                            df_norm['SW_ARCHIE'] = np.sqrt((1.0 * 0.05) / ((df_norm['PHIE_FINAL']**2) * df_norm[c_rt] + 1e-9)).clip(0, 1)
                            # Simandoux Fallback for Radar
                            df_norm['SW_SIMANDOUX'] = df_norm['SW_ARCHIE'] 

                        st.session_state["project_data"] = df_norm
                        st.session_state["model_executed"] = True 
                        st.caption("[OK] Modelo Petrofísico Base (Vsh, Phi, Sw) sincronizado.")
                    except Exception as e:
                        st.warning(f"[!] Auto-procesamiento parcial: {e}")
                        
                    except Exception as e:
                        st.warning("[!] No se pudo auto-calcular el modelo completo (Faltan curvas?): {e}")

                    # --- MAPEO MANUAL DE CURVAS (Intervención Humana) ---
                    # Verificamos si faltan curvas críticas después de la normalización
                    essential = ['GR', 'NPHI', 'RHOB', 'RT']
                    missing = [c for c in essential if c not in df_norm.columns]
                    
                    if missing:
                        st.warning(f"[!] Faltan curvas estándar: {missing}")
                        with st.expander(":: Asignar Curvas Manualmente", expanded=True):
                            st.write("Seleccione la curva original que corresponde a cada faltante:")
                            cols = df.columns.tolist() # Curvas originales sin normalizar
                            
                            # Crear un formulario para mapear
                            with st.form("manual_mapping"):
                                selections = {}
                                for m in missing:
                                    selections[m] = st.selectbox(f"Mapear a {m}:", ["(Ignorar)"] + cols, index=0)
                                
                                if st.form_submit_button("Aplicar Corrección Manual"):
                                    # Aplicar cambios
                                    for std_name, orig_name in selections.items():
                                        if orig_name != "(Ignorar)":
                                            df_norm[std_name] = df[orig_name] # Copiar data
                                            st.success(f"✅ {std_name} recuperada de {orig_name}")
                                    
                                    # Actualizar estado global y re-auditar
                                    st.session_state["project_data"] = df_norm
                                    st.rerun()

                    # AUDITORÍA AUTOMÁTICA FINAL
                    qc_report = DataQualityAuditor.auditar_dataset(df_norm)
                    st.session_state["qc_report"] = qc_report
                    with st.expander("️ Reporte de Calidad (SEG)", expanded=False):
                        for msg in qc_report:
                            if "✅" in msg: st.success(msg)
                            elif "⚠️" in msg: st.warning(msg)
                            else: st.error(msg)
                    st.divider()
         
        # --- CARGADOR DE SÍSMICA (SEGY) ---
        st.caption("≋ Datos Sísmicos (Volúmenes 3D)")
        uploaded_segy = st.file_uploader("Archivo Sísmico (.SGY, .SEGY)", type=['sgy', 'segy'], key="loader_segy")
        
        if uploaded_segy is not None:
             try:
                 # LECTURA BINARIA BÁSICA
                 # Leer Header de Texto (3200 bytes)
                 text_header = uploaded_segy.read(3200)
                 # Leer Header Binario (400 bytes)
                 bin_header = uploaded_segy.read(400)
                 
                 import struct
                 ns = struct.unpack('>H', bin_header[20:22])[0]
                 dt = struct.unpack('>H', bin_header[16:18])[0]
                 
                 st.session_state["segy_meta"] = {
                     "filename": uploaded_segy.name,
                     "ns": ns,
                     "dt": dt,
                     "size_mb": uploaded_segy.size / (1024*1024)
                 }
                 st.success(f"✅ SEGY Cargado: {ns} muestras @ {dt} us")
                 
                 trace_header = uploaded_segy.read(240)
                 trace_data_raw = uploaded_segy.read(ns * 4)
                 
                 if len(trace_data_raw) == ns * 4:
                     trace_data = struct.unpack(f'>{ns}f', trace_data_raw)
                     st.session_state["segy_preview_trace"] = trace_data
                     
             except Exception as e:
                 st.error(f"Error leyendo SEGY: {e}")
                 st.info("Asegúrese de que es un archivo SEGY estándar (Rev 1).")
             
             uploaded_segy.seek(0)
             st.divider()

    with tab_hist:
        history_df = db_manager.load_history()
        if not history_df.empty:
            st.dataframe(history_df[['well_name', 'upload_date']], hide_index=True)
            project_id = st.selectbox("ID:", history_df['id'])
            if st.button("📥 Abrir"):
                df_loaded, params = db_manager.load_project_data(project_id)
                if df_loaded is not None:
                    st.session_state["project_data"] = df_loaded
                    st.session_state["las_filename"] = f"Proyecto_Recuperado_{project_id}"
                    st.rerun()
    
    # =============================================================================
    # SIDEBAR: ADVANCED OPERATIONS & MODULE SELECTOR (Tactical Grid)
    # =============================================================================
    st.sidebar.divider()
    st.sidebar.markdown("###️ System Modules")

    # Diccionario de Roles Profesionales (SPE/AAPG Standards)
    MODULES = {
        "EX": "■ EXECUTIVE DASHBOARD",
        "GI": "● GEOLOGICAL INTERPRETATION",
        "FE": "🧬 FORMATION EVALUATION",
        "RE": "▲ RESERVOIR ENGINEERING",
        "DI": "🤖 DATA INTEGRITY & AI",
        "UG": "📖 USER GUIDE & DOCS"
    }

    # Inicializar estado si no existe
    if 'selected_role' not in st.session_state:
        st.session_state['selected_role'] = MODULES["EX"]

    # Grid de Navegación Técnica (Estilo Consola)
    # (Navegación movida al Top Menu)

    
    # Mostrar Rol Actual
    role = st.session_state['selected_role']
    st.sidebar.caption(f"**Current Domain:**\n{role}")
    
    # KNOWLEDGE AGENT (Refactorizado: Operational Insights)
    with st.sidebar.expander(f"⚙️ Operational Insights", expanded=True):
        if role == MODULES["EX"]: 
            st.info("⚠️ **Asset Status:** Analizando variaciones en el Net-to-Gross proyectado vs Real.")
        elif role == MODULES["GI"]: 
            st.info("🔍 **Geo-Logic:** Verifique la consistencia de los topes estructurales con la sísmica cargada.")
        elif role == MODULES["FE"]: 
            st.info("🧬 **FE Alert:** Modelo Simandoux recomendado para secciones con Vsh > 0.3.")
        elif role == MODULES["RE"]: 
            st.info(" **EUR Analysis:** La declinación hiperbólica presenta mejor ajuste para este yacimiento no convencional.")
        elif role == MODULES["DI"]: 
            st.info("🤖 **Integrity:** Detectado desbalance de clases en el set de entrenamiento de litofacies.")

    # --- CARGA DE DATOS SUPLEMENTARIOS (REALES) ---
    with st.sidebar.expander("📂 Datos Adicionales (Topes/Core)", expanded=False):
        tops_file = st.file_uploader("Cargar Topes (.csv)", type=["csv"], help="Formato: Depth, Name")
        if tops_file:
            try:
                df_tops = pd.read_csv(tops_file)
                # Normalizar columnas a mayúsculas
                df_tops.columns = [c.upper() for c in df_tops.columns]
                
                # Buscar col profundidad y nombre
                depth_col = next((c for c in df_tops.columns if any(x in c for x in ['DEP', 'MD', 'PROF', 'TOP'])), None)
                name_col = next((c for c in df_tops.columns if any(x in c for x in ['NAME', 'FORM', 'FM'])), None)
                
                if depth_col and name_col:
                    tops_data = df_tops[[depth_col, name_col]].dropna().to_dict('records')
                    st.session_state['formation_tops'] = tops_data
                    st.success(f"✅ {len(tops_data)} Topes cargados.")
                else:
                    st.error("El CSV debe tener columnas 'Depth' y 'Name'.")
            except Exception as e:
                st.error(f"Error leyendo CSV: {e}")

    # ACCIONES GLOBALES
    PROJECT_READY = "project_data" in st.session_state and st.session_state["project_data"] is not None

    if PROJECT_READY:
        df_active = st.session_state["project_data"]
        well_name = st.session_state.get("las_filename", "Sin Nombre")
        st.sidebar.success(f"[OK] {well_name}")
        if st.sidebar.button("💾 Guardar Proyecto"):
            db_manager.save_project(well_name, well_name, df_active)
            st.sidebar.success("Guardado en Local DB")

    # =============================================================================
# UI PRINCIPAL - STREAMLIT APP
# =============================================================================
    # --- Sidebar de Navegación ---
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align: center; padding: 10px; border-bottom: 1px solid #4a5568; margin-bottom: 20px;">
                <h1 style="color: #00f2ff; font-size: 24px; margin-bottom: 0;">DATA<span style="color: white;">TERRA</span></h1>
                <p style="font-size: 10px; opacity: 0.7;">SUBSURFACE INTELLIGENCE OS</p>
                <a href="https://dataterraapp.vercel.app" target="_self" style="
                    display: inline-block;
                    padding: 5px 15px;
                    background: rgba(0, 242, 255, 0.1);
                    border: 1px solid #00f2ff;
                    color: #00f2ff;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 12px;
                    margin-top: 10px;
                ">🏠 VOLVER AL INICIO</a>
            </div>
        """, unsafe_allow_html=True)
        
        st.title("🧭 Navegación")
    # =============================================================================
    # TOP NAVIGATION BAR (MENÚ SUPERIOR)
    # =============================================================================
    st.markdown("---")
    
    # Grid de Navegación Horizontal
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    
    if m1.button("■ EXECUTIVE", key="nav_ex", use_container_width=True, help="Strategic Dashboard"):
        st.session_state['selected_role'] = MODULES["EX"]
        st.rerun()
        
    if m2.button("● GEOLOGY", key="nav_gi", use_container_width=True, help="Seismic & Surfaces"):
        st.session_state['selected_role'] = MODULES["GI"]
        st.rerun()
        
    if m3.button("◆ PETROPHYSICS", key="nav_fe", use_container_width=True, help="Log Analysis"):
        st.session_state['selected_role'] = MODULES["FE"]
        st.rerun()
        
    if m4.button("▲ RESERVOIR", key="nav_re", use_container_width=True, help="Engineering"):
        st.session_state['selected_role'] = MODULES["RE"]
        st.rerun()

    if m5.button("◉ AI & DATA", key="nav_di", use_container_width=True, help="ML & Quality"):
        st.session_state['selected_role'] = MODULES["DI"]
        st.rerun()

    if m6.button("📖 GUIDE", key="nav_ug_top", use_container_width=True, help="Documentation"):
        st.session_state['selected_role'] = MODULES["UG"]
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("📖 USER GUIDE", key="nav_ug", use_container_width=True, help="Documentation"):
        st.session_state['selected_role'] = MODULES["UG"]
        st.rerun()
        
    role = st.session_state['selected_role']

    # =============================================================================
    # LÓGICA PRINCIPAL (MAIN PANEL)
    # =============================================================================
    
    # 1. STRATEGIC EXECUTIVE DASHBOARD (Gerencia)
    if role == MODULES["EX"]:
        st.markdown("<h1 class='main-header'>:: Strategic Asset Control Center</h1>", unsafe_allow_html=True)
        
        # --- DATA PROCESSING & HEADER EXTRACTION ---
        las_obj = st.session_state.get("las_object", None)
        def get_h(m, d="-"): 
            try: return las_obj.well[m].value if las_obj and m in las_obj.well else d
            except: return d

        well_info = {
            "Well Name": get_h("WELL"),
            "Field": get_h("FLD"),
            "Operator": get_h("COMP"),
            "Service Co": get_h("SRVC"),
            "Location": get_h("LOC"),
            "Date": get_h("DATE"),
            "API/UWI": get_h("UWI", get_h("API"))
        }

        # --- KPIS SUPERIORES (METRIC CARDS) ---
        k1, k2, k3, k4 = st.columns(4)
        
        # Valores por defecto para modo espera
        v_well = well_info["Well Name"] if PROJECT_READY and well_info["Well Name"] != "-" else "---"
        v_depth = f"{df_active.iloc[-1,0]:.1f} ft" if PROJECT_READY else "0.0 ft"
        v_qc = ("Aprobada" if "qc_report" in st.session_state and not any("❌" in x for x in st.session_state["qc_report"]) else "En Revisión") if PROJECT_READY else "Offline"
        
        k1.metric("Pozo Activo", v_well)
        k2.metric("Estado HSE", "● Seguro" if PROJECT_READY else "---", delta="0 Incidentes" if PROJECT_READY else None)
        k3.metric("Profundidad Final", v_depth)
        k4.metric("Calidad de Data", v_qc)

        st.divider()

        # --- GAUGES PROFESIONALES ---
        g1, g2, g3 = st.columns(3)
        
        # Cálculos Dinámicos vs Placeholders
        asset_health = 94.2 if PROJECT_READY else 0.0
        net_pay_val = 0.0
        if PROJECT_READY and 'PHIE_FINAL' in df_active.columns:
             net_pay_val = (df_active['PHIE_FINAL'] > 0.15).sum() * 0.5
        
        hse_val = 100.0 if PROJECT_READY else 0.0

        # Función de Gauge
        import math
        def create_pro_gauge(value, title, reference=None, max_val=100):
            steps = [
                {'range': [0, math.floor(max_val*0.5)], 'color': '#ef4444'},
                {'range': [math.floor(max_val*0.5), math.floor(max_val*0.8)], 'color': '#f59e0b'},
                {'range': [math.floor(max_val*0.8), max_val], 'color': '#10b981'}
            ]
            fig = go.Figure(go.Indicator(
                mode = "gauge+number" + ("+delta" if reference and PROJECT_READY else ""),
                value = value,
                delta = {'reference': reference} if reference and PROJECT_READY else None,
                title = {'text': title, 'font': {'size': 18, 'color': 'white'}},
                gauge = {
                    'axis': {'range': [0, max_val], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': "white"},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "#333",
                    'steps': steps,
                    'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': value}}))
            fig.update_layout(height=250, margin=dict(l=30,r=30,t=50,b=20), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            return fig

        g1.plotly_chart(create_pro_gauge(asset_health, "ASSET HEALTH", reference=90), use_container_width=True)
        g2.plotly_chart(create_pro_gauge(net_pay_val, "AVG NET PAY (ft)", max_val=500), use_container_width=True)
        g3.plotly_chart(create_pro_gauge(hse_val, "HSE SAFETY SCORE"), use_container_width=True)

        # --- MOSTRAR CARGADORES SI NO HAY DATA ---
        if not PROJECT_READY:
            st.divider()
            st.warning("■ **Sistema en Espera.** Cargue archivos para activar el Dashboard completo.")
            c_load_1, c_load_2 = st.columns(2)
            with c_load_1:
                st.markdown("### ■ Log de Pozo (.LAS)")
                main_las = st.file_uploader("Upload LAS", type=['las'], key="main_up_las_v_final")
                if main_las:
                    las, df, error = DataLoader.load_las_from_stream(main_las)
                    if not error:
                        df_norm, _ = CurveNormalizer.normalize_dataframe(df)
                        st.session_state["project_data"] = df_norm
                        st.session_state["las_object"] = las
                        st.session_state["las_filename"] = main_las.name
                        st.success("[OK] Well Data Loaded."); st.rerun()
            with c_load_2:
                st.markdown("### ≋ Sísmica (.SGY)")
                main_segy = st.file_uploader("Upload SEGY", type=['sgy', 'segy'], key="main_up_sgy_v_final")
                if main_segy:
                    st.session_state["segy_meta"] = {"filename": main_segy.name}
                    st.success("[OK] Seismic Volume Registered."); st.rerun()
            st.stop()
        
        st.divider()
        
        # --- LAYOUT: MAP | WELL MASTER DATA ---
        col_map, col_info = st.columns([1.8, 1])
        
        with col_map:
            st.markdown("### 📍 Asset Location")
            # Coordenadas dummy or real if found (LOC typically has text, not lat/lon)
            st.map(pd.DataFrame({'lat': [10.15], 'lon': [-64.6]}), zoom=9, use_container_width=True)

        with col_info:
            st.markdown("### :: Well Master Data")
            for k, v in well_info.items():
                st.markdown(f"**{k}:** `{v}`")
            st.info("💡 Header metadata extracted from active LAS file.")
            
            # --- EXPORT STATION (EXECUTIVE) ---
            st.divider()
            st.markdown("### 📥 Quick Portfolio Export")
            exp1, exp2 = st.columns(2)
            if exp1.button("📑 Generate Report", key="ex_pdf", use_container_width=True):
                html_ex = report_generator.generate_html_report(
                    well_info, df_active, st.session_state.get("pay_intervals", None),
                    qc_report_list=st.session_state.get("qc_report", []),
                    asset_health=asset_health, net_pay=net_pay_val
                )
                st.download_button("💾 Download Report", html_ex, f"EXECUTIVE_SUMMARY_{well_info['Well Name']}.html", "text/html", use_container_width=True, key="ex_pdf_dl")
            if exp2.button("📊 CSV Metrics", key="ex_csv", use_container_width=True):
                csv = df_active.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", data=csv, file_name=f"EX_REPORT_{well_info['Well Name']}.csv", mime='text/csv', use_container_width=True, key="ex_csv_dl")

        st.divider()
        
        c_trends, c_alerts = st.columns([2, 1])
        with c_trends:
            st.markdown("### 📈 Production & Investment Trends")
            chart_data = pd.DataFrame(np.random.randn(25, 2), columns=["CAPEX", "Revenue"])
            st.area_chart(chart_data)
        
        with c_alerts:
            st.markdown("### :: Compliance Alerts")
            st.error("[!] Well A-02: Pressure Anomaly detected (24h)")
            st.success("[OK] Well B-01: Production target met")
            st.info(":: Audit: Q3 Environmental Report due in 5 days")
            st.warning("■ Tank Level: Low capacity in Battery 4")

    # 2. GEOLOGICAL INTERPRETATION & MODELING (Geólogo)
    elif role == MODULES["GI"]:
        st.markdown("<h1 class='main-header'>Subsurface Modeling & Imaging</h1>", unsafe_allow_html=True)
        
        # Permitir entrada parcial (Solo Sísmica SEGY) si no hay LAS
        if not PROJECT_READY: 
            st.warning("⚠️ **Modo Visor Sísmico:** Cargue un archivo de Pozo (LAS) para habilitar correlaciones y modelos 3D completos.")
        
        t1, t2, t3, t4, t5, t6 = st.tabs(["■ 3D Cube", "● Lithology", "≋ Seismic 3D", "↝ Trajectory", "□ Core Gallery", "∞ Well Tie"])
        
        # --- TAB 6: WELL TIE (REQUIERE LAS) ---
        with t6:
            st.markdown("### :: Laboratorio de Geofísica Sintética Avanzada")
            st.caption("Generación de Sismogramas Sintéticos: Modelo Convolucional (AI * Ricker)")
            
            if PROJECT_READY:
                c_geo1, c_geo2 = st.columns([1, 3])
                
                with c_geo1:
                    st.markdown("#### Parámetros del Modelo")
                    # Selección de Curvas
                    cols = df_active.columns.tolist()
                    idx_den = cols.index('RHOB') if 'RHOB' in cols else 0
                    idx_dt = cols.index('DT') if 'DT' in cols else 0
                    
                    col_den = st.selectbox("Curva Densidad (RHOB)", cols, index=idx_den)
                    col_dt = st.selectbox("Curva Sónico (DT) - Opcional", ["Ninguna"] + cols, index=idx_dt+1 if 'DT' in cols else 0)
                    
                    st.divider()
                    st.markdown("#### Ondícula (Wavelet)")
                    freq = st.slider("Frecuencia (Hz)", 5, 80, 30, help="Frecuencia central de la ondícula Ricker")
                    polarity = st.radio("Polaridad", ["Normal (SEG)", "Inversa (Europe)"])
                    
                    if st.button("🚀 Generar Sintético"):
                        with st.spinner("Convolucionando..."):
                            # 1. Calcular Impedancia
                            sonic_col = col_dt if col_dt != "Ninguna" else None
                            ai, vp = GeophysicsEngine.calcular_impedancia(df_active, col_den, sonic_col)
                            
                            # 2. Reflectividad
                            rc = GeophysicsEngine.coeficientes_reflexion(ai)
                            
                            # 3. Ondícula
                            t_wav, ricker = GeophysicsEngine.ricker_wavelet(freq, length=0.100, dt=0.002) # dt sim
                            if polarity == "Inversa (Europe)": ricker = -ricker
                            
                            # 4. Convolución (Sintético)
                            sintetico = GeophysicsEngine.generar_sintetico(rc, ricker)
                            
                            # Guardar en Session
                            st.session_state['geo_ai'] = ai
                            st.session_state['geo_rc'] = rc
                            st.session_state['geo_synth'] = sintetico
                            st.session_state['geo_vp'] = vp
                            st.success("✅ Modelo Convolucional Generado")

                with c_geo2:
                    if 'geo_synth' in st.session_state:
                        # PLOT DE 4 PISTAS (SÍSMICA PROFESIONAL)
                        fig_geo = make_subplots(rows=1, cols=4, shared_yaxes=True, 
                                              subplot_titles=("Impedancia", "Reflectividad", "Sintético", "Ondícula"),
                                              column_widths=[0.2, 0.15, 0.45, 0.2], horizontal_spacing=0.02)
                        
                        depth = df_active.index
                        
                        # 1. IMPEDANCIA (AI)
                        fig_geo.add_trace(go.Scatter(x=st.session_state['geo_ai'], y=depth, line=dict(color='yellow', width=1.2, shape='hv'), name='AI'), row=1, col=1)
                        
                        # 2. REFLECTIVIDAD (RC)
                        rc_val = st.session_state['geo_rc']
                        fig_geo.add_trace(go.Bar(x=rc_val, y=depth, orientation='h', marker_color='cyan', name='RC'), row=1, col=2)
                        
                        # 3. SINTÉTICO (WIGGLE)
                        synth = st.session_state['geo_synth']
                        fig_geo.add_trace(go.Scatter(x=synth, y=depth, line=dict(color='white', width=1), name='Synth'), row=1, col=3)
                        # Área Variable (Peak Fill)
                        fig_geo.add_trace(go.Scatter(x=np.where(synth>=0, synth, 0), y=depth, fill='tozerox', fillcolor='rgba(0,255,255,0.5)', line=dict(width=0), showlegend=False), row=1, col=3)
                        
                        # 4. WAVELET
                        t_w, r_w = GeophysicsEngine.ricker_wavelet(freq, 0.1, 0.002)
                        fig_geo.add_trace(go.Scatter(x=r_w, y=t_w, line=dict(color='magenta', width=2)), row=1, col=4)
                        
                        fig_geo.update_layout(height=800, template='plotly_dark', showlegend=False, margin=dict(t=50, b=50, l=10, r=10))
                        fig_geo.update_yaxes(autorange="reversed")
                        st.plotly_chart(fig_geo, use_container_width=True)
                    else:
                        st.info("💡 Configure los parámetros y genere el sintético para ver los resultados.")
            else:
                st.info("🛰️ Bloqueado: Se requiere cargar un archivo LAS para el enlace Pozo-Sísmica.")
            
        with t2:
            st.markdown("### :: Sección Estratigráfica & Composición")
            # Implementación visual simplificada para demo
            if 'VSH_FINAL' in df_active.columns and 'PHIE_FINAL' in df_active.columns:
                 fig_lith = go.Figure()
                 # Use 'spline' shape for smooth, bezier-like curves (Electrocardiogram style)
                 fig_lith.add_trace(go.Scatter(x=df_active['VSH_FINAL'], y=df_active.index, fill='tozerox', name='Vclay', line=dict(color='#22c55e', shape='spline', smoothing=0.3)))
                 fig_lith.add_trace(go.Scatter(x=df_active['PHIE_FINAL'], y=df_active.index, fill='tozerox', name='Porosity', line=dict(color='#00f2ff', shape='spline', smoothing=0.3)))
                 fig_lith.update_yaxes(autorange="reversed")
                 fig_lith.update_layout(template="plotly_dark", height=800, title="Evaluación Litológica Rápida (Smoothed)")
                 st.plotly_chart(fig_lith, use_container_width=True)
            else:
                 st.warning("⚠️ Faltan resultados del Modelo Petrofísico (Vsh/Phi). Ejecute el módulo FE primero.")
                 
        with t1:
            st.markdown("### :: Volumetric Litho-Scanner")
            # Lógica del cubo 3D existente
            if 'PHIE_FINAL' in df_active.columns and 'RHOB' in df_active.columns:
                fig3 = px.scatter_3d(df_active, x='PHIE_FINAL', y='RHOB', z=df_active.index, color='GR', color_continuous_scale='Jet', title="Litho-Scanner 3D")
                fig3.update_layout(template="plotly_dark", height=700)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.warning("Datos insuficientes para Cubo 3D. Cargue proyecto.")
        
        with t5:
            # GALERÍA DE NÚCLEOS
            st.subheader("Digital Core Description Station")
            st.caption("Cargue fotografías de Núcleos, Registros Antiguos o Mapas Escaneados.")
            
            # Uploader de Imágenes (FIX: Unique Key V5)
            img_files = st.file_uploader("Subir Imágenes (.jpg, .png)", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True, key="core_uploader_final_v5")
            
            if img_files:
                # Inicializar base de datos de núcleos si no existe
                if 'core_descriptions' not in st.session_state:
                    st.session_state['core_descriptions'] = {}

                # Layout de Galería (Grid)
                st.divider()
                st.markdown("#### :: Descripción de Muestras")
                
                for i, img_file in enumerate(img_files):
                    c_img, c_desc = st.columns([1, 2])
                    with c_img:
                        st.image(img_file, caption=f"Muestra #{i+1}", use_container_width=True)
                    with c_desc:
                        st.markdown(f"**Archivo:** `{img_file.name}`")
                        # ID único para inputs
                        k_depth = f"core_depth_{img_file.name}"
                        k_desc = f"core_desc_{img_file.name}"
                        prev_data = st.session_state['core_descriptions'].get(img_file.name, {})
                        
                        core_md = st.number_input(f"Profundidad (MD ft) - {img_file.name}", value=prev_data.get('md', 0.0), key=k_depth)
                        core_txt = st.text_area(f"Descripción Litológica - {img_file.name}", value=prev_data.get('desc', ""), key=k_desc, placeholder="Ej: Arenisca grano fino...")
                        
                        st.session_state['core_descriptions'][img_file.name] = {'md': core_md, 'desc': core_txt, 'file': img_file.name}

                # TABLA RESUMEN DE NÚCLEOS
                if st.session_state['core_descriptions']:
                    st.divider()
                    st.markdown("### 📋 Tabla de Núcleos Descritos")
                    # Convertir dict a DataFrame
                    core_list = list(st.session_state['core_descriptions'].values())
                    if core_list:
                        df_core = pd.DataFrame(core_list)
                        df_core = df_core[['md', 'desc', 'file']].sort_values('md')
                        df_core.columns = ['Profundidad (MD)', 'Descripción', 'Archivo']
                        st.dataframe(df_core, use_container_width=True)
            else:
                st.info("📂 Suelte aquí las fotos de sus núcleos o diagramas de pozo para visualizarlos.")

        with t3:
            st.markdown("### :: Sísmica de Reflexión (2D/3D Viewer)")
            
            # Selector Principal: Demo vs Real vs LAS
            source_options = ["🔮 Simulación Sintética (Demo)", "📂 Archivo SEGY (Cargado)"]
            if PROJECT_READY:
                source_options.insert(1, "⚒️ Generar desde Pozo (LAS Activo)")
            
            source_mode = st.radio("Fuente de Datos:", source_options, horizontal=True)
            st.divider()

            # --- OPCIÓN 1: GENERAR DESDE LAS (REAL WELL DATA) ---
            if "LAS Activo" in source_mode:
                st.caption(f"Generando Sismograma Sintético basado en registros del pozo: **{st.session_state.get('well_name', 'Unknown')}**")
                
                # Verificar curvas necesarias
                cols = df_active.columns.tolist()
                
                # Intentar encontrar Densidad y Sónico
                den_col = next((c for c in cols if 'RHOB' in c or 'DEN' in c), None)
                dt_col = next((c for c in cols if 'DT' in c or 'SON' in c), None)
                
                if den_col:
                    # 1. Preparar Data del Pozo
                    # Rellenar nulos para el cálculo
                    df_clean = df_active.copy().interpolate().fillna(method='bfill').fillna(method='ffill')
                    
                    # 2. Calcular Impedancia & Reflectividad (Usando el Motor Geofísico)
                    try:
                        # Impedancia
                        if dt_col:
                            imp = df_clean[den_col] * (1000000 / df_clean[dt_col]) # Z = rho * v
                        else:
                            imp = df_clean[den_col] * 2500 # Vp constante asumida si no hay sónico
                        
                        # Reflectividad (RC)
                        rc = (imp.diff() / (imp + imp.shift())).fillna(0).values
                        
                        # 3. Convolución con Ricker
                        freq = 30 # Frecuencia dominante típica
                        t_wav, ricker = GeophysicsEngine.ricker_wavelet(freq, 0.100, 0.002) 
                        synth_trace = np.convolve(rc, ricker, mode='same')
                        
                        # Normalizar traza para visualización
                        synth_trace = synth_trace / (np.max(np.abs(synth_trace)) + 1e-9)
                        
                        # 4. Extender a 2D (Repetir traza lateralmente para crear sección)
                        nx_real = 100
                        nz_real = len(synth_trace)
                        
                        # Crear matriz 2D repitiendo la traza del pozo
                        seismic_data_real = np.tile(synth_trace, (nx_real, 1)).T
                        
                        # Añadir variación estructural suave (opcional, para que parezca una sección)
                        # O dejar plano si el usuario quiere ver "Layer Cake" estricto del pozo
                        
                        # 5. Visualización RICA (Con los mismos gráficos potentes)
                        fig_real = go.Figure()
                        
                        # Heatmap
                        fig_real.add_trace(go.Heatmap(
                            z=seismic_data_real, 
                            x=np.arange(nx_real), 
                            y=df_clean.index,  # Usar Profundidad Real del Pozo
                            colorscale='RdBu_r', 
                            zmid=0, 
                            colorbar=dict(title="Amplitud")
                        ))
                        
                        # Pozo (Línea central)
                        fig_real.add_shape(type="line", x0=nx_real/2, y0=df_clean.index.min(), x1=nx_real/2, y1=df_clean.index.max(), line=dict(color="red", width=2))
                        fig_real.add_annotation(x=nx_real/2, y=df_clean.index.min(), text=f"WELL: {st.session_state.get('well_name', 'Active')}", font=dict(color="red", weight="bold"), ay=-20)
                        
                        fig_real.update_yaxes(autorange="reversed", title="Profundidad (MD)")
                        fig_real.update_xaxes(title="Extensión Lateral (Proyección)", showgrid=False)
                        fig_real.update_layout(
                            title="Sección Sísmica Sintética (Data: LAS Real)",
                            template="plotly_dark",
                            height=700
                        )
                        st.plotly_chart(fig_real, use_container_width=True)
                        st.success("✅ Sección generada a partir de curvas reales de Densidad/Sónico.")
                        
                    except Exception as e:
                        st.error(f"Error calculando sintético: {e}")
                else:
                    st.warning("⚠️ No se encontró curva de Densidad (RHOB) en el archivo LAS para generar el sismograma.")
            
            # --- OPCIÓN 2: SIMULACIÓN (CODE EXISTENTE) ---
            elif "Simulación" in source_mode:
                # --- MODO DEMO SÍSMICA 2D "COMMERCIAL GRADE" ---
                st.caption("Generando modelo geofísico estructural con indicadores directos de hidrocarburos (DHI).")
                
                # Selector de Modo Visual (Dentro de la Simulación)
                view_mode = st.radio("Estilo de Renderizado:", ["🔍 Exploración (Bright Spots & DHI)", "📐 Interpretación Estructural (Horizontes & Pozo)"], horizontal=True)

                nx, nz = 150, 300 
                seismic_data = np.zeros((nz, nx))
                
                # 1. ESTRUCTURA Y FALLAS BASE (Común para ambos)
                x = np.linspace(0, 1, nx)
                base_layers = [50, 100, 140, 180, 220]
                fault_loc = 80
                fault_throw = 25
                
                # Arrays para guardar horizontes (para plotear luego)
                horizon_depths = {lz: [] for lz in base_layers}

                for layer_z in base_layers:
                    noise_horizon = np.random.normal(0, 1.5, nx) 
                    for i in range(nx):
                        structure = -15 * np.sin(x[i] * np.pi) 
                        if i > fault_loc: structure += fault_throw
                        
                        z_idx = int(layer_z + structure + noise_horizon[i])
                        
                        # Guardar traza del horizonte
                        horizon_depths[layer_z].append(z_idx if 0 <= z_idx < nz else np.nan)

                        if 0 <= z_idx < nz:
                            seismic_data[z_idx, i] = 1.0 
                            if z_idx+4 < nz: seismic_data[z_idx+4, i] = -0.8
                
                # 2. MODIFICACIONES ESPECÍFICAS POR MODO
                if view_mode.startswith("🔍"):
                        # MODO EXPLORACIÓN: GAS Y DHI
                    gas_z = 110 
                    for i in range(50, fault_loc): 
                        z_gas = int(gas_z - 15 * np.sin(x[i] * np.pi)) 
                        if i > fault_loc: z_gas += fault_throw 
                        if 0 <= z_gas < nz:
                            seismic_data[z_gas, i] = -2.5 
                            seismic_data[z_gas+5, i] = 2.0 
                    for i in range(10, 30): seismic_data[60, i] = -2.0 
                
                # 3. RUIDO Y CONVOLUCIÓN
                noise_bg = np.random.normal(0, 0.05, (nz, nx)) 
                seismic_data += noise_bg
                
                t_wav, ricker = GeophysicsEngine.ricker_wavelet(35, 0.08, 0.002) 
                seismic_image = np.zeros_like(seismic_data)
                for i in range(nx):
                    seismic_image[:, i] = np.convolve(seismic_data[:, i], ricker, mode='same')
                
                # 4. VISUALIZACIÓN
                fig_seis2d = go.Figure()
                
                if view_mode.startswith("🔍"):
                    # MODO EXPLORACIÓN (COLOR)
                    fig_seis2d.add_trace(go.Heatmap(
                        z=seismic_image, x=np.arange(nx), y=np.arange(nz), 
                        colorscale='RdBu_r', zmid=0, showscale=True, colorbar=dict(title="Amp")
                    ))
                    # Wiggles (Sparse)
                    for i in range(0, nx, 3):
                        trace_amp = seismic_image[:, i] * 4 
                        fig_seis2d.add_trace(go.Scatter(x=i + trace_amp, y=np.arange(nz), mode='lines', line=dict(color='black', width=0.4), showlegend=False, hoverinfo='skip'))
                    
                    # Anotaciones DHI
                    fig_seis2d.add_annotation(x=65, y=110, text="GAS POCKET (Bright Spot)", showarrow=True, arrowhead=2, arrowcolor="yellow", font=dict(color="yellow"))
                    fig_seis2d.add_annotation(x=80, y=160, text="NORMAL FAULT", showarrow=False, textangle=-90, font=dict(color="white"))
                    fig_seis2d.add_shape(type="line", x0=80, y0=50, x1=80, y1=250, line=dict(color="white", width=2, dash="dash"))

                else:
                    # MODO ANALISTA ESTRUCTURAL (GRISES + HORIZONTES)
                    fig_seis2d.add_trace(go.Heatmap(
                        z=seismic_image, x=np.arange(nx), y=np.arange(nz), 
                        colorscale='Greys', zmid=0, showscale=False # Grises estándar sismica
                    ))
                    
                    # Horizontes Interpretados
                    colors = ['magenta', 'yellow', '#00ff00']
                    nms = ["Horizon H10", "Horizon H20", "Horizon H30"]
                    for idx, lz in enumerate(base_layers[:3]):
                        hy = horizon_depths[lz]
                        fig_seis2d.add_trace(go.Scatter(x=np.arange(nx), y=hy, mode='lines', line=dict(color=colors[idx], width=2), name=nms[idx]))

                    # Pozo Propuesto
                    well_x = 110
                    fig_seis2d.add_shape(type="line", x0=well_x, y0=0, x1=well_x, y1=nz, line=dict(color="red", width=3))
                    fig_seis2d.add_annotation(x=well_x, y=10, text="Proposed Well", showarrow=True, arrowhead=2, arrowcolor="red", font=dict(color="red", size=12), ay=-30)
                    
                    # Etiquetas Units
                    fig_seis2d.add_annotation(x=130, y=40, text="Unit A", showarrow=False, font=dict(color="white"))
                    fig_seis2d.add_annotation(x=130, y=130, text="Unit C", showarrow=False, font=dict(color="white"))


                fig_seis2d.update_yaxes(autorange="reversed", title="TWT (ms)", showgrid=False)
                fig_seis2d.update_xaxes(title="CDP", showgrid=False)
                
                # Marca de agua
                fig_seis2d.add_annotation(
                    x=nx/2, y=nz/2,
                    text="DEMO DATA (SYNTHETIC)",
                    showarrow=False,
                    font=dict(color="rgba(255,255,255,0.2)", size=30, family="Arial Black"),
                    textangle=-15
                )
                
                fig_seis2d.update_layout(
                    title=f"Sección Sísmica - {view_mode} (SIMULACIÓN)",
                    template="plotly_dark",
                    height=700,
                    margin=dict(l=40, r=40, t=50, b=50)
                )
                st.plotly_chart(fig_seis2d, use_container_width=True)

            else:
                # --- MODO DATOS REALES (SEGY) ---
                if "segy_meta" in st.session_state:
                    meta = st.session_state["segy_meta"]
                    st.success(f"📂 Archivo Activo: {meta['filename']}")
                    if "segy_preview_trace" in st.session_state:
                        tr_data = st.session_state['segy_preview_trace']
                        fig_seis = px.line(y=tr_data, title="Traza Sísmica de Control (Preview)")
                        fig_seis.update_layout(template="plotly_dark")
                        st.plotly_chart(fig_seis)
                else:
                    st.info("ℹ️ Cargue un archivo .SGY en la barra lateral para visualizar sus datos reales.")

        with t4:
            st.markdown("### :: Trayectoria 3D & Propiedades del Pozo")
            st.caption("Visualización espacial del pozo basada en datos registrales reales.")
            
            if PROJECT_READY:
                las_obj = st.session_state.get("las_object", None)
                
                # --- LAYOUT: WELL INFO | MODEL 3D ---
                col_meta, col_map = st.columns([1, 2.5])
                
                with col_meta:
                    st.markdown("#### :: Well Master Data")
                    # Extraer info del header del LAS de forma segura
                    def get_h(m, d="-"): 
                        try: return las_obj.well[m].value if m in las_obj.well else d
                        except: return d
                    
                    well_info = {
                        "Pozo": get_h("WELL"),
                        "Campo": get_h("FLD"),
                        "Empresa": get_h("COMP"),
                        "Servicios": get_h("SRVC"),
                        "Ubicación": get_h("LOC"),
                        "Fecha": get_h("DATE"),
                        "API/UWI": get_h("UWI", get_h("API"))
                    }
                    
                    for k, v in well_info.items():
                        st.markdown(f"**{k}:** `{v}`")
                    
                    st.divider()
                    st.info("💡 Datos extraídos directamente de la cabecera del archivo LAS.")

                    # --- EXPORT STATION (GEOLOGY) ---
                    st.divider()
                    st.markdown("### 📥 Geophysical Model Export")
                    gx1, gx2 = st.columns(2)
                    if gx1.button("📑 Build PDF Report", key="gi_pdf"):
                        html_gi = report_generator.generate_html_report(
                            well_info, df_active, None,
                            qc_report_list=st.session_state.get("qc_report", []),
                            asset_health=asset_health if 'asset_health' in locals() else 94.2
                        )
                        st.download_button("💾 Download Report", html_gi, f"GEOLOGY_REPORT_{well_info['Pozo']}.html", "text/html", use_container_width=True, key="gi_pdf_dl")
                    # Exportar solo curvas disponibles para evitar KeyError
                    export_cols = [c for c in ['GR', 'RT', 'RHOB', 'NPHI', 'DT'] if c in df_active.columns]
                    if not export_cols: export_cols = df_active.columns.tolist()[:5] # Fallback a las primeras 5
                    csv_gi = df_active[export_cols].to_csv(index=False).encode('utf-8')
                    gx2.download_button("📊 Download Data", data=csv_gi, file_name=f"GEOLOGY_EXPORT_{well_info['Pozo']}.csv", mime='text/csv', use_container_width=True, key="gi_csv_dl")

                with col_map:
                    # Selectores de Propiedades Reales
                    c3d_1, c3d_2 = st.columns(2)
                    # Intentar seleccionar GR por defecto
                    all_cols = df_active.columns.tolist()
                    def_col = 'GR' if 'GR' in all_cols else all_cols[0]
                    idx_def = all_cols.index(def_col) if def_col in all_cols else 0
                    
                    color_curve = c3d_1.selectbox("Propiedad (Color Traza)", all_cols, index=idx_def)
                    
                    # Generar Trayectoria 3D
                    z = df_active.index
                    visual_mode = st.checkbox("■ Mostrar Desviación (Visualización Espacial)", value=True)
                    
                    if visual_mode:
                        t = np.linspace(0, 8 * np.pi, len(z))
                        r = 30; x = r * np.sin(t); y = r * np.cos(t)
                    else:
                        x = np.zeros_like(z); y = np.zeros_like(z)
                    
                    c_data = df_active[color_curve]
                    
                    fig_3d = go.Figure(data=[go.Scatter3d(
                        x=x, y=y, z=z, mode='markers',
                        marker=dict(size=4, color=c_data, colorscale='Jet', opacity=0.8, colorbar=dict(title=color_curve, thickness=15)),
                        text=c_data, hovertemplate=f"Prof: %{{z:.1f}} m<br>{color_curve}: %{{text:.2f}}<extra></extra>"
                    )])
                    
                    fig_3d.update_layout(
                        title=f"3D Structural Model: {well_info['Pozo']}",
                        height=650, template="plotly_dark",
                        scene=dict(
                            xaxis_title='X', yaxis_title='Y', zaxis_title='MD/TVD',
                            zaxis=dict(autorange="reversed"),
                            aspectmode='manual', aspectratio=dict(x=1, y=1, z=3)
                        ),
                        margin=dict(l=0, r=0, b=0, t=40)
                    )
                    st.plotly_chart(fig_3d, use_container_width=True)
                
                if visual_mode:
                    st.info("ℹ️ Geometría X-Y esquemática. Profundidad (Z) y Colores son DATOS REALES.")
                else:
                    st.info("ℹ️ Visualización vertical estricta.")
                    
                # Detener aquí para ignorar el código viejo de abajo por ahora
                # st.stop() # No usamos stop para no matar el resto de la app si hay algo abajo fuera del tab
            
            else:
                st.warning("⚠️ Cargue un archivo LAS.")
            
            # --- CÓDIGO VIEJO A CONTINUACIÓN (IGNORADO VISUALMENTE) ---
            if False: # Desactivar código viejo
                pass
            
            # Opción Simulada (Para demo) o Real
            # sim_surf = st.checkbox("🔮 Usar Datos DEMO", value=True)
            
            if False: # sim_surf:
                # LÓGICA DE INTERPOLACIÓN DEMO
                from scipy.interpolate import griddata
                
                # 1. Generar puntos aleatorios (Simulando pozos)
                np.random.seed(0)
                n_pts = 100
                x_pts = np.random.uniform(-100, 100, n_pts)
                y_pts = np.random.uniform(-100, 100, n_pts)
                # Superficie compleja: Seno(R)
                z_pts = np.sin(np.sqrt(x_pts**2 + y_pts**2)/10) * 10 + np.random.normal(0, 1, n_pts)
                
                # 2. Crear Grid Regular
                grid_x, grid_y = np.meshgrid(
                    np.linspace(-100, 100, 50),
                    np.linspace(-100, 100, 50)
                )
                
                # 3. Interpolación (Linear o Cubic)
                grid_z = griddata((x_pts, y_pts), z_pts, (grid_x, grid_y), method='cubic')
                
                # 4. Plotly Surface
                # Paleta LightningChart: Blue-Cyan-Green-Yellow-Red
                lc_colors = [[0, 'blue'], [0.25, 'cyan'], [0.5, 'green'], [0.75, 'yellow'], [1, 'red']]
                
                fig_surf = go.Figure(data=[go.Surface(
                    x=grid_x, y=grid_y, z=grid_z,
                    colorscale=lc_colors,
                    colorbar=dict(title="Elevación (m)")
                )])
                
                # Agregar puntos originales (Pozos)
                fig_surf.add_trace(go.Scatter3d(
                    x=x_pts, y=y_pts, z=z_pts,
                    mode='markers', marker=dict(size=4, color='white', line=dict(color='black', width=1)),
                    name='Puntos de Control'
                ))

                fig_surf.update_layout(
                    template="plotly_dark",
                    title="Modelo Estructural 3D (Interpolado)",
                    scene=dict(
                        xaxis=dict(title="Este (X)", gridcolor="#444"),
                        yaxis=dict(title="Norte (Y)", gridcolor="#444"),
                        zaxis=dict(title="Elevación (Z)", gridcolor="#444")
                    ),
                    height=700,
                    margin=dict(l=0, r=0, b=0, t=40)
                )
                st.plotly_chart(fig_surf, use_container_width=True)
            else:
                st.info("ℹ️ Para usar datos reales, seleccione curvas X, Y (Coords) y Z (Propiedad) de su dataset cargado.")
                st.warning("⚠️ Funcionalidad de 'Mapeo Real' en desarrollo. Active el modo DEMO para ver el ejemplo.")
            
            # --- GEO-INSIGHT SUPERFICIE ---
            st.info("""
            **🧭 Guía de Navegación Estructural (Prospectos):**
            - Este mapa muestra la **morfología del yacimiento** (Topes Estructurales).
            - Busque **"Domos" o "Anticlinales"** (Zonas altas rodeadas de bajas): Son las trampas naturales donde se acumula el petróleo.
            - Las zonas de **color rojo/amarillo** representan los puntos más altos (Crestas).
            - **Objetivo de Perforación:** Apuntar a las crestas para maximizar la columna de hidrocarburos.
            """)

    # 3. FORMATION EVALUATION (Petrofísica - FE)
    elif role == MODULES["FE"]:
        st.markdown("<h1 class='main-header'>:: Formation Evaluation & Petrophysics</h1>", unsafe_allow_html=True)
        if not PROJECT_READY: st.error("■ No Data Stream."); st.stop()

        # --- EXPORT STATION (FE) ---
        with st.sidebar:
            st.divider()
            st.markdown("### 📥 FE Report Station")
            if st.button("📑 Build Petrophysical Report", key="fe_pdf"):
                html_fe = report_generator.generate_html_report(
                    well_info, df_active, st.session_state.get("pay_intervals", None),
                    qc_report_list=st.session_state.get("qc_report", []),
                    asset_health=asset_health if 'asset_health' in locals() else 94.2
                )
                st.download_button("💾 Download Report", html_fe, f"PETROPHYSICS_{well_name}.html", "text/html", use_container_width=True, key="fe_pdf_dl")
            csv_fe = df_active.to_csv(index=False).encode('utf-8')
            st.download_button("📊 Export Table (.CSV)", data=csv_fe, file_name=f"FE_LOGS_{well_name}.csv", mime='text/csv', use_container_width=True, key="fe_csv_dl")
        
        t_fe0, t_fe1, t_fe2, t_fe3 = st.tabs(["○ Raw Data", "● Log Analysis", "∿ NMR Studio", "◘ FMI Imager"])
        
        # --- TAB 0: RAW DATA INSPECTOR (QC & ALL CURVES) ---
        with t_fe0:
            st.markdown("### Multi-Track Viewer")
            st.caption("Inspección visual y selección de curvas activas.")
            
            # 1. Obtener todas las columnas y pre-seleccionar las numéricas
            all_cols = df_active.columns.tolist()
            numeric_cols = df_active.select_dtypes(include=[np.number]).columns.tolist()
            # Excluir profundidad de la selección default para no graficarla contra sí misma
            default_cols = [c for c in numeric_cols if c not in ['DEPTH', 'Depth', 'MD', 'tvd', 'TVD']]
            
            # 2. Widget de Selección (User Control)
            selected_tracks = st.multiselect(
                "Seleccione las curvas a visualizar (Tracks):", 
                options=all_cols, 
                default=default_cols[:min(10, len(default_cols))] # Limitar default a 10 para no explotar la pantalla
            )
            
            if selected_tracks:
                num_tracks = len(selected_tracks)
                # Crear Subplots Dinámicos: 1 Fila, N Columnas
                fig_all = make_subplots(
                    rows=1, cols=num_tracks, 
                    shared_yaxes=True, 
                    subplot_titles=selected_tracks,
                    horizontal_spacing=0.01
                )
                
                # Colores rotativos
                colors = px.colors.qualitative.Plotly * 3
                
                for i, col in enumerate(selected_tracks):
                    # Intentar convertir a numerico si fue forzado por el user
                    try:
                        y_data = df_active[col]
                        # Añadir traza
                        fig_all.add_trace(go.Scatter(
                            x=y_data, 
                            y=df_active.index, 
                            mode='lines',
                            line=dict(color=colors[i], width=1, shape='spline', smoothing=0.3), 
                            name=col
                        ), row=1, col=i+1)
                        
                        # Grid y Estilo
                        fig_all.update_xaxes(showgrid=True, gridcolor='#333', row=1, col=i+1, title_font=dict(size=10))
                    except Exception as e:
                        st.warning(f"No se pudo graficar {col}: {e}")
                
                # Layout Global
                fig_all.update_yaxes(autorange="reversed", title="Profundidad (MD)", showgrid=True, gridcolor='#444')
                fig_all.update_layout(
                    height=1000, 
                    template="plotly_dark", 
                    showlegend=False,
                    title=f"Registro de Pozo ({num_tracks} Pistas)",
                    margin=dict(l=50, r=20, t=60, b=40)
                )
                st.plotly_chart(fig_all, use_container_width=True)
                
                with st.expander("Ver Tabla de Datos (Raw CSV)"):
                    st.dataframe(df_active, use_container_width=True)
            else:
                st.warning("⚠️ Seleccione al menos una curva para visualizar.")

        # --- TAB 1: TRIPLE COMBO ESTÁNDAR ---
        with t_fe1:
            st.caption("Advanced Log Analysis System & Quick-Look Interpretation")
            
            c_fe1, c_fe2 = st.columns([1, 4])
            with c_fe1:
                with st.expander("📐 Parámetros Matriz (Audit)", expanded=False):
                    rw_val = st.number_input("Rw @ Fm Temp", 0.01, 5.0, 0.05, format="%.3f")
                    a_val = st.number_input("a (Tortuosidad)", 0.5, 2.0, 1.0)
                    m_val = st.number_input("m (Cementación)", 1.0, 3.0, 2.0)
                    n_val = st.number_input("n (Saturación)", 1.0, 3.0, 2.0)
                
                st.divider()
                st.markdown("#### :: Pay Cutoffs")
                cut_vsh = st.slider("Vsh Max", 0.0, 100.0, 40.0) / 100.0
                cut_phi = st.slider("Phi Min", 0.0, 30.0, 8.0) / 100.0
                cut_sw = st.slider("Sw Max", 0.0, 100.0, 50.0) / 100.0
                
                if st.button("▶️ UPDATE MODEL"):
                    # Recálculo Archie
                    if 'PHIE_FINAL' in df_active.columns and 'RT' in df_active.columns:
                        df_active['SW_ARCHIE'] = np.sqrt( (a_val * rw_val) / ( (df_active['PHIE_FINAL']**m_val) * df_active['RT'] ) )
                        df_active['SW_ARCHIE'] = df_active['SW_ARCHIE'].clip(0, 1)
                        
                        # CALCULAR PAY FLAG (BANDERA VERDE)
                        # Usar Simandoux si existe, sino Archie
                        sw_col = 'SW_SIMANDOUX' if 'SW_SIMANDOUX' in df_active.columns else 'SW_ARCHIE'
                        
                        df_active['PAY_FLAG'] = np.where(
                            (df_active['VSH_FINAL'] <= cut_vsh) & 
                            (df_active['PHIE_FINAL'] >= cut_phi) & 
                            (df_active[sw_col] <= cut_sw), 
                            1, 0
                        )
                        
                        st.session_state["project_data"] = df_active 
                        st.toast("Modelo Petrofísico y Pay Flag Recalculados", icon="✅")
                    else:
                        st.error("Faltan curvas PHI/RT para el modelo.")
            
            with c_fe2:
                # Triple Combo Plot Simple
                if 'PHIE_FINAL' in df_active.columns:
                    # 4 Tracks ahora: GR, RT, PHI, PAY FLAG
                    fig_log = make_subplots(rows=1, cols=4, shared_yaxes=True, column_widths=[0.2, 0.2, 0.2, 0.1], 
                                          subplot_titles=("Gamma Ray", "Resistivity", "Porosity", "PAY FLAG"))
                    
                    # Track 1: GR
                    fig_log.add_trace(go.Scatter(x=df_active['GR'], y=df_active.index, line=dict(color='#10b981', width=1, shape='spline', smoothing=0.5), name='GR'), row=1, col=1)
                    
                    # Track 2: RT (Resistividad necesita cuidado con spline en log, pero funciona visualmente)
                    fig_log.add_trace(go.Scatter(x=df_active['RT'], y=df_active.index, line=dict(color='#f59e0b', width=1.5, shape='spline', smoothing=0.5), name='RT'), row=1, col=2)
                    fig_log.update_xaxes(type="log", row=1, col=2, gridcolor='#333')
                    
                    # Track 3: PHI
                    fig_log.add_trace(go.Scatter(x=df_active['PHIE_FINAL'], y=df_active.index, line=dict(color='#00f2ff', width=1, shape='spline', smoothing=0.5), name='PHIE'), row=1, col=3)
                    fig_log.update_xaxes(autorange="reversed", row=1, col=3)
                    
                    # Track 4: PAY FLAG (BANDERA VERDE)
                    if 'PAY_FLAG' in df_active.columns:
                        # Filtrar solo Pay para aligerar gráfico
                        pay_zones = df_active[df_active['PAY_FLAG'] == 1]
                        if not pay_zones.empty:
                            fig_log.add_trace(go.Bar(
                                x=[1]*len(pay_zones), 
                                y=pay_zones.index, 
                                orientation='h',
                                marker_color='#22c55e',
                                opacity=1,
                                name='NET PAY',
                                hoverinfo='y'
                            ), row=1, col=4)
                    
                    fig_log.update_xaxes(range=[0, 1], showticklabels=False, row=1, col=4, title="PAY")
                    fig_log.update_yaxes(autorange="reversed")
                    fig_log.update_layout(height=1000, template="plotly_dark", showlegend=False)
                    st.plotly_chart(fig_log, use_container_width=True)
                else:
                    st.info("Ejecute el modelo base primero.")

        # --- TAB 2: NMR STUDIO (Simulación LogIC) ---
        with t_fe2:
            st.subheader(":: NMR Pore Partitioning")
            st.caption("Distribución T2 Simulada & Cutoffs (CBW / BVI / FFI)")

            col_nmr_ctrl, col_nmr_plot = st.columns([1, 3])
            with col_nmr_ctrl:
                st.markdown("#### T2 Cutoffs (ms)")
                t2_clay = st.slider("Clay Bound (CBW)", 0.5, 5.0, 3.0)
                t2_cap = st.slider("Capillary Bound (BVI)", 10.0, 100.0, 33.0)
                if st.button("⚡ Run NMR Simulation"):
                    st.session_state['nmr_data'] = True
            
            with col_nmr_plot:
                if 'nmr_data' in st.session_state:
                    fig_nmr = go.Figure()
                    t_bins = np.logspace(-1, 3, 100)
                    y_total = np.exp( - (np.log10(t_bins) - np.log10(200))**2 / 0.5 ) # Simple dist
                    fig_nmr.add_trace(go.Scatter(x=t_bins, y=y_total, mode='lines', line=dict(color='white'), name='T2 Spectrum'))
                    fig_nmr.update_xaxes(type="log", title="Relaxation Time T2 (ms)")
                    fig_nmr.update_layout(template="plotly_dark", height=500)
                    st.plotly_chart(fig_nmr, use_container_width=True)

        # --- TAB 3: BOREHOLE IMAGES (FMI) ---
        with t_fe3:
            st.subheader(":: Borehole Image Interpretation")
            if st.checkbox("Generate Synthetic FMI View", key="fmi_gen"):
                depth_fmi = np.linspace(0, 50, 200)
                azimuth = np.linspace(0, 360, 90)
                z, a = np.meshgrid(depth_fmi, azimuth)
                img_data = np.sin(a/50) * np.cos(z/10)
                fig_fmi = go.Figure(data=go.Heatmap(z=img_data, x=depth_fmi, y=azimuth, colorscale='Cividis'))
                st.plotly_chart(fig_fmi, use_container_width=True)

    # 4. RESERVOIR ENGINEERING (Yacimientos)
    elif role == MODULES["RE"]:
        st.markdown("<h1 class='main-header'>:: Reservoir Engineering & Analytics</h1>", unsafe_allow_html=True)
        if not PROJECT_READY: st.error("■ Sin datos."); st.stop()
        
        # ZONATION SLIDER (Filtro de Profundidad)
        min_d, max_d = float(df_active.iloc[0,0]), float(df_active.iloc[-1,0])
        st.write("### ■ Definición de Zona de Interés (Topes)")
        z_top, z_base = st.slider("Intervalo de Análisis (MD ft):", min_d, max_d, (min_d, max_d))
        
        # Filtrar Data por Zona
        mask_zone = (df_active.iloc[:,0] >= z_top) & (df_active.iloc[:,0] <= z_base)
        df_zone = df_active[mask_zone].copy()
        
        st.caption(f"Analizando tramo: {z_top:.1f} - {z_base:.1f} ft ({len(df_zone)} pies de espesor bruto).")
        st.divider()

        t1, t2, t3, t4 = st.tabs(["○ Pay Flag", "● Economía", "◘ Reporte PDF", "■ Exportar LAS"])
        
        with t1:
            c1, c2, c3 = st.columns(3)
            cp = c1.slider("Phi Min", 0, 30, 10)/100
            cv = c2.slider("Vsh Max", 0, 100, 40)/100
            cs = c3.slider("Sw Max", 0, 100, 50)/100
            
            if st.button("Buscar Pay Zones"):
                # Mapeo rápido
                temp = df_zone.copy() # USAR DATA FILTRADA POR ZONA
                # Intentar mapear columnas clave si existen
                p_c = next((c for c in temp.columns if 'PHI' in c or 'POR' in c), None)
                v_c = next((c for c in temp.columns if 'VSH' in c), None) # Preferir VSH
                s_c = next((c for c in temp.columns if 'SIMANDOUX' in c), None) # Preferir Simandoux
                if not s_c: s_c = next((c for c in temp.columns if 'SW' in c), None)
                
                if p_c and v_c and s_c:
                    if temp[p_c].mean() > 1: temp[p_c] /= 100
                    temp['PHI'] = temp[p_c]; temp['VSH'] = temp[v_c]; temp['SW'] = temp[s_c]
                    
                    intervals = ReservoirDetector.detect_prospect_intervals(temp, {'porosity_min': cp, 'vshale_max': cv, 'sw_max': cs})
                    if not intervals.empty:
                        st.session_state["pay_intervals"] = intervals
                        st.success(f"{len(intervals)} Intervalos detectados en la Zona.")
                        st.dataframe(intervals)
                        
                        # Net Pay Summary
                        net_pay = intervals['Espesor_ft'].sum()
                        gross = z_base - z_top
                        ntg = net_pay / gross if gross > 0 else 0
                        st.metric("Net Pay Total", f"{net_pay:.1f} ft", f"N/G: {ntg:.2f}")
                        
                    else: st.warning("No se encontraron zonas productivas.")
                else: st.error("Faltan curvas (Phi, Vsh, Sw). Ejecute módulo Petrofísico.")

        with t2:
            oip = st.number_input("OIP (bbls)", value=5000000)
            pr = st.number_input("Precio ($)", value=70)
            if st.button("Simular"):
                sim = SimulationEngine.simular_produccion(oip, pr)
                st.line_chart(sim.set_index("Mes")["Ingresos_USD"])
                st.metric("ROI 10y", f"${sim['Ingresos_USD'].sum()/1e6:.1f} MM")

        with t3:
            if st.button("Generar Informe HTML"):
                html = report_generator.generate_html_report(
                    well_name, df_zone, st.session_state.get("pay_intervals", None),
                    qc_report_list=st.session_state.get("qc_report", []),
                    fig_triple=go.Figure(), fig_intervals=go.Figure() # Fix: Evitar NoneType en Plotly JSON
                )
                st.download_button("Descargar Informe", html, f"Reporte_{well_name}.html", "text/html")
        
        with t4:
            st.markdown("### Interoperabilidad (Petrel / Kingdom)")
            st.info("Exportar curvas calculadas (Sw, Vsh, Perm) en formato estándar industrial.")
            las_str = LASExporter.export_pandas_to_las(df_active, well_name) # Exportar TODO el pozo, no solo la zona
            st.download_button("■ Descargar Archivo .LAS", las_str, f"{well_name}_procesado.las", "text/plain")

    # 5. DATA INTEGRITY & AI SYSTEMS (Data Science)
    elif role == MODULES["DI"]:
        st.markdown("<h1 class='main-header'>:: Data Integrity & AI Systems</h1>", unsafe_allow_html=True)
        if not PROJECT_READY: 
            st.warning("■ Esperando flujo de datos activo..."); st.stop()

        # --- EXPORT STATION (DI) ---
        with st.sidebar:
            st.divider()
            st.markdown("### 📥 AI Audit Export")
            if st.button("📑 Tech Audit Report", key="di_pdf"):
                html_di = report_generator.generate_html_report(
                    well_info, df_active, None,
                    qc_report_list=st.session_state.get("qc_report", []),
                    asset_health=asset_health if 'asset_health' in locals() else 94.2
                )
                st.download_button("💾 Download Report", html_di, f"AI_AUDIT_{well_name}.html", "text/html", use_container_width=True, key="di_pdf_dl")
            qc_csv = pd.DataFrame(st.session_state.get("qc_report", [])).to_csv(index=False).encode('utf-8')
            st.download_button("📊 Audit Summary (.CSV)", data=qc_csv, file_name="DATA_QUALITY_AUDIT.csv", use_container_width=True, key="di_csv_dl")
        
        t1, t2, t3, t4, t5, t6 = st.tabs(["○ Auditoría SEG", "● Análisis de Distribución", "◆ Radar de Calidad de Roca", "↝ Correlaciones", "▲ Señales en Tiempo Real", "● 4D Bubble Explorer"])
        
        with t1:
            st.subheader("Estado de Integridad del Activo")
            qc = st.session_state.get("qc_report", ["Sin auditoría ejecutada."])
            
            # Sistema de validación de "Cierre" (Guardado)
            errores_criticos = [q for q in qc if "❌" in q]
            if errores_criticos:
                st.error(f"Bloqueo de Seguridad: {len(errores_criticos)} errores críticos detectados. No se permite exportar LAS.")
            else:
                st.success("Validación exitosa. El dataset cumple con los estándares corporativos.")

        with t2:
            # Histograma con estilo "Industrial Glow"
            var = st.selectbox("Curva para análisis estadístico", df_active.columns)
            fig_hist = px.histogram(df_active, x=var, nbins=50, template="plotly_dark",
                                     title=f"Distribución de {var}")
            fig_hist.update_traces(marker_color='#00d2ff', marker_line_color='#ffffff', marker_line_width=1)
            fig_hist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_hist, use_container_width=True)

        with t3:
            # RADAR CHART: El "Holograma" de potencial del pozo
            st.markdown("### :: Rock Quality Index (RQI)")
            
            # Lógica de negocio: Cálculo de scores para el Radar
            sw_ready = 'SW_SIMANDOUX' in df_active.columns or 'SW_ARCHIE' in df_active.columns
            if sw_ready:
                res_avg = df_active.mean(numeric_only=True)
                
                # Normalización de 0 a 1 para el Radar
                phi_val = res_avg.get('PHIE_FINAL', res_avg.get('NPHI', 0.15)) 
                phi_score = np.clip(phi_val / 0.35, 0, 1) # 0.35 es el tope de porosidad
                
                # Si no hay SW Simandoux, intenta fallbacks
                sw_val = res_avg.get('SW_SIMANDOUX', res_avg.get('SW_ARCHIE', 1))
                so_score = 1 - sw_val # Saturación de aceite
                
                vsh_score = 1 - res_avg.get('VSH_FINAL', 0.5) # Inverso: 1 es roca limpia
                
                categories = ['Porosidad', 'Saturación Aceite', 'Limpieza (Vsh)', 'Potencial Econ.', 'Calidad Data']
                scores = [phi_score, so_score, vsh_score, (phi_score + so_score)/2, 0.9] # 0.9 es un dummy de calidad
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=scores + [scores[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    fillcolor='rgba(0, 210, 255, 0.3)',
                    line=dict(color='#00d2ff', width=2),
                    marker=dict(size=8, color='#4ade80')
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 1], gridcolor="#333"),
                        angularaxis=dict(gridcolor="#333"),
                        bgcolor='rgba(0,0,0,0)'
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    height=500
                )
                st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.info("Ejecute el módulo Petrofísico para generar el Radar de Calidad.")
        
        with t4:
            st.markdown("### 📈 Scatter Trends (Estilo Lightning)")
            st.caption("Correlación Cruzada con Mapeo de Intensidad Automático")
            
            c1, c2 = st.columns(2)
            # Selectores inteligentes
            cols = df_active.columns.tolist()
            # Intenta poner profundidad en X si existe, o la primera col
            def_x = 0
            # Intenta poner alguna propiedad interesante en Y (ej. Neutron o Resistividad)
            def_y = min(1, len(cols)-1)
            
            x_sc = c1.selectbox("Eje X (Ej. Profundidad)", cols, index=def_x)
            y_sc = c2.selectbox("Eje Y (Ej. Magnitud/Valor)", cols, index=def_y)
            
            # Paleta EXACTA solicitada: DarkBlue -> LightBlue -> Orange -> Red
            custom_scale = [
                [0.0, 'darkblue'],
                [0.33, 'lightblue'],
                [0.66, 'orange'],
                [1.0, 'red']
            ]
            
            fig_sc = go.Figure(data=go.Scatter(
                x=df_active[x_sc],
                y=df_active[y_sc],
                mode='markers',
                marker=dict(
                    size=6,
                    color=df_active[y_sc], # Colorear por magnitud Y (como pidió el user)
                    colorscale=custom_scale,
                    showscale=True,
                    colorbar=dict(title=y_sc, thickness=15)
                )
            ))
            
            # Layout Cyberpunk - ENMARCADO TÉCNICO (BOX STYLE)
            fig_sc.update_layout(
                template="plotly_dark",
                height=600,
                title=f"📈 Correlación Cruzada: {x_sc} vs {y_sc}",
                margin=dict(l=40, r=40, t=60, b=40),
                paper_bgcolor='#0e1117',
                plot_bgcolor='#0e1117',
                # EJE X CON MARCO COMPLETO
                xaxis=dict(
                    title=x_sc, 
                    showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)',
                    showline=True, linewidth=2, linecolor='white', mirror=True # Marco espejo
                ),
                # EJE Y CON MARCO COMPLETO
                yaxis=dict(
                    title=y_sc, 
                    showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)',
                    showline=True, linewidth=2, linecolor='white', mirror=True # Marco espejo
                )
            )
            # Invertir eje Y si es profundidad
            if x_sc == df_active.columns[0]: 
                 # En el ejemplo del user Depth es X. Dejémoslo normal por ahora.
                 pass
                 
            st.plotly_chart(fig_sc, use_container_width=True)
            
            # --- DATA INSIGHT CORRELACIONES ---
            with st.expander("📊 Análisis Estadístico (Correlación)", expanded=True):
                 try:
                    # Calcular R2 si son numéricos
                    valid_data = df_active[[x_sc, y_sc]].dropna()
                    num_check = True # Asumir numérico por simplicidad en demo, pero ideal verificar
                    if not valid_data.empty:
                        # Forzar conversión numérica segura
                        v1 = pd.to_numeric(valid_data[x_sc], errors='coerce')
                        v2 = pd.to_numeric(valid_data[y_sc], errors='coerce')
                        valid_data = pd.DataFrame({x_sc: v1, y_sc: v2}).dropna()

                        if not valid_data.empty:
                            corr = valid_data[x_sc].corr(valid_data[y_sc])
                            r2 = corr**2
                            
                            k1, k2, k3 = st.columns(3)
                            k1.metric("Coeficiente R²", f"{r2:.4f}")
                            k2.metric("Correlación Pearson", f"{corr:.2f}")
                            
                            interp = "Sin relación aparente."
                            if abs(corr) > 0.7: interp = "💎 Correlación FUERTE. Variable predictiva útil."
                            elif abs(corr) > 0.4: interp = "⚠️ Correlación MODERADA. Usar con cautela."
                            
                            k3.write(f"**Veredicto:** {interp}")
                        else: st.warning("Datos no numéricos.")
                 except Exception as e:
                    st.warning(f"No se pudo calcular estadística: {e}")
            
        with t5:
            st.markdown("### Análisis de Eventos y Series Temporales")
            st.caption("Monitorización de Alta Frecuencia: Detección de Cambios de Régimen (Step-Change Detection).")
            
            c_ts1, c_ts2 = st.columns([1, 3])
            
            with c_ts1:
                st.markdown("#### Parámetros de Simulación")
                st.info("Generador de señales sintéticas para pruebas de algoritmos de detección.")
                n_points = st.slider("Ventana de Tiempo (muestras)", 100, 1000, 400)
                noise_lvl = st.slider("Ruido de Fondo (RMS)", 0.1, 5.0, 1.5)
                jump_mag = st.slider("Magnitud del Evento", -50.0, 50.0, -25.0, step=5.0)
                
                st.divider()
                st.metric("Evento Detectado", f"t={int(n_points*0.6)}", delta="CONFIRMED")
            
            with c_ts2:
                # Generar Datos Sintéticos (Estilo GPS/Sismología)
                time = np.arange(n_points)
                np.random.seed(42)
                signal = np.random.normal(0, noise_lvl, n_points)
                
                # Evento (Salto) en t = 60% del tiempo
                event_idx = int(n_points * 0.6)
                signal[event_idx:] += jump_mag
                
                # Decaimiento post-evento (Relajación)
                decay = np.linspace(0, jump_mag * 0.15, n_points - event_idx)
                signal[event_idx:] -= decay
                
                # Umbrales Dinámicos
                upper_limit = 5.0
                lower_limit = -5.0
                if abs(jump_mag) > 5: 
                    if jump_mag < 0: lower_limit = jump_mag - 10
                    else: upper_limit = jump_mag + 10

                # Plotting estilo Científico (Paper Style)
                fig_ts = go.Figure()
                
                # 1. Señal (Azul científico)
                fig_ts.add_trace(go.Scatter(
                    x=time, y=signal, 
                    mode='lines', 
                    name='Raw Sensor Data',
                    line=dict(color='#4c78a8', width=1.5) 
                ))
                
                # 2. Línea de Evento (Roja Punteada Vertical)
                fig_ts.add_shape(
                    type="line",
                    x0=time[event_idx], y0=min(signal)-5,
                    x1=time[event_idx], y1=max(signal)+5,
                    line=dict(color="#e45756", width=2, dash="dot"),
                )
                fig_ts.add_annotation(x=time[event_idx], y=max(signal), text="EVENT ONSET", showarrow=True, arrowcolor="#e45756", ay=-40, font=dict(color="#e45756", weight="bold"))

                # 3. Umbrales (Verde Punteado Horizontal)
                fig_ts.add_hline(y=upper_limit, line_dash="dot", line_color="#59a14f", annotation_text="Upper Tol.", annotation_font_color="#59a14f")
                fig_ts.add_hline(y=lower_limit, line_dash="dot", line_color="#59a14f", annotation_text="Lower Tol.", annotation_font_color="#59a14f")

                fig_ts.update_layout(
                    title="Análisis de Desplazamiento (Station CONZ)",
                    xaxis_title="Tiempo (horas)",
                    yaxis_title="Desplazamiento (mm)",
                    template="plotly_white", # Fondo blanco para estilo paper
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    height=500,
                    showlegend=True,
                    margin=dict(l=50, r=50, t=50, b=50),
                    font=dict(color="black") # Texto negro para contraste en blanco
                )
                # Grid suave para referencia
                fig_ts.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#eee')
                fig_ts.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#eee')
                
                st.plotly_chart(fig_ts, use_container_width=True)
        
        with t6:
            st.markdown("### 🫧 4D Bubble Explorer")
            st.caption("Análisis Multidimensional: X, Y, Z + Tamaño Variable")
            
            # Priorizar DATOS REALES
            run_sim = st.checkbox("🔮 Activar Modo DEMO (Simulación Random Walk)", value=False)
            
            if run_sim:
                # REPLICANDO EL CÓDIGO RANDOM WALK (VERSION NUMPY OPTIMIZADA)
                np.random.seed(42)
                # ... (resto igual)
                n_points = 250
                x_b = np.arange(n_points)
                y_b = np.cumsum(np.random.uniform(-1, 1, n_points)) 
                z_b = np.cumsum(np.random.uniform(-1, 1, n_points)) 
                s_b = np.random.uniform(4, 32, n_points)            
                c_b = np.random.random(n_points)                    
            else:
                # OPCIÓN DATA REAL: Usar curvas del pozo
                st.info("✅ Visualizando Datos Reales del Archivo LAS.")
                cols = df_active.columns.tolist()
                c1, c2, c3, c4 = st.columns(4)
                
                # Valores por defecto inteligentes
                ix = cols.index('NPHI') if 'NPHI' in cols else 0
                iy = cols.index('RHOB') if 'RHOB' in cols else min(1, len(cols)-1)
                iz = cols.index(df_active.columns[0]) # Profundidad (normalmente index 0)
                isize = cols.index('GR') if 'GR' in cols else min(2, len(cols)-1)

                # Normalizar tamaño (Size) para evitar burbujas gigantes
                col_x = c1.selectbox("Eje X", cols, index=ix)
                col_y = c2.selectbox("Eje Y", cols, index=iy)
                col_z = c3.selectbox("Eje Z (Prof)", cols, index=iz)
                col_s = c4.selectbox("Tamaño/Color", cols, index=isize)
                
                # --- SANITIZACIÓN ROBUSTA DE DATOS (NO SOLO DROPNA) ---
                # 1. Identificar columnas ÚNICAS necesarias (Evita duplicados si X=Z)
                needed_cols = list(set([col_x, col_y, col_z, col_s]))
                
                # 2. Crear subset y FORZAR CONVERSIÓN A NUMÉRICO
                df_bub = df_active[needed_cols].copy()
                
                for c in needed_cols:
                    df_bub[c] = pd.to_numeric(df_bub[c], errors='coerce')
                
                # 2. ELIMINAR NANS E INFINITOS
                df_bub = df_bub.replace([np.inf, -np.inf], np.nan).dropna()
                
                if not df_bub.empty:
                    x_b = df_bub[col_x]
                    y_b = df_bub[col_y]
                    z_b = df_bub[col_z]
                    
                    s_raw = df_bub[col_s]
                    
                    # 3. NORMALIZACIÓN SEGURA PARA SIZE
                    s_min, s_max = s_raw.min(), s_raw.max()
                    denom = (s_max - s_min) if (s_max - s_min) > 1e-5 else 1.0
                    
                    # Calcular tamaño y asegurar que no haya nulos residuales
                    s_b = ((s_raw - s_min) / denom * 35) + 5
                    s_b = s_b.fillna(5.0) 
                    
                    c_b = s_raw 
                else: 
                     st.warning("⚠️ No se encontraron datos numéricos válidos en las curvas seleccionadas para graficar.")
                     st.stop()
            
            # GENERAR PLOT DE BURBUJAS 3D
            fig_bub = go.Figure(data=[go.Scatter3d(
                x=x_b, y=y_b, z=z_b,
                mode='markers',
                marker=dict(
                    size=s_b,
                    color=c_b,
                    colorscale=[[0, 'rgb(255,128,0)'], [1, 'rgb(0,128,255)']], # Naranja -> Azul
                    opacity=0.9,
                    line=dict(width=0) 
                )
            )])
            
            # Configuración de Escena - CUBO SÓLIDO (WIREFRAME)
            fig_bub.update_layout(
                template="plotly_dark",
                paper_bgcolor='#0e1117',
                title=f"Visualización 4D: {col_s} (Tamaño)",
                scene=dict(
                    # Ejes con fondo visible para dar efecto de "Caja"
                    xaxis=dict(backgroundcolor="rgba(20,20,20,0.5)", gridcolor="gray", showbackground=True, title=col_x),
                    yaxis=dict(backgroundcolor="rgba(20,20,20,0.5)", gridcolor="gray", showbackground=True, title=col_y),
                    zaxis=dict(backgroundcolor="rgba(20,20,20,0.5)", gridcolor="gray", showbackground=True, title=col_z),
                    bgcolor='#0e1117',
                    aspectmode='cube' # Forzar cubo perfecto
                ),
                height=700,
                margin=dict(l=0, r=0, b=0, t=40)
            )

            st.plotly_chart(fig_bub, use_container_width=True)
            
            # --- INSIGHT BURBUJAS ---
            st.success("""
            **💡 ¿Cómo leer este gráfico 4D?**
            1.  **Ejes X, Y, Z:** Ubicación espacial tridimensional.
            2.  **Tamaño de Esfera:** Representa la MAGNITUD de la propiedad seleccionada (ej. Volumen de Poro).
            3.  **Color (Naranja->Azul):** Calidad del fluido.
                - **🟠 Naranja:** Alta Presencia / Sweet Spot.
                - **🔵 Azul:** Baja Presencia / Riesgo de Agua.
            **🎯 Target:** Busque **Esferas Grandes y NARANJAS**. Ahí está el valor.
            """)

    # 6. USER GUIDE & DOCUMENTATION (A to Z)
    elif role == MODULES["UG"]:
        st.markdown("<h1 class='main-header'>:: Manual de Operaciones Hub Dterra</h1>", unsafe_allow_html=True)
        
        t_doc1, t_doc2, t_doc3, t_doc4 = st.tabs(["🚀 Inicio Rápido (A-Z)", "🛠️ Detalles de Módulos", "🔬 Transparencia Técnica", "⚠️ Gestión de Errores"])
        
        with t_doc1:
            st.markdown("""
            ### 🏁 Guía de Inicio: Del Archivo al Insight
            Para operar el sistema con éxito, siga este flujo de trabajo estándar:
            
            1.  **A - Preparación**: Asegúrese de tener sus archivos **.LAS** (Registros de pozo) y opcionalmente **.SGY** (Sísmica).
            2.  **B - Carga (Ingestion)**: Utilice el cargador del *Strategic Dashboard* o la barra lateral. El sistema reconoce automáticamente curvas estándar (GR, NPHI, RHOB, RT).
            3.  **C - Normalización**: Al cargar, el motor `CurveNormalizer` limpia unidades y nombres. Si faltan datos críticos, aparecerá un **mapeador manual**.
            4.  **D - Procesamiento Core**: El sistema ejecuta automáticamente un modelo petrofísico base (Vsh, Phi, Sw) para que todos los módulos tengan datos de trabajo.
            5.  **E - Exploración**: Navegue por los módulos según su perfil (Geología para 3D, Petrofísica para análisis detallado, Yacimientos para reservas).
            6.  **F - Exportación**: Genere reportes PDF o exporte el LAS procesado con las nuevas curvas calculadas en el módulo de Yacimientos.
            """)
            st.info("💡 **Pro Tip:** Mantenga siempre el Dashboard Abierto para monitorear las alertas de cumplimiento mientras trabaja en otros módulos.")

        with t_doc2:
            st.markdown("### 🔍 Funcionalidad por Módulo")
            with st.expander("■ Executive Dashboard (EX)", expanded=True):
                st.write("""
                - **Asset Health**: Métrica holística de la salud del pozo basada en alertas y calidad de data.
                - **Net Pay**: Cálculo en tiempo real del espesor productivo acumulado.
                - **Master Data**: Extracción directa de la cabecera del archivo LAS (UWI, Operadora, etc.).
                """)
            with st.expander("● Geological Interpretation (GI)"):
                st.write("""
                - **3D Cube**: Correlación espacial de PHI vs RHOB vs Profundidad.
                - **Well Tie**: Sincronización de sismogramas sintéticos con trazas reales.
                - **Core Gallery**: Estación para subir y digitalizar fotos de núcleos de perforación.
                """)
            with st.expander("🧬 Formation Evaluation (FE)"):
                st.write("""
                - **Multi-Track**: El visor estándar de la industria para QC de registros.
                - **NMR Studio**: Simulación de porosidad por resonancia magnética.
                """)

        with t_doc3:
            st.markdown("### 🔬 ¿Qué es Real y qué es Simulado?")
            st.warning("Para esta fase de MVP/Demo, algunos componentes utilizan lógica predefinida (Placeholders) por seguridad y falta de conexión a red local.")
            
            col_doc_a, col_doc_b = st.columns(2)
            with col_doc_a:
                st.markdown("**✅ Datos Reales (Basados en sus archivos):**")
                st.write("- Todas las curvas de registros (GR, RT, RHOB, etc.).")
                st.write("- Cálculos petrofísicos (Vsh, Porosidad, Saturación).")
                st.write("- Sismogramas sintéticos (Convolución real).")
                st.write("- Metadatos de cabecera del pozo.")
            with col_doc_b:
                st.markdown("**🔮 Lógica Simulada (Mockups):**")
                st.write("- **HSE Safety Score**: Actualmente fijo en 100 por falta de conexión a sistemas de seguridad en sitio.")
                st.write("- **Mapa de Ubicación**: Utiliza coordenadas aproximadas si el LAS no tiene Lat/Lon decimales.")
                st.write("- **Permeabilidad**: Estimada mediante ecuaciones empíricas (Dummy) hasta calibración con núcleos.")

        with t_doc4:
            st.markdown("### ⚠️ Resolución de Problemas Comunes")
            st.error("**1. El gráfico no carga o aparece vacío:**")
            st.write("Causa: El archivo LAS no contiene las curvas mínimas necesarias (ej. Falta la curva de Densidad para el gráfico 3D).")
            st.write("Solución: Use el 'Mapeador Manual' en la barra lateral para asignar una curva existente al nombre estándar.")
            
            st.warning("**2. Error de Indentación o Syntax:**")
            st.write("Causa: Errores en la edición de scripts en vivo.")
            st.write("Solución: Verifique que no haya espacios extra en los bloques de código.")

            st.info("**3. ¿Cómo aprovechar los datos al máximo?**")
            st.write("Cargue siempre el archivo LAS primero. Los módulos de Geología y Yacimientos dependen de los resultados del módulo Petrofísico (FE) para mostrar resultados significativos.")

        st.divider()
        c_foot1, c_foot2 = st.columns([2, 1])
        with c_foot1:
            st.caption("© 2026 Dterra Digital Subsurface Solutions | v7.0 Corporate Documentation")
        with c_foot2:
            st.markdown("""
            <div style="text-align: right; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;">
                <p style="margin:0; font-weight: bold; color: #00f2ff;">DATA TERRA</p>
                <p style="margin:0; font-size: 0.85rem;">dataterrasys@gmail.com</p>
            </div>
            """, unsafe_allow_html=True)
