
import React, { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import * as THREE from 'three';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

// --- Utilitarios Geométricos ---

import { calculateDLS } from '../utils/physics_models'; // Nueva Geofísica

const WellPath = ({ depthData }) => {

    const points = useMemo(() => {
        if (!depthData || depthData.length === 0) return [];

        const pts = [];
        let z = 0;

        for (let i = 0; i < depthData.length; i += 10) { // Subsampling cada 10 pts para rendimiento
            const md = depthData[i];
            const dMd = i > 0 ? (md - depthData[i - 10]) : md;
            const prevMd = i > 0 ? depthData[i - 10] : 0;

            z -= dMd;

            const dls = calculateDLS(prevMd, 0, 0, md, 0, 0);
            const color = new THREE.Color('#22c55e');

            pts.push({ pos: new THREE.Vector3(0, z, 0), color, depth: md, val: dls });
        }
        return pts;
    }, [depthData]);

    // Crear geometría del tubo
    const curve = useMemo(() => {
        if (points.length < 2) return null;
        return new THREE.CatmullRomCurve3(points.map(p => p.pos));
    }, [points]);

    if (!curve) return null;

    return (
        <group>
            {/* El Tubo del Pozo */}
            <mesh>
                <tubeGeometry args={[curve, points.length, 120, 16, false]} />
                {/* Material AUTO-ILUMINADO para máxima visibilidad */}
                <meshBasicMaterial vertexColors={true} />
            </mesh>

            {/* Líneas de Profundidad cada 1000m */}
            {points.filter((_, i) => i % 50 === 0).map((p, i) => (
                <Text key={i} position={[p.pos.x + 30, p.pos.y, p.pos.z]} fontSize={40} color="white">
                    {Math.round(p.depth)}'
                </Text>
            ))}
        </group>
    );
};

// --- Componente de Rejilla Geológica (Grid) ---
const ReservoirGrid = () => {
    return (
        <gridHelper args={[10000, 50, 0x444444, 0x222222]} position={[0, -8000, 0]} />
    );
};

const WellTrajectory3D = ({ data, onClose }) => {
    // Helper para buscar curvas con aliases
    const findCurve = (aliases) => {
        if (!data?.well_data) return [];
        for (const alias of aliases) {
            // Check exact match
            if (data.well_data[alias]) return data.well_data[alias];
            // Check case-insensitive
            const key = Object.keys(data.well_data).find(k => k.toUpperCase() === alias);
            if (key) return data.well_data[key];
        }
        return [];
    };

    const depth = findCurve(['DEPTH', 'DEPT', 'M_DEPTH', 'MD']);
    const hasDepth = depth && depth.length > 1;

    console.log("3D Viewer data:", { depthLen: depth?.length, available: Object.keys(data?.well_data || {}) });

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                style={{
                    position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
                    background: '#000', zIndex: 3000, display: 'flex', flexDirection: 'column'
                }}
            >
                {/* Header Flotante */}
                <div style={{
                    position: 'absolute', top: 20, left: 20, zIndex: 3010,
                    background: 'rgba(0,0,0,0.8)', padding: '15px 25px', borderRadius: '12px',
                    border: '1px solid rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)',
                    display: 'flex', gap: '20px', alignItems: 'center'
                }}>
                    <div>
                        <h2 style={{ margin: 0, color: '#fff', fontSize: '1.2rem', fontFamily: 'Outfit' }}>
                            Visor de Trayectoria 3D
                        </h2>
                        <div style={{ fontSize: '0.8rem', color: '#888' }}>
                            Trayectoria basada únicamente en datos reales del LAS
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '15px', fontSize: '0.75rem', color: '#ccc' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <div style={{ width: 12, height: 12, background: '#10b981', borderRadius: '50%' }}></div>
                            Trayectoria vertical medida
                        </div>
                    </div>
                </div>

                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute', top: 20, right: 20, zIndex: 3010,
                        background: 'rgba(255,255,255,0.1)', border: 'none', color: '#fff',
                        width: '40px', height: '40px', borderRadius: '50%', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}
                >
                    <X size={20} />
                </button>

                {/* Canvas 3D */}
                <div style={{ flex: 1, cursor: 'move' }}>
                    <Canvas camera={{ position: [4000, -3000, 4000], fov: 45, far: 50000 }}>
                        {/* Fondo Azul Ingenieria (Petrel Style) */}
                        <color attach="background" args={['#1e293b']} />
                        <fog attach="fog" args={['#1e293b', 2000, 40000]} />

                        <ambientLight intensity={0.8} />
                        <pointLight position={[2000, 5000, 2000]} intensity={1.5} />

                        {/* Superficie (Ground Level) */}
                        <gridHelper args={[20000, 40, 0x64748b, 0x334155]} position={[0, 0, 0]} />

                        <OrbitControls
                            target={[0, -4000, 0]}
                            autoRotate={true}
                            autoRotateSpeed={1.0}
                            enableDamping
                            dampingFactor={0.05}
                            rotateSpeed={0.5}
                            minDistance={100}
                            maxDistance={30000}
                        />

                        {/* Elementos Geológicos */}
                        <ReservoirGrid />
                        {hasDepth ? <WellPath depthData={depth} /> : null}
                        <axesHelper args={[1000]} />
                    </Canvas>
                </div>

                {!hasDepth && (
                    <div style={{
                        position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: 'rgba(0,0,0,0.6)', color: '#f8fafc', fontSize: '0.95rem', zIndex: 3005
                    }}>
                        No hay curva de profundidad real para dibujar trayectoria 3D.
                    </div>
                )}

                {/* Footer Controls */}
                <div style={{
                    position: 'absolute', bottom: 30, left: '50%', transform: 'translateX(-50%)',
                    zIndex: 3010, background: 'rgba(0,0,0,0.6)', padding: '10px 20px', borderRadius: '30px',
                    color: '#666', fontSize: '0.8rem', pointerEvents: 'none'
                }}>
                    Hold Click to Rotate • Scroll to Zoom • Right Click to Pan
                </div>
            </motion.div>
        </AnimatePresence>
    );
};

export default WellTrajectory3D;
