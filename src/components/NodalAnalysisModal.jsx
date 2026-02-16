import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Play, TrendingUp, AlertTriangle, Settings, Activity } from 'lucide-react';
import {
    Chart as ChartJS,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    Legend,
} from 'chart.js';
import { Scatter } from 'react-chartjs-2';

ChartJS.register(LinearScale, PointElement, LineElement, Tooltip, Legend);


const NodalAnalysisModal = ({ isOpen, onClose, wellData, kpis }) => {
    const [params, setParams] = useState({
        k: 50, // Permeabilidad (mD)
        h: 20, // Espesor Neto (ft)
        pr: 3500, // Presión Yacimiento (psi)
        p_wh: 200, // Presión Cabezal (psi)
        tubing_id: 2.875, // ID Tubing (in)
        md: 8000, // MD (ft)
        tvd: 8000, // TVD (ft)
        wc: 0, // Corte de Agua (%)
        gor: 500, // Relación Gas-Petróleo
        api: 35, // Gravedad API
        skin: 0, // Daño
        temp_wh: 100, // Temp Cabezal (F)
        temp_bh: 200 // Temp Fondo (F)
    });

    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Cargar valores por defecto del KPI si existen
    useEffect(() => {
        if (isOpen && kpis) {
            setParams(prev => ({
                ...prev,
                k: kpis.avg_perm || 50,
                h: kpis.net_pay_ft || 20,
                md: kpis.max_depth || 8000, // Asumir MD total del log
                tvd: kpis.max_depth || 8000, // Asumir Vertical por defecto
                // Estimar Pr como Gradiente Normal (0.433 psi/ft) a Max Depth
                pr: Math.round((kpis.max_depth || 8000) * 0.433),
                temp_bh: Math.round(70 + (kpis.max_depth || 8000) * 0.012) // Gradiente geotérmico
            }));
        }
    }, [isOpen, kpis]);

    const runSimulation = async () => {
        setLoading(true);
        setError(null);
        try {
            const payload = {
                ...params
            };

            console.log("Simulando producción...", payload);

            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/analyze_nodal`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error("Error en simulación");

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const chartData = result ? {
        datasets: [
            {
                label: 'IPR (Oferta Yacimiento)',
                data: result.ipr.rates.map((r, i) => ({ x: r, y: result.ipr.pressures[i] })),
                borderColor: '#4ade80', // Verde neón
                backgroundColor: 'rgba(74, 222, 128, 0.2)',
                showLine: true,
                pointRadius: 0,
                borderWidth: 2,
                tension: 0.4
            },
            {
                label: 'VLP (Demanda Pozo)',
                data: result.vlp.rates.map((r, i) => ({ x: r, y: result.vlp.pressures[i] })),
                borderColor: '#fbbf24', // Dorado
                backgroundColor: 'rgba(251, 191, 36, 0.2)',
                showLine: true,
                pointRadius: 0,
                borderWidth: 2,
                tension: 0.4
            },
            result.operating_point ? {
                label: 'Punto de Operación',
                data: [{ x: result.operating_point.q_op, y: result.operating_point.pwf_op }],
                backgroundColor: '#00f2ff', // Cyan
                borderColor: '#fff',
                pointRadius: 6,
                pointHoverRadius: 8
            } : null
        ].filter(Boolean)
    } : null;

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { labels: { color: '#ccc', font: { size: 10 } } },
            tooltip: {
                mode: 'nearest', intersect: false,
                callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.x.toFixed(0)} bpd @ ${ctx.raw.y.toFixed(0)} psi` }
            }
        },
        scales: {
            x: {
                title: { display: true, text: 'Tasa de Liquido (stb/d)', color: '#666' },
                grid: { color: 'rgba(255,255,255,0.05)' },
                ticks: { color: '#888' }
            },
            y: {
                title: { display: true, text: 'Presión de Fondo (psi)', color: '#666' },
                grid: { color: 'rgba(255,255,255,0.05)' },
                ticks: { color: '#888' },
                min: 0
            }
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div style={{
                position: 'fixed', inset: 0, zIndex: 60,
                background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
            }} onClick={onClose}>
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    style={{
                        width: '900px', height: '85vh',
                        background: '#0a0a0a', border: '1px solid #333', borderRadius: '24px',
                        display: 'flex', flexDirection: 'column', overflow: 'hidden',
                        boxShadow: '0 20px 50px rgba(0,0,0,0.5)'
                    }}
                    onClick={e => e.stopPropagation()}
                >
                    {/* Header */}
                    <div style={{ padding: '20px 30px', borderBottom: '1px solid #222', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div style={{ padding: '8px', background: 'rgba(251,191,36,0.1)', borderRadius: '10px' }}>
                                <Activity size={20} color="#fbbf24" />
                            </div>
                            <div>
                                <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 800 }}>Simulador de Producción</h2>
                                <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>Análisis Nodal Dinámico (Vogel IPR + VLP Multifásico)</p>
                            </div>
                        </div>
                        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#666' }}><X /></button>
                    </div>

                    <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                        {/* Panel Izquierdo: Inputs */}
                        <div style={{ width: '300px', borderRight: '1px solid #222', padding: '20px', overflowY: 'auto', background: '#050505' }}>
                            <h3 style={{ fontSize: '11px', fontWeight: 900, color: '#fbbf24', letterSpacing: '1px', marginBottom: '15px' }}>CONDICIONES OPERATIVAS</h3>

                            <div style={{ display: 'grid', gap: '15px' }}>
                                {[
                                    { k: 'k', l: 'Permeabilidad (mD)', color: '#f472b6' },
                                    { k: 'h', l: 'Espesor Neto (ft)', color: '#4ade80' },
                                    { k: 'pr', l: 'Presión Yacimiento (psi)' },
                                    { k: 'p_wh', l: 'Presión Cabezal (psi)' },
                                    { k: 'tubing_id', l: 'ID Tubing (in)', step: 0.001 },
                                    { k: 'md', l: 'Prof. Medida (MD)', color: '#a78bfa' },
                                    { k: 'tvd', l: 'Prof. Vertical (TVD)', color: '#3b82f6' },
                                    { k: 'wc', l: 'Corte de Agua (%)' },
                                    { k: 'gor', l: 'GOR (scf/stb)' },
                                    { k: 'api', l: 'Gravedad API' },
                                    { k: 'skin', l: 'Daño (Skin)' },
                                    { k: 'temp_wh', l: 'Temp. Cabezal (°F)' },
                                ].map(f => (
                                    <div key={f.k}>
                                        <label style={{ display: 'block', fontSize: '10px', color: f.color || '#888', marginBottom: '4px', fontWeight: f.color ? 800 : 400 }}>{f.l}</label>
                                        <input
                                            type="number"
                                            step={f.step || 1}
                                            value={params[f.k]}
                                            onChange={e => setParams({ ...params, [f.k]: parseFloat(e.target.value) })}
                                            style={{
                                                width: '100%', padding: '8px 10px', background: '#111', border: '1px solid #333',
                                                borderRadius: '6px', color: '#fff', fontSize: '12px', fontWeight: 600
                                            }}
                                        />
                                    </div>
                                ))}
                            </div>

                            <button
                                onClick={runSimulation}
                                disabled={loading}
                                style={{
                                    width: '100%', marginTop: '30px', padding: '12px',
                                    background: loading ? '#333' : '#fbbf24', color: loading ? '#666' : '#000',
                                    border: 'none', borderRadius: '8px', fontWeight: 800, fontSize: '12px',
                                    cursor: loading ? 'not-allowed' : 'pointer', transition: 'all 0.2s',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
                                }}
                            >
                                {loading ? 'Calculando...' : <><Play size={14} /> EJECUTAR SIMULACIÓN</>}
                            </button>
                        </div>

                        {/* Panel Derecho: Resultados */}
                        <div style={{ flex: 1, padding: '30px', background: '#000', display: 'flex', flexDirection: 'column' }}>
                            {result ? (
                                <>
                                    <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
                                        <div style={{ padding: '15px 20px', background: 'rgba(74,222,128,0.05)', borderRadius: '12px', border: '1px solid rgba(74,222,128,0.2)' }}>
                                            <div style={{ fontSize: '10px', fontWeight: 700, color: '#4ade80' }}>TASA LÍQUIDA (Qop)</div>
                                            <div style={{ fontSize: '24px', fontWeight: 900, color: '#fff' }}>
                                                {result.operating_point?.q_op || 0} <span style={{ fontSize: '12px', color: '#666' }}>bpd</span>
                                            </div>
                                        </div>
                                        <div style={{ padding: '15px 20px', background: 'rgba(251,191,36,0.05)', borderRadius: '12px', border: '1px solid rgba(251,191,36,0.2)' }}>
                                            <div style={{ fontSize: '10px', fontWeight: 700, color: '#fbbf24' }}>PRESIÓN DE FONDO (Pwf)</div>
                                            <div style={{ fontSize: '24px', fontWeight: 900, color: '#fff' }}>
                                                {result.operating_point?.pwf_op || 0} <span style={{ fontSize: '12px', color: '#666' }}>psi</span>
                                            </div>
                                        </div>
                                        <div style={{ padding: '15px 20px', background: 'rgba(0,242,255,0.05)', borderRadius: '12px', border: '1px solid rgba(0,242,255,0.2)' }}>
                                            <div style={{ fontSize: '10px', fontWeight: 700, color: '#00f2ff' }}>ESTADO</div>
                                            <div style={{ fontSize: '18px', fontWeight: 900, color: '#fff', marginTop: '4px' }}>
                                                {result.status?.toUpperCase()}
                                            </div>
                                        </div>
                                    </div>

                                    <div style={{ flex: 1, position: 'relative', minHeight: '300px' }}>
                                        <Scatter data={chartData} options={chartOptions} />
                                    </div>

                                    <button
                                        onClick={() => window.print()}
                                        style={{
                                            marginTop: '20px', padding: '10px', background: '#333',
                                            color: '#fff', border: 'none', borderRadius: '8px',
                                            cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
                                        }}
                                    >
                                        <TrendingUp size={16} /> IMPRIMIR REPORTE NODAL
                                    </button>
                                </>
                            ) : (
                                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', opacity: 0.3 }}>
                                    <Settings size={48} />
                                    <p style={{ marginTop: '20px', fontSize: '14px' }}>Configura los parámetros y ejecuta la simulación</p>
                                </div>
                            )}
                        </div>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};

export default NodalAnalysisModal;
