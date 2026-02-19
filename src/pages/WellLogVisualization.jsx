import React from 'react';

const WellLogVisualization = ({ wellData }) => {
    const hasData = wellData && Array.isArray(wellData.depth) && wellData.depth.length > 0;

    if (!hasData) {
        return (
            <div className="h-screen bg-[#050505] text-white flex items-center justify-center font-mono">
                <div className="text-center">
                    <h2 className="text-xl font-black mb-3">WELL LOG VISUALIZATION</h2>
                    <p className="text-sm text-white/60">Este módulo requiere datos reales del backend.</p>
                    <p className="text-xs text-white/40 mt-2">No se renderizan curvas simuladas ni valores quemados.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen bg-[#050505] text-white flex items-center justify-center font-mono">
            <div className="text-center">
                <h2 className="text-xl font-black mb-3">WELL LOG VISUALIZATION</h2>
                <p className="text-sm text-cyan-400">Datos listos para visualización: {wellData.depth.length} muestras</p>
            </div>
        </div>
    );
};

export default WellLogVisualization;
