import React, { useState } from 'react';
import { X, FileText, Globe, Download, Share2, Copy, Check } from 'lucide-react';
import { motion } from 'framer-motion';

// ============================================================
// Helper: compute stats from array
// ============================================================
const arrStats = (arr) => {
    if (!arr || arr.length === 0) return { min: 0, max: 0, mean: 0, std: 0, n: 0 };
    const valid = arr.filter(v => isFinite(v));
    const n = valid.length;
    if (n === 0) return { min: 0, max: 0, mean: 0, std: 0, n: 0 };
    const min = Math.min(...valid);
    const max = Math.max(...valid);
    const mean = valid.reduce((a, b) => a + b, 0) / n;
    const std = Math.sqrt(valid.reduce((a, b) => a + (b - mean) ** 2, 0) / n);
    return { min, max, mean, std, n };
};

// ============================================================
// GENERADOR DE REPORTE HTML COMPLETO (con datos reales + resúmenes de gráficos)
// ============================================================
const generateHTMLReport = (data) => {
    if (!data) return '';
    const { well_info, kpis, pay_zones, audit, analysis_meta, curves, depths } = data;
    const wi = well_info || {};
    const date = new Date().toLocaleString();
    const wellName = wi.well_name || 'Sin nombre';

    // Generar tabla de pay zones
    const payTable = (pay_zones && pay_zones.length > 0) ? pay_zones.map((z, i) => `
        <tr>
            <td>${i + 1}</td>
            <td>${z.Top?.toFixed(1)}</td>
            <td>${z.Base?.toFixed(1)}</td>
            <td><strong>${z.Espesor_ft?.toFixed(1)}</strong></td>
            <td>${(z.Porosidad_Avg * 100).toFixed(1)}%</td>
            <td>${(z.Sw_Avg * 100).toFixed(1)}%</td>
            <td><span class="badge ${z.Calidad === 'Excelente' ? 'badge-green' : z.Calidad === 'Bueno' ? 'badge-yellow' : 'badge-orange'}">${z.Calidad}</span></td>
        </tr>`).join('') : '<tr><td colspan="7">Sin zonas de pago detectadas</td></tr>';

    const auditItems = (audit || []).map(msg => {
        const cls = msg.includes('❌') ? 'audit-error' : msg.includes('⚠️') ? 'audit-warn' : 'audit-ok';
        return `<div class="audit-item ${cls}">${msg}</div>`;
    }).join('');

    const curveTags = (data.available_curves || []).map(c => `<span class="curve-tag">${c}</span>`).join('');

    // ---------- Chart interpretations ----------
    const depthRange = depths?.length > 0 ? `${depths[0]?.toFixed(0)} – ${depths[depths.length - 1]?.toFixed(0)} ft` : 'N/A';
    const numPoints = depths?.length || 0;

    // Lithology
    const vshS = arrStats(curves?.vsh);
    const phiS = arrStats(curves?.phi);
    const swS = arrStats(curves?.sw);
    const grS = arrStats(curves?.gr);
    const permS = arrStats(curves?.perm);
    const shS = arrStats(curves?.sh);
    const cleanCount = curves?.vsh ? curves.vsh.filter(v => v < 0.3).length : 0;
    const shaleCount = curves?.vsh ? curves.vsh.filter(v => v > 0.6).length : 0;
    const cleanPct = numPoints > 0 ? ((cleanCount / numPoints) * 100).toFixed(0) : 0;
    const shalePct = numPoints > 0 ? ((shaleCount / numPoints) * 100).toFixed(0) : 0;

    // Geophysics
    const geo = data.geophysics || {};
    const impS = arrStats(geo.impedance);
    const rcS = arrStats(geo.reflectivity);
    const synS = arrStats(geo.synthetic);

    // Radar
    const radar = data.radar || {};
    const radarAvg = radar.scores ? (radar.scores.reduce((a, b) => a + b, 0) / radar.scores.length) : 0;
    const radarItems = radar.categories ? radar.categories.map((c, i) =>
        `<div class="info-row"><span class="k">${c}</span><span class="v" style="color:${radar.scores[i] > 0.6 ? '#4ade80' : '#fbbf24'}">${(radar.scores[i] * 100).toFixed(0)}%</span></div>`
    ).join('') : '';

    // Production
    const prod = data.production || {};
    const totalBarrels = prod.barrels ? prod.barrels.reduce((a, b) => a + b, 0) : 0;
    const peakRate = prod.barrels ? Math.max(...prod.barrels) : 0;

    // Correlations
    const corr = data.correlations || {};
    const topCorrs = (corr.pairs || []).slice(0, 6).map(p =>
        `<div class="info-row"><span class="k">${p.x} ↔ ${p.y}</span><span class="v" style="color:${Math.abs(p.r) > 0.7 ? '#4ade80' : '#fbbf24'}">R = ${p.r}</span></div>`
    ).join('');

    // Histograms
    const hists = data.histograms || {};
    const histSummary = Object.keys(hists).map(k => {
        const h = hists[k];
        const barX = h.bin_edges.slice(0, -1).map((v, i) => (v + h.bin_edges[i + 1]) / 2);
        const total = h.counts.reduce((a, b) => a + b, 0);
        let sum = 0; barX.forEach((x, i) => { sum += x * h.counts[i]; });
        const mean = total > 0 ? sum / total : 0;
        return `<div class="info-row"><span class="k">${k}</span><span class="v">μ = ${mean.toFixed(3)} (${total} muestras)</span></div>`;
    }).join('');

    // Build section helper
    const chartSection = (title, icon, interpretation, method, statsHtml) => `
        <div class="section chart-section">
            <h2>${icon} ${title}</h2>
            ${statsHtml ? `<div class="grid-4">${statsHtml}</div>` : ''}
            <div class="interp-box">
                <div class="interp-label">📊 INTERPRETACIÓN</div>
                <p>${interpretation}</p>
            </div>
            <div class="method-box">
                <div class="method-label">🔧 METODOLOGÍA</div>
                <p>${method}</p>
            </div>
        </div>`;

    return `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Petrofísico — ${wi.well_name || 'Pozo'}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0a0a0a; color: #e5e5e5; padding: 30px; line-height: 1.6; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { text-align: center; padding: 40px 20px; border-bottom: 2px solid #1a1a1a; margin-bottom: 30px; }
        .header h1 { font-size: 2.2rem; font-weight: 900; letter-spacing: -1px; }
        .header h1 span { color: #00f2ff; }
        .header .subtitle { color: #666; font-size: 0.85rem; margin-top: 8px; }
        .header .well-name { font-size: 1.4rem; color: #00f2ff; margin-top: 15px; font-weight: 800; }
        .section { margin-bottom: 30px; padding: 25px; background: #111; border-radius: 16px; border: 1px solid #1a1a1a; }
        .section h2 { font-size: 0.75rem; font-weight: 900; color: #00f2ff; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 18px; }
        .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
        .kpi-card { background: #0a0a0a; padding: 16px; border-radius: 12px; border: 1px solid #1a1a1a; }
        .kpi-card .label { font-size: 0.65rem; font-weight: 800; color: #555; letter-spacing: 1px; text-transform: uppercase; }
        .kpi-card .value { font-size: 1.6rem; font-weight: 900; margin-top: 4px; }
        .kpi-card .unit { font-size: 0.7rem; color: #666; font-weight: 600; }
        table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
        th { text-align: left; padding: 10px 12px; font-size: 0.65rem; font-weight: 800; color: #555; letter-spacing: 1px; text-transform: uppercase; border-bottom: 1px solid #222; }
        td { padding: 10px 12px; border-bottom: 1px solid #111; }
        .info-row { display: flex; justify-content: space-between; padding: 8px 14px; background: #0a0a0a; border-radius: 8px; margin-bottom: 4px; font-size: 0.8rem; }
        .info-row .k { color: #666; font-weight: 600; }
        .info-row .v { font-weight: 800; }
        .badge { padding: 3px 12px; border-radius: 20px; font-size: 0.65rem; font-weight: 800; }
        .badge-green { background: rgba(74,222,128,0.15); color: #4ade80; }
        .badge-yellow { background: rgba(251,191,36,0.15); color: #fbbf24; }
        .badge-orange { background: rgba(251,146,60,0.15); color: #fb923c; }
        .audit-item { padding: 8px 14px; border-radius: 8px; margin-bottom: 5px; font-size: 0.8rem; }
        .audit-ok { background: rgba(74,222,128,0.06); border: 1px solid rgba(74,222,128,0.15); }
        .audit-warn { background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.15); }
        .audit-error { background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.15); }
        .curve-tag { display: inline-block; padding: 4px 12px; background: rgba(0,242,255,0.08); border: 1px solid rgba(0,242,255,0.15); border-radius: 20px; font-size: 0.7rem; font-weight: 700; color: #00f2ff; margin: 3px; }
        .chart-section { border-left: 3px solid #00f2ff; }
        .interp-box { padding: 14px 18px; background: rgba(74,222,128,0.04); border-radius: 10px; border: 1px solid rgba(74,222,128,0.1); margin: 10px 0; }
        .interp-label { font-size: 0.65rem; font-weight: 900; color: #4ade80; letter-spacing: 1px; margin-bottom: 6px; }
        .interp-box p { font-size: 0.8rem; line-height: 1.7; opacity: 0.85; }
        .method-box { padding: 14px 18px; background: rgba(251,191,36,0.04); border-radius: 10px; border: 1px solid rgba(251,191,36,0.1); margin: 10px 0; }
        .method-label { font-size: 0.65rem; font-weight: 900; color: #fbbf24; letter-spacing: 1px; margin-bottom: 6px; }
        .method-box p { font-size: 0.8rem; line-height: 1.7; opacity: 0.75; }
        .section-divider { text-align: center; padding: 20px; color: #333; font-size: 0.7rem; border-top: 2px solid #1a1a1a; margin: 30px 0; }
        .section-divider h3 { color: #00f2ff; font-size: 0.85rem; letter-spacing: 3px; }
        .footer { text-align: center; padding: 30px; color: #333; font-size: 0.7rem; border-top: 1px solid #1a1a1a; margin-top: 30px; }
        @media (max-width: 768px) {
            body { padding: 15px; }
            .header h1 { font-size: 1.5rem; }
            .grid-4 { grid-template-columns: 1fr 1fr; }
            .kpi-card .value { font-size: 1.2rem; }
        }
        @media print {
            body { background: white; color: #222; padding: 20px; }
            .section { border: 1px solid #ddd; background: #fafafa; page-break-inside: avoid; }
            .chart-section { border-left: 3px solid #0066cc; }
            .kpi-card { border: 1px solid #ddd; background: white; }
            .header h1 span { color: #0066cc; }
            .interp-box { background: #f0f9f0; border: 1px solid #cce5cc; }
            .method-box { background: #fefce8; border: 1px solid #fde68a; }
            .interp-label { color: #15803d; }
            .method-label { color: #a16207; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DATA<span>TERRA</span></h1>
            <p class="subtitle">Reporte Petrofísico Integral • Generado: ${date}</p>
            <p class="well-name">${wellName}</p>
        </div>

        <!-- WELL INFO -->
        <div class="section">
            <h2>Información del Pozo</h2>
            <div class="grid-4">
                ${[['Pozo', wi.well_name], ['Campo', wi.field], ['Operadora', wi.operator], ['Servicio', wi.service], ['Ubicación', wi.location], ['Fecha', wi.date], ['País', wi.country], ['Provincia', wi.province]].map(([k, v]) =>
        `<div class="info-row"><span class="k">${k}</span><span class="v">${v || '-'}</span></div>`
    ).join('')}
            </div>
        </div>

        <!-- KPIs -->
        <div class="section">
            <h2>Indicadores Clave (KPIs)</h2>
            <div class="grid-4">
                <div class="kpi-card"><div class="label">Prof. Máxima</div><div class="value">${kpis?.max_depth || 0} <span class="unit">FT</span></div></div>
                <div class="kpi-card"><div class="label">Porosidad Prom.</div><div class="value" style="color:#22d3ee">${kpis?.avg_phi || 0}<span class="unit">%</span></div></div>
                <div class="kpi-card"><div class="label">Vshale Prom.</div><div class="value" style="color:#fbbf24">${kpis?.avg_vsh || 0}<span class="unit">%</span></div></div>
                <div class="kpi-card"><div class="label">Sw Promedio</div><div class="value" style="color:#3b82f6">${kpis?.avg_sw || 0}<span class="unit">%</span></div></div>
                <div class="kpi-card"><div class="label">Permeabilidad</div><div class="value" style="color:#f472b6">${kpis?.avg_perm || 0} <span class="unit">mD</span></div></div>
                <div class="kpi-card"><div class="label">Net Pay</div><div class="value" style="color:#4ade80">${kpis?.net_pay_ft || 0} <span class="unit">FT</span></div></div>
                <div class="kpi-card"><div class="label">Zonas Productivas</div><div class="value" style="color:#fbbf24">${kpis?.num_pay_zones || 0}</div></div>
                <div class="kpi-card"><div class="label">Total Muestras</div><div class="value">${kpis?.total_points || 0}</div></div>
            </div>
        </div>

        <!-- PAY ZONES -->
        <div class="section">
            <h2>Zonas de Interés (Pay Zones)</h2>
            <table>
                <thead><tr><th>#</th><th>Top (ft)</th><th>Base (ft)</th><th>H (ft)</th><th>Avg Φ</th><th>Avg Sw</th><th>Calidad</th></tr></thead>
                <tbody>${payTable}</tbody>
            </table>
        </div>

        <!-- ANALYSIS METHODS -->
        <div class="section">
            <h2>Métodos de Análisis Aplicados</h2>
            <div class="grid-4">
                <div class="info-row"><span class="k">Fuente Porosidad</span><span class="v">${analysis_meta?.phi_source || '-'}</span></div>
                <div class="info-row"><span class="k">Vsh disponible</span><span class="v">${analysis_meta?.vsh_available ? '✅ Sí' : '❌ No'}</span></div>
                <div class="info-row"><span class="k">Sw (Archie)</span><span class="v">${analysis_meta?.sw_available ? '✅ Sí' : '❌ No'}</span></div>
                <div class="info-row"><span class="k">Sw (Simandoux)</span><span class="v">${analysis_meta?.sw_simandoux_available ? '✅ Sí' : '❌ No'}</span></div>
            </div>
        </div>

        <!-- CURVAS -->
        <div class="section">
            <h2>Curvas Cargadas (${data.available_curves?.length || 0})</h2>
            <div>${curveTags}</div>
        </div>

        <!-- ====== CHART INTERPRETATION SECTIONS ====== -->
        <div class="section-divider">
            <h3>RESÚMENES DE MÓDULOS GRÁFICOS</h3>
            <p>Interpretaciones técnicas generadas desde datos reales del archivo .LAS</p>
        </div>

        ${chartSection(
        'SECCIÓN LITOLÓGICA — Composición del Reservorio',
        '🪨',
        `La sección litológica del pozo ${wellName} muestra que el ${cleanPct}% del intervalo (${depthRange}) corresponde a arenas limpias (Vsh<30%), mientras que el ${shalePct}% es arcilla (Vsh>60%). La porosidad efectiva promedio es ${(phiS.mean * 100).toFixed(1)}% (máx: ${(phiS.max * 100).toFixed(1)}%), lo que sugiere ${phiS.max > 0.15 ? 'buen potencial de almacenamiento' : 'reservorio compacto'}. El GR promedio es ${grS.mean.toFixed(0)} API — ${grS.mean < 60 ? 'predominio de arenas' : 'mezcla arena-arcilla'}.`,
        'Vsh calculado método Linear (GR Index): (GR - GR_min) / (GR_max - GR_min). Porosidad desde NPHI o RHOB. Cutoffs aplicados: Φ>8%, Vsh<50%, Sw<60% para Pay Zones.',
        `<div class="info-row"><span class="k">GR Promedio</span><span class="v">${grS.mean.toFixed(0)} API</span></div>
             <div class="info-row"><span class="k">Vsh Promedio</span><span class="v">${(vshS.mean * 100).toFixed(1)}%</span></div>
             <div class="info-row"><span class="k">Φ Promedio</span><span class="v">${(phiS.mean * 100).toFixed(1)}%</span></div>
             <div class="info-row"><span class="k">Arena Limpia (Vsh<30%)</span><span class="v" style="color:#4ade80">${cleanPct}%</span></div>
             <div class="info-row"><span class="k">Arcilla (Vsh>60%)</span><span class="v" style="color:#fbbf24">${shalePct}%</span></div>
             <div class="info-row"><span class="k">Muestras</span><span class="v">${numPoints}</span></div>`
    )}

        ${chartSection(
        'PETROFÍSICA — Saturación y Permeabilidad',
        '💧',
        `Saturación de agua promedio: ${(swS.mean * 100).toFixed(1)}% (Archie). Saturación HC: ${(shS.mean * 100).toFixed(1)}% promedio, máximo ${(shS.max * 100).toFixed(1)}%. Permeabilidad promedio: ${permS.mean.toFixed(1)} mD (rango: ${permS.min.toFixed(2)}–${permS.max.toFixed(1)} mD). ${swS.mean < 0.5 ? 'La fracción HC dominante sugiere potencial de producción significativo.' : 'La alta saturación de agua indica una zona potencialmente acuífera; evaluar zona por zona.'}`,
        'Sw calculada por ecuación de Archie: Sw = ((a × Rw) / (Φ^m × Rt))^(1/n), con a=1, m=2, n=2, Rw=0.04. Permeabilidad por ecuación empírica de Morris-Biggs: K = C × Φ^4.4 / (Sw_irr^2). SH = 1 - Sw.',
        `<div class="info-row"><span class="k">Sw Promedio (Archie)</span><span class="v" style="color:#3b82f6">${(swS.mean * 100).toFixed(1)}%</span></div>
             <div class="info-row"><span class="k">SH Promedio</span><span class="v" style="color:#4ade80">${(shS.mean * 100).toFixed(1)}%</span></div>
             <div class="info-row"><span class="k">Perm Promedio</span><span class="v" style="color:#f472b6">${permS.mean.toFixed(1)} mD</span></div>
             <div class="info-row"><span class="k">Perm Máx</span><span class="v">${permS.max.toFixed(1)} mD</span></div>`
    )}

        ${geo.available ? chartSection(
        'GEOFÍSICA — Sísmica Sintética y Well Tie',
        '🌊',
        `La sección sísmica 2D fue generada usando ${geo.has_dt ? 'curvas RHOB y DT reales' : 'RHOB con relación de Gardner'}. Impedancia Acústica promedio: ${impS.mean.toFixed(0)} kg/m²s (rango: ${impS.min.toFixed(0)}–${impS.max.toFixed(0)}). Coeficientes de reflexión: ${rcS.min.toFixed(4)} a ${rcS.max.toFixed(4)} — ${Math.abs(rcS.max) > 0.1 ? 'contrastes fuertes (cambios litológicos)' : 'contrastes moderados (transiciones graduales)'}. El sismograma sintético fue generado mediante convolución con wavelet Ricker (25 Hz).`,
        'Flujo: AI = RHOB × Vp → RC = ΔAI/ΣAI → Convolución con Ricker → Traza Sintética. Sección 2D por extensión lateral con ruido gaussiano.',
        `<div class="info-row"><span class="k">Fuente Sónica</span><span class="v">${geo.has_dt ? 'DT Real' : 'Gardner (Est.)'}</span></div>
             <div class="info-row"><span class="k">AI Promedio</span><span class="v">${impS.mean.toFixed(0)} kg/m²s</span></div>
             <div class="info-row"><span class="k">RC Rango</span><span class="v">${rcS.min.toFixed(4)} a ${rcS.max.toFixed(4)}</span></div>
             <div class="info-row"><span class="k">Trazas CMP</span><span class="v">${geo.seismic_nx || 0}</span></div>`
    ) : ''}

        ${radar.scores ? chartSection(
        'CALIDAD DE ROCA — Índice RQI (Radar)',
        '🎯',
        `El Índice de Calidad de Roca RQI global es ${(radarAvg * 100).toFixed(0)}%, clasificado como ${radarAvg > 0.7 ? 'EXCELENTE' : radarAvg > 0.5 ? 'BUENO' : radarAvg > 0.3 ? 'MODERADO' : 'BAJO'}. Un perfil radar equilibrado indica reservorio homogéneo; un perfil asimétrico indica heterogeneidad en las propiedades.`,
        'Normalización: Porosidad vs max teórico, Saturación HC (1-Sw), Limpieza (1-Vsh), Potencial Económico (K × H × (1-Sw)), Calidad de Datos (% curvas sin NaN). Score Global = promedio de 5 dimensiones.',
        radarItems
    ) : ''}

        ${Object.keys(hists).length > 0 ? chartSection(
        'DISTRIBUCIÓN ESTADÍSTICA — Histogramas',
        '📊',
        `Se analizaron las distribuciones de ${Object.keys(hists).length} propiedades petrofísicas. Cada histograma muestra 40 bins con la media aritmética resaltada. Las distribuciones permiten identificar modas (valores más frecuentes), asimetría (skewness) y detección de poblaciones mixtas.`,
        'Histogramas con 40 bins equiespaciados. La media aritmética (μ) se calcula como el centroide ponderado de los bins. Datos directamente del motor de cálculo Python.',
        histSummary
    ) : ''}

        ${topCorrs ? chartSection(
        'CORRELACIONES CRUZADAS — Análisis de Pearson',
        '🔗',
        `Se calculó la matriz de correlación de Pearson entre todas las curvas disponibles. Las correlaciones fuertes (|R|>0.7) indican relaciones directas entre propiedades — útiles para modelado y predicción. Las correlaciones débiles (|R|<0.3) sugieren independencia estadística.`,
        'Coeficiente de Pearson: R = Σ((xi-μx)(yi-μy)) / (n·σx·σy). |R|>0.7 = fuerte; 0.4-0.7 = moderada; <0.4 = débil.',
        topCorrs
    ) : ''}

        ${prod.barrels ? chartSection(
        'PRODUCCIÓN — Pronóstico Arps (10 Años)',
        '💰',
        `Basado en las propiedades petrofísicas, el OIP estimado es ${(prod.oip_estimate / 1e6).toFixed(2)} MM STB. Con tasa inicial de ${peakRate.toFixed(0)} bbl/mes y declinación exponencial 5%/año, la producción acumulada en 10 años sería ${(totalBarrels / 1e6).toFixed(2)} MM bbl, con ingresos totales de $${(prod.total_revenue_10y / 1e6).toFixed(1)} MM USD. ${prod.total_revenue_10y > 5e6 ? 'El pozo muestra potencial económico significativo.' : 'Evaluar con costos operativos.'}`,
        'Modelo Arps exponencial: q(t) = qi × exp(-D×t). OIP = 7758 × A × h × Φ × (1-Sw) / Boi. Precio: $65/bbl. Área: 40 acres. Boi = 1.2.',
        `<div class="info-row"><span class="k">OIP Estimado</span><span class="v" style="color:#00f2ff">${(prod.oip_estimate / 1e6).toFixed(2)} MM STB</span></div>
             <div class="info-row"><span class="k">Ingresos 10yr</span><span class="v" style="color:#4ade80">$${(prod.total_revenue_10y / 1e6).toFixed(1)} MM</span></div>
             <div class="info-row"><span class="k">Producción Acumulada</span><span class="v" style="color:#fb923c">${(totalBarrels / 1e6).toFixed(2)} MM bbl</span></div>
             <div class="info-row"><span class="k">Tasa Inicial</span><span class="v">${peakRate.toFixed(0)} bbl/mes</span></div>`
    ) : ''}

        <!-- DATA QC -->
        <div class="section">
            <h2>Auditoría de Calidad (Data QC)</h2>
            ${auditItems}
        </div>

        <div class="footer">
            <p>© ${new Date().getFullYear()} DataTerra — Subsurface Intelligence Systems</p>
            <p>Reporte generado automáticamente desde archivo: <strong>${data.filename || '-'}</strong></p>
            <p style="margin-top:8px; font-size:0.6rem;">Este documento contiene datos reales procesados del archivo .LAS. Incluye resúmenes de TODOS los módulos gráficos disponibles.</p>
        </div>
    </div>
</body>
</html>`;
};

// ============================================================
// GENERADOR CSV
// ============================================================
const generateCSV = (data) => {
    if (!data || !data.curves || !data.depths) return '';
    const { curves, depths } = data;
    const cols = Object.keys(curves);
    const header = ['DEPTH', ...cols.map(c => c.toUpperCase())].join(',');
    const rows = depths.map((d, i) => {
        const vals = cols.map(c => curves[c]?.[i] ?? '');
        return [d, ...vals].join(',');
    });
    return header + '\n' + rows.join('\n');
};

// ============================================================
// GENERADOR PDF (via print del HTML)
// ============================================================
const openReportInNewTab = (html) => {
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
};

const downloadFile = (content, filename, type) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
};

// ============================================================
// EXPORT MODAL COMPONENT
// ============================================================
export const ExportModal = ({ data, onClose }) => {
    const [copied, setCopied] = useState(false);
    if (!data) return null;

    const wellName = data.well_info?.well_name || 'WELL';
    const sanitized = wellName.replace(/[^a-zA-Z0-9]/g, '_');

    const handleHTML = () => {
        const html = generateHTMLReport(data);
        openReportInNewTab(html);
    };

    const handleDownloadHTML = () => {
        const html = generateHTMLReport(data);
        downloadFile(html, `Reporte_${sanitized}.html`, 'text/html');
    };

    const handlePDF = () => {
        const html = generateHTMLReport(data);
        const win = window.open('', '_blank');
        win.document.write(html);
        win.document.close();
        setTimeout(() => win.print(), 800);
    };

    const handleCSV = () => {
        const csv = generateCSV(data);
        downloadFile(csv, `Datos_${sanitized}.csv`, 'text/csv');
    };

    const handlePayCSV = () => {
        if (!data.pay_zones || data.pay_zones.length === 0) return;
        const header = 'Top,Base,Espesor_ft,Porosidad_Avg,Sw_Avg,Calidad\n';
        const rows = data.pay_zones.map(z => `${z.Top},${z.Base},${z.Espesor_ft},${z.Porosidad_Avg},${z.Sw_Avg},${z.Calidad}`).join('\n');
        downloadFile(header + rows, `PayZones_${sanitized}.csv`, 'text/csv');
    };

    const handleShareLink = () => {
        const html = generateHTMLReport(data);
        const blob = new Blob([html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        navigator.clipboard.writeText(url).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }).catch(() => {
            // Fallback: copiar KPIs como texto
            const text = `DataTerra Report: ${wellName}\nDepth: ${data.kpis?.max_depth} ft\nPorosity: ${data.kpis?.avg_phi}%\nSw: ${data.kpis?.avg_sw}%\nNet Pay: ${data.kpis?.net_pay_ft} ft\nPay Zones: ${data.kpis?.num_pay_zones}`;
            navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    };

    const btnStyle = (color) => ({
        display: 'flex', alignItems: 'center', gap: '12px', padding: '16px 20px', width: '100%',
        background: `${color}08`, border: `1px solid ${color}25`, borderRadius: '16px',
        color: 'white', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s',
    });

    return (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '15px' }} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={{ background: '#0a0a0a', borderRadius: '25px', border: '1px solid #1a1a1a', width: '95%', maxWidth: '550px', maxHeight: '90vh', overflow: 'auto', padding: '30px', position: 'relative' }}
                onClick={e => e.stopPropagation()}>
                <button onClick={onClose} style={{ position: 'absolute', top: '15px', right: '15px', background: 'rgba(255,255,255,0.05)', border: '1px solid #333', borderRadius: '12px', padding: '8px', cursor: 'pointer', color: 'white' }}><X size={18} /></button>

                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '5px' }}>EXPORTAR & COMPARTIR</h2>
                <p style={{ fontSize: '10px', opacity: 0.4, marginBottom: '20px' }}>Datos reales del pozo: {wellName}</p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {/* Ver como HTML */}
                    <button style={btnStyle('#00f2ff')} onClick={handleHTML}>
                        <Globe size={20} color="#00f2ff" />
                        <div>
                            <div style={{ fontSize: '12px', fontWeight: 800 }}>Ver Reporte en Navegador</div>
                            <div style={{ fontSize: '9px', opacity: 0.4 }}>Abre el reporte completo como página HTML (responsive, imprimible)</div>
                        </div>
                    </button>

                    {/* Descargar HTML */}
                    <button style={btnStyle('#22c55e')} onClick={handleDownloadHTML}>
                        <Download size={20} color="#22c55e" />
                        <div>
                            <div style={{ fontSize: '12px', fontWeight: 800 }}>Descargar Reporte HTML</div>
                            <div style={{ fontSize: '9px', opacity: 0.4 }}>Archivo .html standalone (KPIs, Pay Zones, QC, Info del Pozo)</div>
                        </div>
                    </button>

                    {/* PDF via Print */}
                    <button style={btnStyle('#a78bfa')} onClick={handlePDF}>
                        <FileText size={20} color="#a78bfa" />
                        <div>
                            <div style={{ fontSize: '12px', fontWeight: 800 }}>Exportar como PDF</div>
                            <div style={{ fontSize: '9px', opacity: 0.4 }}>Abre diálogo de impresión (Ctrl+P → Guardar como PDF)</div>
                        </div>
                    </button>

                    {/* CSV Datos completos */}
                    <button style={btnStyle('#fb923c')} onClick={handleCSV}>
                        <Download size={20} color="#fb923c" />
                        <div>
                            <div style={{ fontSize: '12px', fontWeight: 800 }}>Descargar Datos (.CSV)</div>
                            <div style={{ fontSize: '9px', opacity: 0.4 }}>Todas las curvas + profundidades en formato Excel/CSV</div>
                        </div>
                    </button>

                    {/* CSV Pay Zones */}
                    <button style={btnStyle('#fbbf24')} onClick={handlePayCSV}
                        disabled={!data.pay_zones || data.pay_zones.length === 0}>
                        <Download size={20} color="#fbbf24" />
                        <div>
                            <div style={{ fontSize: '12px', fontWeight: 800 }}>Descargar Pay Zones (.CSV)</div>
                            <div style={{ fontSize: '9px', opacity: 0.4 }}>Tabla de Zonas Productivas con Top, Base, H, Φ, Sw, Calidad</div>
                        </div>
                    </button>

                    {/* Compartir */}
                    <button style={btnStyle('#f472b6')} onClick={handleShareLink}>
                        {copied ? <Check size={20} color="#4ade80" /> : <Share2 size={20} color="#f472b6" />}
                        <div>
                            <div style={{ fontSize: '12px', fontWeight: 800 }}>{copied ? '✅ Copiado al Portapapeles' : 'Copiar Resumen (Texto)'}</div>
                            <div style={{ fontSize: '9px', opacity: 0.4 }}>Copia los KPIs principales al clipboard para enviar por mensaje</div>
                        </div>
                    </button>
                </div>

                <div style={{ marginTop: '15px', padding: '12px', background: 'rgba(0,242,255,0.03)', borderRadius: '12px', border: '1px solid rgba(0,242,255,0.08)' }}>
                    <p style={{ fontSize: '9px', opacity: 0.4, margin: 0, lineHeight: '1.6' }}>
                        ℹ️ Todos los reportes contienen <strong>datos reales</strong> del archivo .LAS procesado.
                        El reporte HTML se puede abrir en cualquier teléfono o computadora sin necesidad de instalar nada.
                        Para PDF: usa la función "Guardar como PDF" del diálogo de impresión de tu navegador.
                    </p>
                </div>
            </motion.div>
        </div>
    );
};
