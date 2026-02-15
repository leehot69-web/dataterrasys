import React, { useState } from 'react';
import './index.css';
import ExecutiveDashboard from './pages/ExecutiveDashboard';

function App() {
    const [view, setView] = useState('landing');

    console.log("App Rendering - Current View:", view);

    if (view === 'dashboard') {
        return (
            <div style={{ backgroundColor: '#050505', minHeight: '100vh' }}>
                <button
                    onClick={() => setView('landing')}
                    style={{ position: 'fixed', top: '20px', right: '20px', zIndex: 100, padding: '10px', background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid white', borderRadius: '5px', cursor: 'pointer' }}
                >
                    VOLVER AL INICIO
                </button>
                <ExecutiveDashboard />
            </div>
        );
    }

    return (
        <div style={{
            minHeight: '100vh',
            background: 'radial-gradient(circle at top right, #0a192f, #050505 80%)',
            color: 'white',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            padding: '20px',
            fontFamily: 'sans-serif'
        }}>
            <div style={{ maxWidth: '800px' }}>
                <h1 style={{ fontSize: '4rem', fontWeight: 900, letterSpacing: '-0.05em', marginBottom: '10px' }}>
                    DATA<span style={{ color: '#00f2ff' }}>TERRA</span>
                </h1>
                <p style={{ fontSize: '1.2rem', color: '#94a3b8', marginBottom: '40px' }}>
                    Analítica de subsuelo impulsada por IA. Petrofísica y Visualización en tiempo real.
                </p>

                <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <button
                        onClick={() => window.location.href = 'http://localhost:8501'}
                        style={{
                            padding: '15px 40px',
                            fontSize: '18px',
                            fontWeight: '800',
                            background: '#00f2ff',
                            color: 'black',
                            border: 'none',
                            borderRadius: '50px',
                            cursor: 'pointer',
                            boxShadow: '0 0 20px rgba(0, 242, 255, 0.5)'
                        }}
                    >
                        ENTRAR A LA PLATAFORMA (PYTHON)
                    </button>

                    <button
                        onClick={() => setView('dashboard')}
                        style={{
                            padding: '15px 40px',
                            fontSize: '18px',
                            fontWeight: '800',
                            background: 'transparent',
                            color: 'white',
                            border: '2px solid white',
                            borderRadius: '50px',
                            cursor: 'pointer'
                        }}
                    >
                        VER DEMO TÉCNICA (TESLA UI)
                    </button>
                </div>
            </div>

            <div style={{ marginTop: '100px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', width: '100%', maxWidth: '1000px' }}>
                <div style={{ padding: '20px', background: 'rgba(255,255,255,0.05)', borderRadius: '20px' }}>
                    <h3 style={{ color: '#00f2ff' }}>IA Agentica</h3>
                    <p style={{ fontSize: '14px', opacity: 0.7 }}>Interpretación automática de registros y sísmica.</p>
                </div>
                <div style={{ padding: '20px', background: 'rgba(255,255,255,0.05)', borderRadius: '20px' }}>
                    <h3 style={{ color: '#00f2ff' }}>Tiempo Real</h3>
                    <p style={{ fontSize: '14px', opacity: 0.7 }}>Visualización LWD y MWD al instante.</p>
                </div>
                <div style={{ padding: '20px', background: 'rgba(255,255,255,0.05)', borderRadius: '20px' }}>
                    <h3 style={{ color: '#00f2ff' }}>Excelencia</h3>
                    <p style={{ fontSize: '14px', opacity: 0.7 }}>Diseño inspirado en los estándares de Tesla.</p>
                </div>
            </div>
        </div>
    );
}

export default App;
