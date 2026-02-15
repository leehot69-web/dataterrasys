import React from 'react';
import { Zap, Activity, ShieldCheck, TrendingUp, Droplets, Navigation, Bell, Search, Map as MapIcon, Settings } from 'lucide-react';

const ExecutiveDashboard = () => {
    return (
        <div style={{ backgroundColor: '#050505', color: 'white', minHeight: '100vh', padding: '40px', fontFamily: 'sans-serif' }}>
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px', borderBottom: '1px solid #222', paddingBottom: '20px' }}>
                <div>
                    <h1 style={{ fontSize: '32px', fontWeight: 900, letterSpacing: '-0.05em', margin: 0 }}>OPERACIONES <span style={{ color: '#00f2ff' }}>DTERRA</span></h1>
                    <p style={{ color: '#00f2ff', fontSize: '12px', fontWeight: 'bold', letterSpacing: '2px' }}>STATUS: SISTEMA OPERATIVO ACTIVO</p>
                </div>
                <div style={{ display: 'flex', gap: '15px' }}>
                    <div style={{ padding: '12px', background: '#111', borderRadius: '15px', border: '1px solid #333' }}><Bell size={20} /></div>
                    <div style={{ padding: '12px', background: '#111', borderRadius: '15px', border: '1px solid #333' }}><Settings size={20} /></div>
                </div>
            </header>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '40px' }}>
                {[
                    { t: 'Producción Diaria', v: '48,250', u: 'BBL', c: '#00f2ff', i: Droplets },
                    { t: 'Energía de Red', v: '12.4', u: 'MWH', c: '#ff9900', i: Zap },
                    { t: 'Integridad de Red', v: '99.9', u: '%', c: '#00ff00', i: ShieldCheck },
                    { t: 'Ingresos Mensuales', v: '2.8M', u: 'USD', c: '#cc00ff', i: Activity }
                ].map((k, i) => (
                    <div key={i} style={{ background: '#0f1111', padding: '25px', borderRadius: '25px', border: '1px solid #222' }}>
                        <div style={{ color: k.c, marginBottom: '15px' }}><k.i size={28} /></div>
                        <p style={{ fontSize: '11px', opacity: 0.5, textTransform: 'uppercase', fontWeight: '800' }}>{k.t}</p>
                        <h3 style={{ fontSize: '28px', fontWeight: '900', margin: '10px 0' }}>{k.v} <span style={{ fontSize: '14px', opacity: 0.5, fontWeight: '400' }}>{k.u}</span></h3>
                    </div>
                ))}
            </div>

            <div style={{
                height: '400px',
                background: '#0a0a0a',
                borderRadius: '40px',
                border: '1px solid #222',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                overflow: 'hidden'
            }}>
                {/* Background Grid Pattern */}
                <div style={{ position: 'absolute', inset: 0, opacity: 0.1, backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

                <MapIcon size={64} style={{ color: '#00f2ff', opacity: 0.8, marginBottom: '20px' }} />
                <h2 style={{ fontSize: '20px', fontWeight: '900', margin: 0 }}>MAPA GEOSPACIAL ACTIVO</h2>
                <p style={{ fontSize: '12px', opacity: 0.6, color: '#00f2ff' }}>ORINOCO BELT // SECTOR ANALÍTICO 7</p>

                <div style={{
                    marginTop: '30px',
                    padding: '10px 20px',
                    background: 'rgba(0, 242, 255, 0.1)',
                    borderRadius: '50px',
                    border: '1px solid rgba(0, 242, 255, 0.3)',
                    color: '#00f2ff',
                    fontSize: '12px',
                    fontWeight: 'bold'
                }}>
                    ESCANEANDO FORMACIÓN...
                </div>
            </div>
        </div>
    );
};

export default ExecutiveDashboard;
