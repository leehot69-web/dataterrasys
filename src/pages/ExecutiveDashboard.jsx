import React from 'react';
import { Zap, Activity, ShieldCheck, TrendingUp, Droplets, Navigation, Bell, Search, Map as MapIcon, Settings } from 'lucide-react';

const ExecutiveDashboard = () => {
    return (
        <div style={{ backgroundColor: '#1a1a1a', color: 'white', minHeight: '100vh', padding: '20px', fontFamily: 'sans-serif' }}>
            <div style={{ background: 'red', color: 'white', padding: '10px', marginBottom: '20px', fontWeight: 'bold' }}>
                DASHBOARD MODO EMERGENCIA - SI VES ESTO, EL CAMBIO DE PANTALLA FUNCIONA
            </div>

            <header style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '30px' }}>
                <div>
                    <h1 style={{ fontSize: '24px', margin: 0 }}>OPERACIONES DTERRA</h1>
                    <p style={{ color: '#00f2ff', fontSize: '12px' }}>NODO ACTIVO: VENEZUELA-ESTE</p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <div style={{ padding: '10px', background: '#333', borderRadius: '10px' }}><Bell size={20} /></div>
                    <div style={{ padding: '10px', background: '#333', borderRadius: '10px' }}><Settings size={20} /></div>
                </div>
            </header>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                {[
                    { t: 'Producción Diaria', v: '48,250', u: 'BBL', c: '#00f2ff', i: Droplets },
                    { t: 'Energía', v: '12.4', u: 'MWH', c: '#ff9900', i: Zap },
                    { t: 'Integridad', v: '99.9', u: '%', c: '#00ff00', i: ShieldCheck },
                    { t: 'Ingresos MTD', v: '2.8M', u: 'USD', c: '#cc00ff', i: Activity }
                ].map((k, i) => (
                    <div key={i} style={{ background: '#222', padding: '20px', borderRadius: '20px', border: '1px solid #333' }}>
                        <div style={{ color: k.c, marginBottom: '10px' }}><k.i size={24} /></div>
                        <p style={{ fontSize: '10px', opacity: 0.5 }}>{k.t}</p>
                        <h3 style={{ fontSize: '20px', margin: '5px 0' }}>{k.v} <span style={{ fontSize: '12px', opacity: 0.5 }}>{k.u}</span></h3>
                    </div>
                ))}
            </div>

            <div style={{ marginTop: '30px', background: '#222', padding: '30px', borderRadius: '30px', textAlign: 'center', border: '1px solid #333' }}>
                <MapIcon size={40} style={{ color: '#00f2ff', opacity: 0.5 }} />
                <p style={{ marginTop: '10px', fontWeight: 'bold' }}>VISUALIZACIÓN DE MAPA ACTIVA</p>
                <p style={{ fontSize: '10px', opacity: 0.5 }}>ORINOCO_BELT_SEC_7</p>
            </div>
        </div>
    );
};

export default ExecutiveDashboard;
