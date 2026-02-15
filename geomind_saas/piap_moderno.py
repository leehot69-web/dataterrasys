# piap_moderno.py
"""
PIAP-MODERNO: Aplicación Streamlit completa para análisis petrofísico de archivos LAS.

Cómo usar:
1. Guardar este archivo como piap_moderno.py
2. Activar tu entorno virtual (venv) y asegurarte de instalar:
   pip install streamlit lasio pandas numpy plotly openpyxl
   (SciPy es opcional; si está instalada, se usa para una superficie 3D mejorada)
3. Ejecutar:
   streamlit run piap_moderno.py
"""

import streamlit as st
import pandas as pd
import lasio
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import tempfile
import os
import base64
from io import BytesIO

# Try optional SciPy for interpolation (not required)
try:
    from scipy.interpolate import griddata
    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False

# ================
# CONFIG STREAMLIT
# ================
st.set_page_config(page_title="PIAP-Moderno", layout="wide", initial_sidebar_state="expanded")
# Glass effect (opción 2: fondo general con transparencia alta)
st.markdown(
    """
    <style>
    body, .stApp {
        background: rgba(250, 250, 250, 0.96);
        backdrop-filter: blur(8px);
    }
    .stButton>button {
        background: rgba(255,255,255,0.45);
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.6);
        box-shadow: 0 6px 20px rgba(0,0,0,0.06);
        transition: all 0.18s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.09);
    }
    .stSidebar .stButton>button {
        width: 100%;
    }
    .stExpander {
        background: rgba(255,255,255,0.45);
        border-radius: 12px;
        padding: 6px;
        border: 1px solid rgba(255,255,255,0.6);
    }
    .css-1lcbmhc.e1fqkh3o1 { overflow-x: auto; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===========
# UTILIDADES
# ===========
def get_temp_las_from_uploaded(uploaded_file):
    """
    Escribe el archivo subido a disco temporal y lo lee con lasio.
    Esto evita el error 'a bytes-like object is required, not str'.
    """
    if uploaded_file is None:
        return None
    try:
        # si uploaded_file es un UploadedFile, getvalue() devuelve bytes
        b = uploaded_file.getvalue()
        # use BytesIO directly with lasio or save to temp file (some lasio versions prefer filename)
        try:
            las = lasio.read(BytesIO(b))
            return las
        except Exception:
            # fallback a archivo temporal por compatibilidad
            with tempfile.NamedTemporaryFile(delete=False, suffix=".las") as tmp:
                tmp.write(b)
                tmp_path = tmp.name
            las = lasio.read(tmp_path)
            os.unlink(tmp_path)
            return las
    except Exception as e:
        raise RuntimeError(f"Error preparando LAS desde upload: {e}")

def df_safe_from_las(las):
    """
    Devuelve DataFrame y asegura que el índice sea numérico (profundidad).
    """
    df = las.df()
    # si el índice no es float, intentar convertir
    try:
        df.index = pd.to_numeric(df.index)
    except Exception:
        pass
    return df

def make_download_link(df, filename="datos.csv"):
    csv = df.to_csv(index=True)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Descargar {filename}</a>'

# ==========================
# CÁLCULOS PETROFÍSICOS
# ==========================
def calcular_vsh(gr_series, gr_min=None, gr_max=None):
    """Calcula Vsh (linear y Clavier)"""
    if gr_series is None or len(gr_series) == 0:
        return None, None
    gr_min = gr_series.min() if gr_min is None else gr_min
    gr_max = gr_series.max() if gr_max is None else gr_max
    denom = (gr_max - gr_min) if (gr_max - gr_min) != 0 else 1.0
    vsh_linear = (gr_series - gr_min) / denom
    vsh_linear = np.clip(vsh_linear, 0, 1)
    # Clavier empirical
    vsh_clavier = 1.7 - np.sqrt(3.38 - (vsh_linear + 0.7) ** 2)
    vsh_clavier = np.clip(vsh_clavier, 0, 1)
    return vsh_linear, vsh_clavier

def calcular_porosidad_rhob(rhob_series, nphi_series=None):
    """
    Porosidad por densidad y combinación con neutrón (si existe)
    RHOB_FRAME: matrix/mineral ~2.65 ; fluid ~1.0
    """
    if rhob_series is None or len(rhob_series) == 0:
        return None, None
    RHO_MATRIX = 2.65
    RHO_FLUID = 1.0
    phi_density = (RHO_MATRIX - rhob_series) / (RHO_MATRIX - RHO_FLUID)
    phi_density = np.clip(phi_density, 0, 0.5)
    if nphi_series is not None:
        phi_neutron = nphi_series
        phi_eff = (phi_density + phi_neutron) / 2.0
    else:
        phi_eff = phi_density
    return phi_eff, phi_density

def calcular_sw_archie(rt_series, phi_eff, rw=0.05, a=1.0, m=2.0, n=2.0):
    """Calcula saturación de agua por Archie"""
    phi_safe = np.where(phi_eff > 0.01, phi_eff, 0.01)
    rt_safe = np.where(rt_series > 0.01, rt_series, 0.01)
    r0 = (a / (phi_safe ** m)) * rw
    sw = np.clip((r0 / rt_safe) ** (1.0 / n), 0.01, 1.0)
    return sw

def estimar_permeabilidad_empirica(phi_eff, method="coates", sw_irreducible=0.2):
    """Estimaciones empíricas de permeabilidad (mD aproximado)"""
    phi_safe = np.where(phi_eff > 0.01, phi_eff, 0.01)
    if method == "coates":
        k = (100.0 * (phi_safe ** 2) * ((1 - sw_irreducible) / sw_irreducible)) ** 2
    elif method == "tixier":
        k = (250.0 * (phi_safe ** 3) / sw_irreducible) ** 2
    else:  # timur
        k = 0.136 * phi_safe ** 4.4 / (sw_irreducible ** 2)
    k = np.clip(k, 1e-6, 1e6)
    return k

# ==========================
# ANÁLISIS DE INTERVALOS
# ==========================
def identificar_intervalos(df, gr_cut=85, phi_cut=0.05, rt_cut=10.0):
    """
    Detecta intervalos candidatos (regla combinada).
    Retorna DataFrame con intervalos (puntos) y criterios usados.
    """
    if df is None or df.empty:
        return pd.DataFrame()
    # Prepare columns presence
    has_gr = "GR" in df.columns
    has_phi = "PHI" in df.columns or "NPHI" in df.columns
    has_rt = "RT" in df.columns
    # Compose selection
    sel = pd.Series(True, index=df.index)
    used = []
    if has_gr:
        sel = sel & (df["GR"] < gr_cut)
        used.append("GR")
    if has_phi:
        phi_col = "PHI" if "PHI" in df.columns else "NPHI"
        sel = sel & (df[phi_col] > phi_cut)
        used.append(phi_col)
    if has_rt:
        sel = sel & (df["RT"] > rt_cut)
        used.append("RT")
    cand = df.loc[sel].copy()
    # Build results
    if cand.empty:
        return pd.DataFrame()
    rows = []
    for depth, row in cand.iterrows():
        item = {"Profundidad": depth}
        for c in used:
            item[c] = row.get(c, np.nan)
        item["Arena_Potencial"] = True
        item["HC_Candidato"] = True if has_rt else False
        rows.append(item)
    return pd.DataFrame(rows)

# ==========================
# VISUALIZACIÓN: tracks y crossplots y 3D
# ==========================
def grafico_multi_track(df, intervalos, curvas_preferidas=None, title="Perfil de Pozo"):
    """
    Muestra múltiples curvas en tracks separados como gráfico Plotly.
    curvas_preferidas: lista opcional para ordenar tracks.
    """
    if df is None or df.empty:
        return None
    cols = df.columns.tolist()
    # If prefered provided, put them first if exist
    if curvas_preferidas:
        cols_sorted = [c for c in curvas_preferidas if c in cols] + [c for c in cols if c not in (curvas_preferidas or [])]
    else:
        cols_sorted = cols
    # Limit number of tracks to avoid overcrowding (Plotly overlay)
    fig = make_subplots(rows=1, cols=len(cols_sorted), shared_yaxes=True, horizontal_spacing=0.02,
                        subplot_titles=cols_sorted)
    for i, col in enumerate(cols_sorted, start=1):
        series = df[col].dropna()
        if series.empty:
            continue
        # Normalize x-range per track for visual consistency (but keep actual values)
        fig.add_trace(go.Scatter(x=series, y=series.index, mode="lines", name=col), row=1, col=i)
        # set axis title per subplot
        fig.update_xaxes(title_text=col, row=1, col=i)
    # Mark intervals as colored rectangles across all columns
    if intervalos is not None and not intervalos.empty:
        # use main xref as paper so rectangle spans track width
        for _, r in intervalos.iterrows():
            fig.add_shape(type="rect",
                          xref="paper", yref="y",
                          x0=0, x1=1,
                          y0=r["Profundidad"] - 0.25, y1=r["Profundidad"] + 0.25,
                          fillcolor="rgba(255, 235, 59, 0.25)",
                          line_width=0)
    fig.update_yaxes(autorange="reversed", title_text="Profundidad (m)")
    fig.update_layout(title=title, height=850, showlegend=False)
    return fig

def crear_crossplot(df, x_col, y_col, z_col=None):
    if df is None or df.empty:
        return None
    if x_col not in df.columns or y_col not in df.columns:
        return None
    if z_col and z_col in df.columns:
        fig = px.scatter(df, x=x_col, y=y_col, color=z_col, color_continuous_scale="Viridis", opacity=0.8)
    else:
        fig = px.scatter(df, x=x_col, y=y_col, opacity=0.8)
    fig.update_layout(title=f"Crossplot: {y_col} vs {x_col}", height=650)
    return fig

def grafico_3d_surface_from_curve(df, curve_name):
    """
    Genera una visualización 3D tipo 'superficie' a partir de una curva:
    - eje X: índice de punto (o sección lateral)
    - eje Y: profundidad
    - eje Z: valor de la curva
    Si no hay densidad de datos suficiente, devuelve scatter 3D de puntos.
    """
    if df is None or df.empty or curve_name not in df.columns:
        return None
    z = df[curve_name].values
    y = df.index.values  # profundidad
    x = np.arange(len(z))  # lateral index (simple)
    # Build grid: we'll produce a thin mesh by replicating curve lateral (for visualization)
    # If SciPy available and user wants fancy grid, one could interpolate. We'll simply tile.
    X, Y = np.meshgrid(x, y)
    Z = np.tile(z.reshape(-1, 1), (1, len(x)))
    fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y, colorscale="Viridis", showscale=True)])
    fig.update_layout(title=f"3D Surface approximada: {curve_name}", scene=dict(
        xaxis_title="Lateral (indice)",
        yaxis_title="Profundidad",
        zaxis_title=curve_name
    ), height=700)
    # If insufficient resolution, also add scatter overlay
    if len(z) < 30:
        fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode="markers+lines",
                                   marker=dict(size=2, color=z, colorscale="Viridis")))
    return fig

def grafico_3d_scatter_xyz(df, x_col, y_col, z_col):
    """3D scatter para cualquier trio de columnas"""
    if df is None or df.empty:
        return None
    if not (x_col in df.columns and y_col in df.columns and z_col in df.columns):
        return None
    fig = px.scatter_3d(df, x=x_col, y=y_col, z=z_col, color=z_col, opacity=0.8)
    fig.update_layout(height=750, title=f"3D: {z_col} coloreado")
    return fig

# ===========================
# INTERFAZ PRINCIPAL (STREAMLIT)
# ===========================
st.title("🛢️ PIAP-Moderno — Análisis Petrofísico")

# Sidebar: configuración y carga
with st.sidebar:
    st.header("📂 Datos y Configuración")
    uploaded = st.file_uploader("Sube uno o varios archivos LAS", type=["las"], accept_multiple_files=False)
    st.markdown("---")
    st.subheader("⚙️ Parámetros (Archie & cortes)")
    rw = st.number_input("Rw (Ohm·m)", value=0.05, step=0.01, format="%.3f")
    a_archie = st.number_input("Constante a", value=1.0, step=0.1)
    m_archie = st.number_input("Exponente m", value=2.0, step=0.1)
    n_archie = st.number_input("Exponente n", value=2.0, step=0.1)
    st.markdown("**Cortes para detección**")
    gr_cut = st.number_input("GR < (API)", value=85.0)
    phi_cut = st.number_input("PHI > (fracción)", value=0.05, step=0.01)
    rt_cut = st.number_input("RT > (ohm·m)", value=10.0, step=1.0)
    st.markdown("---")
    if st.button("🔄 Reiniciar vista"):
        st.experimental_rerun()

# Main content
if uploaded:
    try:
        las = get_temp_las_from_uploaded(uploaded)
    except Exception as e:
        st.error(f"No se pudo cargar el LAS: {e}")
        las = None

    if las is not None:
        st.success(f"Archivo cargado: {uploaded.name}")
        # Header summary
        try:
            header = las.header
            # Produce DataFrame sencilla del header
            hdr_list = []
            for section_name, section in header.items():
                # las.header is sometimes a dict of LASSection; iterate items
                try:
                    for item in section:
                        hdr_list.append([section_name, item.mnemonic, str(item.value), str(item.unit), str(item.descr)])
                except Exception:
                    # If section is mapping
                    for k, v in section.items():
                        hdr_list.append([section_name, str(k), str(v), "", ""])
            hdr_df = pd.DataFrame(hdr_list, columns=["Section", "Mnemonic", "Value", "Unit", "Description"])
            st.subheader("🔹 Encabezado (Header) del LAS")
            st.dataframe(hdr_df, use_container_width=True, height=240)
        except Exception as e:
            st.warning(f"No se pudo leer header completo: {e}")

        # Convert LAS to DataFrame
        try:
            df = df_safe_from_las(las)
            df = df.dropna(how="all")
            st.subheader("🔹 Curvas disponibles")
            if df.empty:
                st.warning("El LAS no contiene curvas legibles o está vacío.")
            else:
                # show up to 20 column names in a neat table
                cols = pd.DataFrame({"Curvas": df.columns})
                st.dataframe(cols.T, use_container_width=True, height=120)
                # metrics
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Curvas detectadas", len(df.columns))
                with c2:
                    st.metric("Puntos", len(df))
                with c3:
                    st.metric("Prof. mínima", f"{df.index.min():.2f}")
                with c4:
                    st.metric("Prof. máxima", f"{df.index.max():.2f}")
        except Exception as e:
            st.error(f"Error creando DataFrame desde LAS: {e}")
            df = pd.DataFrame()

        # Análisis rápido de intervalos
        if not df.empty:
            st.header("🔎 Detección Rápida de Intervalos")
            intervalos = identificar_intervalos(df, gr_cut=gr_cut, phi_cut=phi_cut, rt_cut=rt_cut)
            if intervalos.empty:
                st.info("No se detectaron intervalos con los criterios actuales.")
            else:
                st.success(f"{len(intervalos)} intervalos candidatos detectados")
                st.dataframe(intervalos, use_container_width=True)
                st.markdown(make_download_link(intervalos, "intervalos_potenciales.csv"), unsafe_allow_html=True)
        else:
            intervalos = pd.DataFrame()

        # Advanced calculations (if required curves exist)
        st.header("🧮 Cálculos Petrofísicos")
        # compute vsh, porosity, sw, permeability when curves available
        try:
            # Vsh
            if "GR" in df.columns:
                vsh_lin, vsh_cla = calcular_vsh(df["GR"])
                df["VSH_LINEAR"] = vsh_lin
                df["VSH_CLAVIER"] = vsh_cla
                st.write("Vsh calculado y agregado al DataFrame.")
            # porosity
            if "RHOB" in df.columns:
                nphi = df["NPHI"] if "NPHI" in df.columns else None
                phi_eff, phi_den = calcular_porosidad_rhob(df["RHOB"], nphi)
                df["PHI_EFFECTIVE"] = phi_eff
                df["PHI_DENSITY"] = phi_den
                st.write("Porosidad estimada agregada.")
            # Sw and permeability
            if "RT" in df.columns and "PHI_EFFECTIVE" in df.columns:
                df["SW_ARCHIE"] = calcular_sw_archie(df["RT"].values, df["PHI_EFFECTIVE"].values, rw=rw, a=a_archie, m=m_archie, n=n_archie)
                df["PERMEABILITY_EST"] = estimar_permeabilidad_empirica(df["PHI_EFFECTIVE"].values)
                st.write("Saturación y permeabilidad estimadas.")
        except Exception as e:
            st.warning(f"Error en cálculos avanzados: {e}")

        # VISUALIZACIONES - pestañas
        st.header("📊 Visualizaciones")
        tab1, tab2, tab3, tab4 = st.tabs(["Curvas (tracks)", "Crossplots", "3D / Superficie", "Reporte & Export"])

        with tab1:
            st.subheader("Curvas tipo track")
            # user selects curves to view
            default_curves = [c for c in ["GR", "NPHI", "PHI", "RHOB", "RT"] if c in df.columns]
            choices = st.multiselect("Selecciona curvas para visualizar (ordenadas a la izquierda):", options=df.columns.tolist(), default=default_curves[:3])
            if choices:
                fig_tracks = grafico_multi_track(df, intervalos, curvas_preferidas=choices, title="Visualización multi-track")
                if fig_tracks:
                    st.plotly_chart(fig_tracks, use_container_width=True)
                else:
                    st.warning("No se pudo generar el gráfico multi-track.")
            else:
                st.info("Selecciona al menos una curva para visualizar.")

        with tab2:
            st.subheader("Cross-plot profesional")
            # choose x,y,z
            available = [c for c in df.columns if not df[c].isna().all()]
            if len(available) < 2:
                st.warning("No hay suficientes curvas con datos para cross-plot.")
            else:
                x_col = st.selectbox("Eje X", available, index=0)
                y_col = st.selectbox("Eje Y", available, index=min(1, len(available)-1))
                z_col = st.selectbox("Color (opcional)", [""] + available, index=0)
                if st.button("Generar crossplot"):
                    cross = crear_crossplot(df, x_col, y_col, z_col if z_col != "" else None)
                    if cross:
                        st.plotly_chart(cross, use_container_width=True)
                        try:
                            corr = df[x_col].corr(df[y_col])
                            st.metric("Correlación (Pearson)", f"{corr:.3f}")
                        except Exception:
                            pass
                    else:
                        st.warning("No se pudo crear crossplot con esas columnas.")

        with tab3:
            st.subheader("Visualización 3D")
            # offer two modes: surface from a single curve or scatter from three columns
            mode = st.radio("Modo 3D", ["Surface from curve", "Scatter XYZ"], index=0, horizontal=True)
            if mode == "Surface from curve":
                curve3d = st.selectbox("Selecciona curva para superficie 3D (z)", [c for c in df.columns])
                if st.button("Generar superficie 3D"):
                    fig3d = grafico_3d_surface_from_curve(df, curve3d)
                    if fig3d:
                        st.plotly_chart(fig3d, use_container_width=True)
                    else:
                        st.warning("No se pudo generar la superficie 3D.")
            else:
                # three-axis scatter
                if len(available) >= 3:
                    x3 = st.selectbox("X", available, index=0)
                    y3 = st.selectbox("Y", available, index=1)
                    z3 = st.selectbox("Z (color)", available, index=2)
                    if st.button("Generar scatter 3D"):
                        fig3dsc = grafico_3d_scatter_xyz(df, x3, y3, z3)
                        if fig3dsc:
                            st.plotly_chart(fig3dsc, use_container_width=True)
                        else:
                            st.warning("No se pudo generar scatter 3D con esas columnas.")
                else:
                    st.warning("Se requieren al menos 3 curvas con datos para scatter 3D.")

        with tab4:
            st.subheader("Reporte y Export")
            # Download processed dataframe (with calculated columns) as CSV
            st.markdown("🔽 Descargar datos procesados (CSV)")
            if not df.empty:
                tmp_name = "pozo_procesado.csv"
                st.markdown(make_download_link(df, tmp_name), unsafe_allow_html=True)
            else:
                st.info("No hay datos para exportar.")
            st.markdown("---")
            st.subheader("Resumen ejecutivo")
            # quick summary metrics
            colA, colB, colC, colD = st.columns(4)
            with colA:
                st.metric("Curvas", len(df.columns))
            with colB:
                st.metric("Puntos", len(df))
            with colC:
                st.metric("Intervalos detectados", len(intervalos) if not intervalos.empty else 0)
            with colD:
                if "PHI_EFFECTIVE" in df.columns:
                    st.metric("Φ promedio", f"{df['PHI_EFFECTIVE'].mean():.3f}")
                else:
                    st.metric("Φ promedio", "N/A")

            st.markdown("---")
            st.info("✅ Reporte resumido listo. Para reportes PDF/HTML requiere paso adicional (generación con librerías tipo reportlab/xhtml2pdf).")

    else:
        st.error("No fue posible leer el archivo LAS subido. Verifica el formato.")

else:
    # Pantalla inicial
    st.markdown(
        """
        # Bienvenido a PIAP-Moderno
        Sube un archivo LAS en la barra lateral para comenzar.
        - Módulos: Resumen, Curvas, Cross-plots, 3D, Reportes.
        - Los cálculos avanzados se habilitan si las curvas necesarias (GR, RHOB, NPHI, RT) están presentes.
        """
    )

# Footer
st.divider()
f1, f2, f3 = st.columns(3)
with f1:
    st.caption("PIAP-Moderno • Versión local")
with f2:
    st.caption("Soporte: soporte@piap-a.local")
with f3:
    st.caption("Hecho con ❤️ • Streamlit + Plotly + lasio")
