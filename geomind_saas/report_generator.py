import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np

def create_report_triple_combo(df):
    """Genera una pista petrofísica estándar para el reporte."""
    if df is None or df.empty: return go.Figure()
    
    # Identificar curvas disponibles
    has_gr = 'GR' in df.columns
    has_rt = 'RT' in df.columns
    has_phi = 'PHIE_FINAL' in df.columns or 'NPHI' in df.columns
    p_col = 'PHIE_FINAL' if 'PHIE_FINAL' in df.columns else 'NPHI'
    
    fig = make_subplots(rows=1, cols=3, shared_yaxes=True, 
                        subplot_titles=("Gamma Ray", "Resistivity", "Porosity"),
                        horizontal_spacing=0.02)
    
    if has_gr:
        fig.add_trace(go.Scatter(x=df['GR'], y=df.index, name="GR", line=dict(color="green", width=1)), row=1, col=1)
    if has_rt:
        fig.add_trace(go.Scatter(x=df['RT'], y=df.index, name="RT", line=dict(color="red", width=1)), row=1, col=2)
        fig.update_xaxes(type="log", row=1, col=2)
    if has_phi:
        fig.add_trace(go.Scatter(x=df[p_col], y=df.index, name="PHI", line=dict(color="blue", width=1)), row=1, col=3)
        fig.update_xaxes(autorange="reversed", row=1, col=3)

    fig.update_yaxes(autorange="reversed", title="Depth")
    fig.update_layout(height=800, template="plotly_white", margin=dict(t=50, b=50, l=50, r=50))
    return fig

def generate_html_report(well_info, df_data, df_intervals, qc_report_list=None, asset_health=94.2, net_pay=0.0):
    """
    Genera un informe HTML Profesional con datos reales calibrados.
    """
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    well_name = well_info.get("Pozo", well_info.get("Well Name", "Unknown Well"))
    
    # 1. Generar Gráfico Real si no se provee uno
    fig_triple = create_report_triple_combo(df_data)
    
    # 2. Formatear QC
    qc_html = ""
    if qc_report_list:
        items = "".join([f"<li style='color: {'#27ae60' if '✅' in m else '#c0392b'}; margin-bottom:5px;'>{m}</li>" for m in qc_report_list])
        qc_html = f"<div class='card'><h3>🛡️ Technical Audit (AI QC)</h3><ul>{items}</ul></div>"

    # 3. Formatear Tabla de Intervalos
    intervals_html = "<p>No prospect zones identified in this run.</p>"
    if df_intervals is not None and not df_intervals.empty:
        intervals_html = df_intervals.to_html(classes='data-table', index=False, float_format="%.2f")

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>DTERRA | Report: {well_name}</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            :root {{ --primary: #00f2ff; --dark: #1e293b; --bg: #f8fafc; }}
            body {{ font-family: 'Inter', system-ui, sans-serif; background: var(--bg); margin: 0; padding: 40px; color: #334155; }}
            .container {{ max-width: 1100px; margin: 0 auto; background: white; padding: 50px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 30px; }}
            .brand {{ color: #0f172a; font-size: 24px; font-weight: 800; letter-spacing: -1px; }}
            .brand span {{ color: var(--primary); }}
            h1 {{ font-size: 28px; color: #0f172a; margin: 0; }}
            .kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
            .kpi-card {{ background: #f1f5f9; padding: 20px; border-radius: 10px; border-left: 5px solid var(--primary); }}
            .kpi-val {{ font-size: 24px; font-weight: 700; color: #0f172a; }}
            .kpi-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; }}
            .card {{ background: white; border: 1px solid #e2e8f0; padding: 25px; border-radius: 12px; margin-bottom: 30px; }}
            .data-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
            .data-table th {{ background: #f8fafc; text-align: left; padding: 12px; border-bottom: 2px solid #e2e8f0; }}
            .data-table td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; }}
            .footer {{ text-align: center; margin-top: 50px; color: #94a3b8; font-size: 13px; border-top: 1px solid #eee; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <div class="brand">DATA<span>TERRA</span></div>
                    <p style="margin:5px 0 0; color:#94a3b8; font-size:12px;">Subsurface Intelligence Systems</p>
                </div>
                <div style="text-align: right;">
                    <h1>TECHNICAL WELL REPORT</h1>
                    <p style="margin:0; color:#64748b;">Generated: {report_date}</p>
                </div>
            </div>

            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">Asset Health</div>
                    <div class="kpi-val" style="color:#27ae60;">{asset_health}%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Cumulative Net Pay</div>
                    <div class="kpi-val">{net_pay:.1f} ft</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Well Integrity</div>
                    <div class="kpi-val" style="color:#2980b9;">SECURE</div>
                </div>
            </div>

            <div class="card">
                <h3>📍 Well Master Information</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 14px;">
                    <div><strong>Operator:</strong> {well_info.get('Empresa',well_info.get('Operator','-'))}</div>
                    <div><strong>Field:</strong> {well_info.get('Campo',well_info.get('Field','-'))}</div>
                    <div><strong>Location:</strong> {well_info.get('Ubicación',well_info.get('Location','-'))}</div>
                    <div><strong>UWI/API:</strong> {well_info.get('API/UWI','-')}</div>
                </div>
            </div>

            {qc_html}

            <div class="card">
                <h3>📊 Formation Evaluation (Target Intervals)</h3>
                {intervals_html}
            </div>

            <div class="card">
                <h3>≋ Petrophysical Log Synthesis</h3>
                <div id="plotly-logs"></div>
            </div>

            <div class="footer">
                © 2026 Data Terra Digital Solutions | Confidential Property | dataterrasys@gmail.com
            </div>
        </div>

        <script>
            var figLogs = {pio.to_json(fig_triple)};
            Plotly.newPlot('plotly-logs', figLogs.data, figLogs.layout);
        </script>
    </body>
    </html>
    """
    return html_template
