# geo_mind_petrophysics.py
# VERSIÓN COMPLETA MEJORADA - Con análisis funcionando

import sys
import os
import tempfile
import math
import lasio
import folium
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import logging
from typing import Dict, List, Optional, Tuple, Any

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QComboBox, QTabWidget, QGroupBox, QFormLayout,
    QLineEdit, QTextEdit, QDoubleSpinBox, QMessageBox, QSplitter, QListWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QSpinBox,
    QCheckBox, QFrame, QSizePolicy, QGridLayout, QScrollArea, QDialog,
    QDialogButtonBox, QProgressDialog
)
from PyQt5.QtCore import QUrl, Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QIcon

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib as mpl
from matplotlib.patches import Rectangle
import matplotlib.colors as mcolors

# =============================================================================
# CONFIGURACIÓN AVANZADA
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('geomind_petrophysics.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('GeoMind')

# Paleta de colores profesional extendida
COLORS = {
    'primary': '#3498db',
    'secondary': '#2c3e50', 
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'info': '#1abc9c',
    'light': '#ecf0f1',
    'dark': '#2c3e50',
    'accent1': '#9b59b6',
    'accent2': '#e67e22',
    'accent3': '#34495e'
}

# Sistema de colores para curvas petrofísicas
CURVE_COLORS = {
    'GR': '#2ecc71',      # Verde - Litología
    'RHOB': '#e74c3c',    # Rojo - Densidad
    'NPHI': '#3498db',    # Azul - Neutrón
    'ILD': '#9b59b6',     # Púrpura - Resistividad Profunda
    'ILM': '#34495e',     # Gris oscuro - Resistividad Media
    'RT': '#e67e22',      # Naranja - Resistividad Verdadera
    'DT': '#f39c12',      # Amarillo - Sónico
    'CALI': '#95a5a6',    # Gris - Calibre
    'SP': '#1abc9c',      # Turquesa - Potencial Espontáneo
    'DRHO': '#d35400',    # Naranja oscuro - Corrección Densidad
    'PEF': '#8e44ad'      # Violeta - Factor Fotoelectrico
}

# Parámetros petrofísicos por defecto con validación
DEFAULT_PETRO_PARAMS = {
    'gr': {'clean': 40.0, 'shale': 120.0},
    'density': {'matrix': 2.65, 'fluid': 1.0},
    'archie': {'a': 1.0, 'm': 2.0, 'n': 2.0, 'rw': 0.035},
    'cutoffs': {
        'porosity_min': 0.12,
        'vshale_max': 0.45, 
        'sw_max': 0.6,
        'min_thickness': 1.0
    }
}

# =============================================================================
# SISTEMA DE ANÁLISIS MEJORADO
# =============================================================================

class AdvancedPetroCalculationThread(QThread):
    """Hilo avanzado para cálculos petrofísicos con logging completo"""
    
    # Señales mejoradas
    progress_updated = pyqtSignal(int, str)  # porcentaje, mensaje
    calculation_finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    warning_emitted = pyqtSignal(str)
    
    def __init__(self, df: pd.DataFrame, params: dict, well_name: str):
        super().__init__()
        self.df = df.copy()
        self.params = params
        self.well_name = well_name
        self.results = {}
        
    def run(self):
        """Ejecutar cálculo completo con manejo robusto de errores"""
        try:
            logger.info(f"Iniciando análisis petrofísico para {self.well_name}")
            
            # FASE 1: Preparación de datos
            self.progress_updated.emit(5, "Preparando datos...")
            self.prepare_data()
            
            # FASE 2: Cálculos básicos
            self.progress_updated.emit(20, "Calculando propiedades básicas...")
            self.calculate_basic_properties()
            
            # FASE 3: Cálculos avanzados
            self.progress_updated.emit(50, "Calculando propiedades avanzadas...")
            self.calculate_advanced_properties()
            
            # FASE 4: Análisis de intervalos
            self.progress_updated.emit(70, "Analizando intervalos...")
            self.analyze_intervals()
            
            # FASE 5: Estadísticas y resumen
            self.progress_updated.emit(90, "Generando reporte...")
            self.generate_summary()
            
            self.progress_updated.emit(100, "Análisis completado")
            self.calculation_finished.emit(self.results)
            logger.info(f"Análisis completado exitosamente para {self.well_name}")
            
        except Exception as e:
            error_msg = f"Error crítico en análisis: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
    
    def prepare_data(self):
        """Preparar y validar datos de entrada"""
        try:
            # Validar columnas requeridas
            required_curves = ['GR', 'RHOB']
            missing_curves = [curve for curve in required_curves if curve not in self.df.columns]
            
            if missing_curves:
                raise ValueError(f"Curvas requeridas faltantes: {missing_curves}")
            
            # Limpiar datos
            self.df = self.df.replace(-999.25, np.nan)
            self.df = self.df.dropna(subset=required_curves)
            
            if self.df.empty:
                raise ValueError("No hay datos válidos después de la limpieza")
                
            logger.info(f"Datos preparados: {len(self.df)} registros válidos")
            
        except Exception as e:
            logger.error(f"Error preparando datos: {e}")
            raise
    
    def calculate_basic_properties(self):
        """Calcular propiedades petrofísicas básicas"""
        try:
            # 1. Volumen de Arcilla (VShale)
            self.progress_updated.emit(25, "Calculando VShale...")
            if 'GR' in self.df.columns:
                gr_clean = self.params['gr']['clean']
                gr_shale = self.params['gr']['shale']
                
                self.df['VSH'] = (self.df['GR'] - gr_clean) / (gr_shale - gr_clean)
                self.df['VSH'] = self.df['VSH'].clip(0.0, 1.0)
                self.results['vshale'] = self.df['VSH'].tolist()
                logger.info(f"VShale calculado: {len(self.df['VSH'])} puntos")
            
            # 2. Porosidad (PHI)
            self.progress_updated.emit(35, "Calculando porosidad...")
            if 'RHOB' in self.df.columns:
                rho_matrix = self.params['density']['matrix']
                rho_fluid = self.params['density']['fluid']
                
                self.df['PHI'] = (rho_matrix - self.df['RHOB']) / (rho_matrix - rho_fluid)
                self.df['PHI'] = self.df['PHI'].clip(0.0, 0.6)
                self.results['porosity'] = self.df['PHI'].tolist()
                logger.info(f"Porosidad calculada: {len(self.df['PHI'])} puntos")
            
            # 3. Permeabilidad (K)
            self.progress_updated.emit(45, "Calculando permeabilidad...")
            if 'PHI' in self.df.columns:
                self.df['K'] = 100.0 * (self.df['PHI'] ** 3) / ((1 - self.df['PHI']) ** 2)
                self.df['K'] = self.df['K'].clip(0.001, 10000)
                self.results['permeability'] = self.df['K'].tolist()
                logger.info(f"Permeabilidad calculada: {len(self.df['K'])} puntos")
                
        except Exception as e:
            logger.error(f"Error en cálculos básicos: {e}")
            raise
    
    def calculate_advanced_properties(self):
        """Calcular propiedades petrofísicas avanzadas"""
        try:
            # 4. Saturación de Agua (SW)
            self.progress_updated.emit(55, "Calculando saturación de agua...")
            if 'RT' in self.df.columns and 'PHI' in self.df.columns:
                a = self.params['archie']['a']
                m = self.params['archie']['m']
                n = self.params['archie']['n']
                rw = self.params['archie']['rw']
                
                # Fórmula de Archie
                self.df['SW'] = ((a * rw) / ((self.df['PHI'] ** m) * self.df['RT'])) ** (1.0 / n)
                self.df['SW'] = self.df['SW'].clip(0.05, 1.0)
                self.results['water_saturation'] = self.df['SW'].tolist()
                logger.info(f"Saturación calculada: {len(self.df['SW'])} puntos")
            
            # 5. Hidrocarburos móviles
            self.progress_updated.emit(65, "Calculando hidrocarburos...")
            if 'PHI' in self.df.columns and 'SW' in self.df.columns:
                self.df['HYDROCARBONS'] = self.df['PHI'] * (1 - self.df['SW'])
                self.results['hydrocarbons'] = self.df['HYDROCARBONS'].tolist()
                logger.info(f"Hidrocarburos calculados: {len(self.df['HYDROCARBONS'])} puntos")
                
        except Exception as e:
            logger.warning(f"Algunos cálculos avanzados no pudieron completarse: {e}")
            self.warning_emitted.emit(f"Cálculos avanzados: {str(e)}")
    
    def analyze_intervals(self):
        """Analizar intervalos prospectivos automáticamente"""
        try:
            self.progress_updated.emit(75, "Detectando intervalos...")
            
            if all(col in self.df.columns for col in ['PHI', 'VSH', 'SW']):
                cutoffs = self.params['cutoffs']
                
                # Crear máscara de prospectividad
                prospect_mask = (
                    (self.df['PHI'] >= cutoffs['porosity_min']) &
                    (self.df['VSH'] <= cutoffs['vshale_max']) &
                    (self.df['SW'] <= cutoffs['sw_max'])
                )
                
                # Detectar intervalos continuos
                intervals = self.detect_prospect_intervals(prospect_mask)
                self.results['prospect_intervals'] = intervals
                logger.info(f"Intervalos detectados: {len(intervals)}")
                
        except Exception as e:
            logger.warning(f"Análisis de intervalos no disponible: {e}")
    
    def detect_prospect_intervals(self, prospect_mask):
        """Detectar intervalos prospectivos continuos"""
        intervals = []
        depth_col = 'DEPTH' if 'DEPTH' in self.df.columns else self.df.columns[0]
        depths = self.df[depth_col].values
        
        i = 0
        while i < len(prospect_mask):
            if prospect_mask.iloc[i]:
                start_idx = i
                # Encontrar el final del intervalo
                while i < len(prospect_mask) and prospect_mask.iloc[i]:
                    i += 1
                end_idx = i - 1
                
                # Verificar espesor mínimo
                thickness = depths[end_idx] - depths[start_idx]
                if thickness >= self.params['cutoffs']['min_thickness']:
                    intervals.append({
                        'top': float(depths[start_idx]),
                        'base': float(depths[end_idx]),
                        'thickness': float(thickness),
                        'quality': self.assess_interval_quality(start_idx, end_idx)
                    })
            else:
                i += 1
                
        return intervals
    
    def assess_interval_quality(self, start_idx, end_idx):
        """Evaluar calidad del intervalo"""
        avg_phi = self.df['PHI'].iloc[start_idx:end_idx+1].mean()
        avg_vsh = self.df['VSH'].iloc[start_idx:end_idx+1].mean()
        avg_sw = self.df.get('SW', pd.Series([1.0])).iloc[start_idx:end_idx+1].mean()
        
        if avg_phi > 0.18 and avg_vsh < 0.25 and avg_sw < 0.4:
            return "EXCELENTE"
        elif avg_phi > 0.12 and avg_vsh < 0.35 and avg_sw < 0.55:
            return "BUENA"
        else:
            return "REGULAR"
    
    def generate_summary(self):
        """Generar resumen estadístico completo"""
        try:
            self.progress_updated.emit(85, "Calculando estadísticas...")
            
            stats = {}
            calculated_columns = ['VSH', 'PHI', 'K']
            
            for col in calculated_columns:
                if col in self.df.columns:
                    valid_data = self.df[col].dropna()
                    if len(valid_data) > 0:
                        stats[col.lower()] = {
                            'min': float(valid_data.min()),
                            'max': float(valid_data.max()),
                            'mean': float(valid_data.mean()),
                            'median': float(valid_data.median()),
                            'std': float(valid_data.std()),
                            'count': int(len(valid_data))
                        }
            
            # Estadísticas de curvas originales
            original_curves = ['GR', 'RHOB', 'RT', 'ILD', 'ILM', 'NPHI']
            for curve in original_curves:
                if curve in self.df.columns:
                    valid_data = self.df[curve].dropna()
                    if len(valid_data) > 0:
                        stats[f'original_{curve.lower()}'] = {
                            'min': float(valid_data.min()),
                            'max': float(valid_data.max()),
                            'mean': float(valid_data.mean())
                        }
            
            self.results['statistics'] = stats
            self.results['summary'] = self.generate_interpretive_summary(stats)
            logger.info(f"Estadísticas generadas: {len(stats)} parámetros")
            
        except Exception as e:
            logger.error(f"Error generando estadísticas: {e}")
            raise
    
    def generate_interpretive_summary(self, stats):
        """Generar resumen interpretativo"""
        summary = []
        
        if 'phi' in stats:
            avg_phi = stats['phi']['mean']
            if avg_phi > 0.15:
                summary.append("✅ Porosidad EXCELENTE para producción")
            elif avg_phi > 0.10:
                summary.append("📊 Porosidad BUENA, potencial moderado")
            elif avg_phi > 0.05:
                summary.append("⚠️ Porosidad REGULAR, considerar estimulación")
            else:
                summary.append("❌ Porosidad POBRE, potencial limitado")
        
        if 'vsh' in stats:
            avg_vsh = stats['vsh']['mean']
            if avg_vsh < 0.20:
                summary.append("🪨 Bajo contenido de arcilla - Alta calidad")
            elif avg_vsh < 0.35:
                summary.append("🪨 Contenido de arcilla moderado")
            else:
                summary.append("🪨 Alto contenido de arcilla - Calidad reducida")
        
        if 'k' in stats:
            avg_k = stats['k']['mean']
            if avg_k > 100:
                summary.append("🌊 Permeabilidad EXCELENTE - Flujo fácil")
            elif avg_k > 10:
                summary.append("🌊 Permeabilidad BUENA - Flujo moderado")
            elif avg_k > 1:
                summary.append("🌊 Permeabilidad REGULAR - Flujo difícil")
            else:
                summary.append("🌊 Permeabilidad POBRE - Muy bajo flujo")
        
        return summary

# =============================================================================
# COMPONENTES DE INTERFAZ AVANZADOS
# =============================================================================

class AdvancedMplCanvas(FigureCanvasQTAgg):
    """Canvas de matplotlib con capacidades avanzadas de visualización petrofísica"""
    
    def __init__(self, width=10, height=12, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.current_well = None
        self.current_data = None
        
    def plot_triple_combo(self, las_data, tops=None, depth_range=None, analysis_results=None):
        """Crear visualización Triple Combo profesional"""
        self.fig.clear()
        self.current_data = las_data
        
        # Determinar rango de profundidad
        if depth_range:
            depth_min, depth_max = depth_range
        else:
            depth_min = las_data.index.min()
            depth_max = las_data.index.max()
        
        # Crear layout de 4 tracks
        self.axes = [
            self.fig.add_subplot(141),  # Track 1: GR - Litología
            self.fig.add_subplot(142),  # Track 2: Resistividad
            self.fig.add_subplot(143),  # Track 3: Porosidad
            self.fig.add_subplot(144)   # Track 4: Resultados/Análisis
        ]
        
        # Compartir eje Y
        for i in range(1, 4):
            self.axes[i].sharey(self.axes[0])
        
        # TRACK 1: Gamma Ray y Litología
        self._plot_track1(las_data, depth_min, depth_max)
        
        # TRACK 2: Resistividad
        self._plot_track2(las_data, depth_min, depth_max)
        
        # TRACK 3: Porosidad
        self._plot_track3(las_data, depth_min, depth_max)
        
        # TRACK 4: Resultados del Análisis
        self._plot_track4(las_data, analysis_results, depth_min, depth_max)
        
        # Aplicar topes formacionales
        if tops:
            self._plot_formation_tops(tops, depth_min, depth_max)
        
        # Formato final
        self._apply_final_formatting(depth_min, depth_max)
        
        self.fig.suptitle('Triple Combo - Análisis Petrofísico Integrado', 
                         fontsize=14, fontweight='bold', y=0.95)
        self.fig.tight_layout()
        self.draw()
    
    def _plot_track1(self, data, depth_min, depth_max):
        """Plot Track 1: Gamma Ray y Litología"""
        ax = self.axes[0]
        
        if 'GR' in data.columns:
            gr = data['GR']
            depth = data.index
            
            # Curva GR
            ax.plot(gr, depth, color=CURVE_COLORS['GR'], linewidth=1.2, label='GR')
            
            # Relleno para litología
            ax.fill_betweenx(depth, gr, gr.min(), 
                           where=(gr >= gr.min()), 
                           color='green', alpha=0.2)
            
            # Líneas de referencia
            ax.axvline(x=40, color='red', linestyle='--', alpha=0.5, linewidth=0.8)
            ax.axvline(x=120, color='red', linestyle='--', alpha=0.5, linewidth=0.8)
            
            ax.set_xlabel('Gamma Ray (API)', fontweight='bold')
            ax.set_xlim(0, 150)
            ax.grid(True, alpha=0.3)
            
            # Leyenda de litología
            ax.text(0.95, 0.95, 'Lutita', transform=ax.transAxes, 
                   fontsize=8, color='darkgreen', ha='right', va='top',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
            ax.text(0.95, 0.05, 'Arena', transform=ax.transAxes, 
                   fontsize=8, color='darkred', ha='right', va='bottom',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.7))
    
    def _plot_track2(self, data, depth_min, depth_max):
        """Plot Track 2: Resistividad"""
        ax = self.axes[1]
        
        # Buscar curvas de resistividad
        resist_curves = ['ILD', 'ILM', 'RT', 'LLD', 'LLS']
        available_res = [curve for curve in resist_curves if curve in data.columns]
        
        colors = ['red', 'blue', 'purple', 'orange', 'brown']
        for i, curve in enumerate(available_res[:3]):  # Máximo 3 curvas
            color = colors[i % len(colors)]
            ax.semilogx(data[curve], data.index, 
                       color=color, linewidth=1.2, label=curve)
        
        ax.set_xlabel('Resistividad (ohm.m)', fontweight='bold')
        ax.grid(True, alpha=0.3, which='both')
        if available_res:
            ax.legend(fontsize=8, loc='upper right')
    
    def _plot_track3(self, data, depth_min, depth_max):
        """Plot Track 3: Porosidad"""
        ax = self.axes[2]
        
        # Neutrón
        if 'NPHI' in data.columns:
            ax.plot(data['NPHI'], data.index, 
                   color=CURVE_COLORS['NPHI'], linewidth=1.2, label='NPHI')
        
        # Densidad
        if 'RHOB' in data.columns:
            ax.plot(data['RHOB'], data.index, 
                   color=CURVE_COLORS['RHOB'], linewidth=1.2, label='RHOB')
        
        ax.set_xlabel('NPHI / RHOB', fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Escala invertida estándar para porosidad
        if 'NPHI' in data.columns or 'RHOB' in data.columns:
            ax.legend(fontsize=8, loc='upper right')
            ax.invert_xaxis()
    
    def _plot_track4(self, data, analysis_results, depth_min, depth_max):
        """Plot Track 4: Resultados del Análisis"""
        ax = self.axes[3]
        
        if analysis_results and 'vshale' in analysis_results:
            # Plot VShale
            ax.plot(analysis_results['vshale'], data.index, 
                   color='purple', linewidth=1.5, label='VShale')
            
            # Plot Porosidad si está disponible
            if 'porosity' in analysis_results:
                ax.plot(analysis_results['porosity'], data.index, 
                       color='blue', linewidth=1.5, label='Porosidad')
            
            ax.set_xlabel('VShale / Porosidad', fontweight='bold')
            ax.set_xlim(0, 1)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8, loc='upper right')
            
        else:
            # Placeholder para análisis
            ax.text(0.5, 0.5, 'Ejecute el análisis\npara ver resultados', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, style='italic', color='gray')
            ax.set_xlabel('Resultados del Análisis', fontweight='bold')
        
        ax.set_xticks([])
    
    def _plot_formation_tops(self, tops, depth_min, depth_max):
        """Dibujar líneas de topes formacionales"""
        for top_name, depth in tops.items():
            if depth_min <= depth <= depth_max:
                for ax in self.axes[:3]:  # Solo en los primeros 3 tracks
                    ax.axhline(y=depth, color='red', linestyle='--', 
                              alpha=0.8, linewidth=1.5)
                    # Etiqueta del tope
                    ax.text(ax.get_xlim()[0], depth, f' {top_name}', 
                           va='bottom', ha='left', fontsize=8, color='red',
                           bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))
    
    def _apply_final_formatting(self, depth_min, depth_max):
        """Aplicar formato final a todos los ejes"""
        for ax in self.axes:
            ax.set_ylim(depth_max, depth_min)  # Profundidad invertida
            ax.grid(True, alpha=0.3)
            
            # Estilo profesional
            for spine in ax.spines.values():
                spine.set_linewidth(0.5)
                spine.set_color('gray')

# =============================================================================
# APLICACIÓN PRINCIPAL COMPLETA
# =============================================================================

class GeoMindPetrophysicsApp(QMainWindow):
    """Aplicación principal GeoMind Petrophysics - Versión Completa"""
    
    def __init__(self):
        super().__init__()
        
        # Sistema de datos
        self.wells: Dict[str, Dict] = {}
        self.current_well: Optional[str] = None
        self.petro_params = DEFAULT_PETRO_PARAMS.copy()
        self.analysis_results: Dict[str, Dict] = {}
        
        # Configuración inicial
        self.setup_application()
        self.init_ui()
        
        logger.info("Aplicación GeoMind Petrophysics iniciada")
    
    def setup_application(self):
        """Configurar aplicación"""
        self.setWindowTitle("🛢️ GeoMind Petrophysics - Sistema Avanzado de Análisis Petrofísico")
        self.setGeometry(100, 50, 1920, 1080)
        
        # Aplicar estilo profesional
        self.apply_professional_style()
    
    def apply_professional_style(self):
        """Aplicar estilo visual profesional"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['secondary']}, stop:1 {COLORS['dark']});
            }}
            QWidget {{
                background: {COLORS['light']};
                color: {COLORS['dark']};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }}
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['primary']}, stop:1 #2980b9);
                border: none;
                border-radius: 6px;
                color: white;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 12px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 {COLORS['primary']});
                transform: scale(1.02);
            }}
            QPushButton:pressed {{
                background: #21618c;
            }}
            QPushButton:disabled {{
                background: #95a5a6;
                color: #7f8c8d;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 12px;
                background: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: {COLORS['dark']};
                font-weight: bold;
            }}
            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QTextEdit {{
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                background: white;
                font-size: 12px;
                selection-background-color: {COLORS['primary']};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {COLORS['primary']};
            }}
            QLabel {{
                color: {COLORS['dark']};
                padding: 4px;
                font-size: 12px;
            }}
            QListWidget, QTableWidget {{
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                background: white;
                font-size: 11px;
                outline: none;
            }}
            QListWidget::item:selected, QTableWidget::item:selected {{
                background: {COLORS['primary']};
                color: white;
            }}
            QTabWidget::pane {{
                border: 2px solid #bdc3c7;
                background: white;
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: {COLORS['secondary']};
                color: white;
                padding: 10px 20px;
                margin: 2px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['primary']};
            }}
            QTabBar::tab:hover {{
                background: {COLORS['info']};
            }}
            QProgressBar {{
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                text-align: center;
                background: #ecf0f1;
                color: {COLORS['dark']};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['success']}, stop:1 #27ae60);
                border-radius: 4px;
            }}
        """)
    
    def init_ui(self):
        """Inicializar interfaz de usuario completa"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Crear componentes
        self.create_side_panel(main_layout)
        self.create_main_area(main_layout)
        
        # Barra de estado
        self.statusBar().showMessage("✅ GeoMind Petrophysics - Sistema listo")
        
        logger.info("Interfaz de usuario inicializada")
    
    def create_side_panel(self, main_layout):
        """Crear panel lateral de control"""
        side_panel = QWidget()
        side_panel.setMaximumWidth(400)
        side_panel.setMinimumWidth(350)
        side_layout = QVBoxLayout(side_panel)
        
        # Header con logo
        header = QLabel("🛢️ GEO MIND\nPETROPHYSICS")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['info']});
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 25px;
                border-radius: 10px;
                margin: 5px;
            }}
        """)
        side_layout.addWidget(header)
        
        # Grupo de carga de datos
        data_group = QGroupBox("📁 CARGA DE DATOS")
        data_layout = QVBoxLayout(data_group)
        
        # Botones de carga con iconos
        load_actions = [
            ("📄 Cargar Archivo LAS", self.load_las_file),
            ("📂 Cargar Múltiples LAS", self.load_multiple_las),
            ("🗂️ Cargar Carpeta LAS", self.load_las_folder),
            ("📊 Cargar Topes CSV", self.load_tops_csv),
            ("🖼️ Cargar Imágenes Núcleo", self.load_core_images)
        ]
        
        for text, slot in load_actions:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            data_layout.addWidget(btn)
        
        side_layout.addWidget(data_group)
        
        # Lista de pozos
        wells_group = QGroupBox("🏭 POZOS CARGADOS")
        wells_layout = QVBoxLayout(wells_group)
        
        self.wells_list = QListWidget()
        self.wells_list.itemSelectionChanged.connect(self.on_well_selected)
        self.wells_list.setMinimumHeight(200)
        wells_layout.addWidget(self.wells_list)
        
        # Información del pozo seleccionado
        self.well_info = QLabel("ℹ️ Seleccione un pozo para ver detalles")
        self.well_info.setWordWrap(True)
        self.well_info.setStyleSheet(f"""
            QLabel {{
                background: {COLORS['info']}15;
                border: 1px solid {COLORS['info']};
                border-radius: 6px;
                padding: 12px;
                font-size: 11px;
                margin-top: 5px;
            }}
        """)
        wells_layout.addWidget(self.well_info)
        
        side_layout.addWidget(wells_group)
        
        # Acciones rápidas
        actions_group = QGroupBox("⚡ ACCIONES RÁPIDAS")
        actions_layout = QVBoxLayout(actions_group)
        
        quick_actions = [
            ("⚙️ Configurar Parámetros", self.show_parameters_dialog),
            ("🧮 Análisis Petrofísico", self.run_petrophysical_analysis),
            ("📈 Triple Combo", self.show_triple_combo),
            ("🔍 Detectar Intervalos", self.detect_prospect_intervals),
            ("💾 Exportar Resultados", self.export_results)
        ]
        
        for text, slot in quick_actions:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            actions_layout.addWidget(btn)
        
        side_layout.addWidget(actions_group)
        side_layout.addStretch()
        
        main_layout.addWidget(side_panel)
    
    def create_main_area(self, main_layout):
        """Crear área principal con pestañas"""
        self.tab_widget = QTabWidget()
        
        # Pestaña de Visualización Principal
        self.viz_tab = QWidget()
        self.setup_visualization_tab()
        self.tab_widget.addTab(self.viz_tab, "📊 Visualización Principal")
        
        # Pestaña de Análisis
        self.analysis_tab = QWidget()
        self.setup_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "🧮 Análisis Petrofísico")
        
        # Pestaña de Resultados
        self.results_tab = QWidget()
        self.setup_results_tab()
        self.tab_widget.addTab(self.results_tab, "📋 Resultados Detallados")
        
        # Pestaña de Mapa
        self.map_tab = QWidget()
        self.setup_map_tab()
        self.tab_widget.addTab(self.map_tab, "🗺️ Mapa de Pozos")
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_visualization_tab(self):
        """Configurar pestaña de visualización"""
        layout = QVBoxLayout(self.viz_tab)
        
        # Controles de visualización
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Tipo de Visualización:"))
        self.viz_type_combo = QComboBox()
        self.viz_type_combo.addItems([
            "Triple Combo Profesional",
            "Curva Individual", 
            "Múltiples Curvas",
            "Análisis Integrado"
        ])
        controls_layout.addWidget(self.viz_type_combo)
        
        self.viz_apply_btn = QPushButton("🔄 Actualizar Visualización")
        self.viz_apply_btn.clicked.connect(self.update_visualization)
        controls_layout.addWidget(self.viz_apply_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Canvas de visualización avanzado
        self.viz_canvas = AdvancedMplCanvas(width=12, height=10)
        self.viz_toolbar = NavigationToolbar2QT(self.viz_canvas, self)
        layout.addWidget(self.viz_toolbar)
        layout.addWidget(self.viz_canvas)
    
    def setup_analysis_tab(self):
        """Configurar pestaña de análisis"""
        layout = QVBoxLayout(self.analysis_tab)
        
        # Controles de análisis
        analysis_controls = QGridLayout()
        
        analysis_controls.addWidget(QLabel("Tipo de Análisis:"), 0, 0)
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems([
            "Análisis Completo Automático",
            "Solo Propiedades Básicas", 
            "Análisis Avanzado + Archie",
            "Detección de Intervalos"
        ])
        analysis_controls.addWidget(self.analysis_type_combo, 0, 1)
        
        self.run_analysis_btn = QPushButton("🚀 Ejecutar Análisis Petrofísico")
        self.run_analysis_btn.clicked.connect(self.run_petrophysical_analysis)
        self.run_analysis_btn.setStyleSheet(f"background: {COLORS['success']};")
        analysis_controls.addWidget(self.run_analysis_btn, 0, 2)
        
        # Barra de progreso
        self.analysis_progress = QProgressBar()
        self.analysis_progress.setVisible(False)
        analysis_controls.addWidget(self.analysis_progress, 1, 0, 1, 3)
        
        layout.addLayout(analysis_controls)
        
        # Área de resultados del análisis
        self.analysis_results_text = QTextEdit()
        self.analysis_results_text.setReadOnly(True)
        self.analysis_results_text.setPlainText(
            "Bienvenido al módulo de análisis petrofísico de GeoMind.\n\n"
            "Para comenzar:\n"
            "1. Cargue un archivo LAS con curvas GR y RHOB\n"
            "2. Seleccione el pozo en la lista izquierda\n" 
            "3. Ejecute el análisis para ver resultados detallados\n\n"
            "El análisis calculará automáticamente:\n"
            "• Volumen de arcilla (VShale) desde Gamma Ray\n"
            "• Porosidad desde densidad (RHOB)\n"
            "• Permeabilidad desde porosidad\n"
            "• Saturación de agua (ecuación de Archie)\n"
            "• Intervalos prospectivos automáticos"
        )
        layout.addWidget(self.analysis_results_text)
    
    def setup_results_tab(self):
        """Configurar pestaña de resultados"""
        layout = QVBoxLayout(self.results_tab)
        
        # Tabla de resultados estadísticos
        results_header = QLabel("📈 Resultados Estadísticos - Análisis Petrofísico")
        results_header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(results_header)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Parámetro", "Mínimo", "Máximo", "Promedio", "Mediana", "Desviación"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.results_table)
        
        # Gráfico de resultados
        results_viz_label = QLabel("📊 Distribución de Propiedades Petrofísicas")
        results_viz_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(results_viz_label)
        
        self.results_canvas = AdvancedMplCanvas(width=10, height=6)
        layout.addWidget(self.results_canvas)
    
    def setup_map_tab(self):
        """Configurar pestaña de mapa"""
        layout = QVBoxLayout(self.map_tab)
        
        map_header = QLabel("🗺️ Mapa de Ubicación de Pozos")
        map_header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(map_header)
        
        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(500)
        layout.addWidget(self.map_view)
        
        # Generar mapa inicial
        self.generate_wells_map()
    
    # =========================================================================
    # MÉTODOS PRINCIPALES MEJORADOS
    # =========================================================================
    
    def load_las_file(self):
        """Cargar archivo LAS individual con manejo robusto"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar archivo LAS", "",
                "Archivos LAS (*.las *.LAS);;Todos los archivos (*)"
            )
            
            if file_path:
                self.process_las_file(file_path)
                
        except Exception as e:
            self.show_error(f"Error cargando archivo LAS: {str(e)}")
            logger.error(f"Error cargando LAS: {e}")
    
    def load_multiple_las(self):
        """Cargar múltiples archivos LAS con progreso"""
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Seleccionar archivos LAS", "",
                "Archivos LAS (*.las *.LAS);;Todos los archivos (*)"
            )
            
            if not file_paths:
                return
            
            # Diálogo de progreso
            progress = QProgressDialog("Cargando archivos LAS...", "Cancelar", 0, len(file_paths), self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            loaded_count = 0
            for i, file_path in enumerate(file_paths):
                if progress.wasCanceled():
                    break
                    
                try:
                    self.process_las_file(file_path)
                    loaded_count += 1
                except Exception as e:
                    logger.warning(f"Error cargando {file_path}: {e}")
                
                progress.setValue(i + 1)
                QApplication.processEvents()
            
            progress.close()
            self.show_success(f"Se cargaron {loaded_count} de {len(file_paths)} archivos")
            
        except Exception as e:
            self.show_error(f"Error cargando múltiples archivos: {str(e)}")
    
    def load_las_folder(self):
        """Cargar carpeta completa de archivos LAS"""
        try:
            folder = QFileDialog.getExistingDirectory(
                self, "Seleccionar carpeta con archivos LAS"
            )
            
            if not folder:
                return
            
            # Buscar archivos LAS
            las_files = []
            for file in os.listdir(folder):
                if file.lower().endswith('.las'):
                    las_files.append(os.path.join(folder, file))
            
            if not las_files:
                self.show_warning("No se encontraron archivos LAS en la carpeta seleccionada")
                return
            
            # Cargar con progreso
            progress = QProgressDialog(f"Cargando {len(las_files)} archivos...", "Cancelar", 0, len(las_files), self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            loaded_count = 0
            for i, file_path in enumerate(las_files):
                if progress.wasCanceled():
                    break
                    
                try:
                    self.process_las_file(file_path)
                    loaded_count += 1
                except Exception as e:
                    logger.warning(f"Error cargando {file_path}: {e}")
                
                progress.setValue(i + 1)
                QApplication.processEvents()
            
            progress.close()
            self.show_success(f"Se cargaron {loaded_count} de {len(las_files)} archivos desde la carpeta")
            self.generate_wells_map()
            
        except Exception as e:
            self.show_error(f"Error cargando carpeta: {str(e)}")
    
    def process_las_file(self, file_path):
        """Procesar archivo LAS individual con extracción completa de metadatos"""
        try:
            logger.info(f"Procesando archivo LAS: {file_path}")
            
            # Leer archivo LAS
            las = lasio.read(file_path)
            df = las.df().reset_index()
            
            # Normalizar columna de profundidad
            if df.columns[0].lower() not in ('depth', 'dept', 'md'):
                df.rename(columns={df.columns[0]: 'DEPTH'}, inplace=True)
            
            # Generar clave única para el pozo
            well_key = self.generate_well_key(las, file_path)
            
            # Extraer metadatos completos
            metadata = self.extract_complete_metadata(las, file_path, well_key)
            
            # Guardar datos del pozo
            self.wells[well_key] = {
                'las': las,
                'df': df,
                'metadata': metadata,
                'tops': {},
                'core_images': [],
                'analysis': None,
                'loaded_at': datetime.now()
            }
            
            # Actualizar interfaces
            self.refresh_wells_list()
            self.update_visualization_controls()
            
            logger.info(f"Pozo {well_key} cargado exitosamente: {len(df.columns)} curvas, {len(df)} registros")
            self.statusBar().showMessage(f"✅ Pozo {well_key} cargado - {len(df.columns)} curvas")
            
        except Exception as e:
            error_msg = f"Error procesando {file_path}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def generate_well_key(self, las, file_path):
        """Generar clave única para el pozo con prioridad de metadatos"""
        try:
            # Prioridad 1: UWI (Unique Well Identifier)
            if hasattr(las, 'well') and 'UWI' in las.well:
                uwi = str(las.well['UWI'].value).strip()
                if uwi and uwi != 'None':
                    return uwi
            
            # Prioridad 2: Nombre del pozo
            if hasattr(las, 'well') and 'WELL' in las.well:
                well_name = str(las.well['WELL'].value).strip()
                if well_name and well_name != 'None':
                    return well_name
            
            # Prioridad 3: Nombre del archivo
            return os.path.splitext(os.path.basename(file_path))[0]
            
        except Exception:
            return os.path.splitext(os.path.basename(file_path))[0]
    
    def extract_complete_metadata(self, las, file_path, well_key):
        """Extraer metadatos completos del archivo LAS"""
        metadata = {
            'name': well_key,
            'path': file_path,
            'loaded_at': datetime.now().isoformat(),
            'coords': None,
            'field': None,
            'company': None,
            'country': None,
            'basin': None,
            'elevation': None,
            'curves': []
        }
        
        try:
            if hasattr(las, 'well'):
                # Información de ubicación
                if 'LAT' in las.well and 'LON' in las.well:
                    try:
                        lat = float(las.well['LAT'].value)
                        lon = float(las.well['LON'].value)
                        metadata['coords'] = f"{lat},{lon}"
                    except:
                        pass
                
                # Información de elevación
                if 'ELEV' in las.well:
                    try:
                        metadata['elevation'] = float(las.well['ELEV'].value)
                    except:
                        pass
                
                # Información operacional
                for field, key in [('FLD', 'field'), ('COMP', 'company'), 
                                 ('CTRY', 'country'), ('BASIN', 'basin')]:
                    if field in las.well and las.well[field].value:
                        metadata[key] = str(las.well[field].value)
            
            # Lista de curvas disponibles
            if hasattr(las, 'curves'):
                metadata['curves'] = [curve.mnemonic for curve in las.curves 
                                    if curve.mnemonic not in ['DEPT', 'DEPTH']]
                
        except Exception as e:
            logger.warning(f"Error extrayendo metadatos: {e}")
        
        return metadata
    
    def load_tops_csv(self):
        """Cargar topes estratigráficos desde CSV"""
        if not self.current_well:
            self.show_warning("Seleccione un pozo primero")
            return
            
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar archivo de topes", "",
                "Archivos CSV (*.csv);;Todos los archivos (*)"
            )
            
            if file_path:
                df = pd.read_csv(file_path)
                
                # Validar formato
                if 'Tope' in df.columns and 'Profundidad' in df.columns:
                    tops = dict(zip(df['Tope'], df['Profundidad']))
                    self.wells[self.current_well]['tops'] = tops
                    
                    self.show_success(f"✅ Topes cargados: {len(tops)} formaciones estratigráficas")
                    self.update_visualization()
                    
                else:
                    self.show_error("El archivo CSV debe contener las columnas 'Tope' y 'Profundidad'")
                    
        except Exception as e:
            self.show_error(f"Error cargando topes: {str(e)}")
            logger.error(f"Error cargando topes CSV: {e}")
    
    def load_core_images(self):
        """Cargar imágenes de núcleo con metadatos"""
        if not self.current_well:
            self.show_warning("Seleccione un pozo primero")
            return
            
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Seleccionar imágenes de núcleo", "",
                "Imágenes (*.png *.jpg *.jpeg *.tiff *.bmp);;Todos los archivos (*)"
            )
            
            if file_paths:
                for file_path in file_paths:
                    self.wells[self.current_well]['core_images'].append({
                        'path': file_path,
                        'depth_range': None,
                        'description': os.path.basename(file_path),
                        'loaded_at': datetime.now()
                    })
                
                self.show_success(f"✅ {len(file_paths)} imágenes de núcleo cargadas")
                
        except Exception as e:
            self.show_error(f"Error cargando imágenes: {str(e)}")
    
    def on_well_selected(self):
        """Manejar selección de pozo con actualización completa"""
        items = self.wells_list.selectedItems()
        if not items:
            return
            
        self.current_well = items[0].text()
        self.update_well_display()
        self.update_visualization()
    
    def update_well_display(self):
        """Actualizar display de información del pozo seleccionado"""
        if not self.current_well or self.current_well not in self.wells:
            return
            
        well = self.wells[self.current_well]
        df = well['df']
        metadata = well['metadata']
        
        # Información detallada
        depth_range = self.get_depth_range(df)
        curve_count = len([c for c in df.columns if c not in ['DEPTH', 'DEPT']])
        
        info_html = f"""
        <div style='font-family: Arial; font-size: 11px;'>
            <h3 style='color: {COLORS["primary"]}; margin: 0;'>{self.current_well}</h3>
            <hr style='margin: 5px 0;'>
            <p><b>📏 Profundidad:</b> {depth_range}</p>
            <p><b>📊 Curvas:</b> {curve_count} disponibles</p>
            <p><b>📈 Registros:</b> {len(df):,} puntos</p>
            <p><b>🏭 Campo:</b> {metadata.get('field', 'No especificado')}</p>
            <p><b>🏢 Compañía:</b> {metadata.get('company', 'No especificada')}</p>
            <p><b>🪨 Topes:</b> {len(well.get('tops', {}))} formaciones</p>
            <p><b>🖼️ Núcleos:</b> {len(well.get('core_images', []))} imágenes</p>
            <p><b>📅 Cargado:</b> {well['loaded_at'].strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        """
        
        self.well_info.setText(info_html)
        self.update_visualization_controls()
    
    def get_depth_range(self, df):
        """Obtener rango de profundidad formateado"""
        try:
            depth_col = 'DEPTH' if 'DEPTH' in df.columns else df.columns[0]
            depths = pd.to_numeric(df[depth_col], errors='coerce')
            if not depths.empty:
                return f"{depths.min():.1f} - {depths.max():.1f} m"
        except:
            pass
        return "No disponible"
    
    def update_visualization_controls(self):
        """Actualizar controles de visualización según el pozo seleccionado"""
        # Esta función se implementaría para actualizar comboboxes, etc.
        pass
    
    def update_visualization(self):
        """Actualizar visualización según selección actual"""
        if not self.current_well:
            return
            
        viz_type = self.viz_type_combo.currentText()
        
        try:
            if viz_type == "Triple Combo Profesional":
                self.show_triple_combo()
            elif viz_type == "Curva Individual":
                self.show_single_curve()
            elif viz_type == "Múltiples Curvas":
                self.show_multiple_curves()
            elif viz_type == "Análisis Integrado":
                self.show_integrated_analysis()
                
        except Exception as e:
            self.show_error(f"Error en visualización: {str(e)}")
    
    def show_triple_combo(self):
        """Mostrar Triple Combo profesional"""
        if not self.current_well:
            return
            
        well = self.wells[self.current_well]
        tops = well.get('tops', {})
        analysis = well.get('analysis')
        
        self.viz_canvas.plot_triple_combo(
            las_data=well['df'],
            tops=tops,
            analysis_results=analysis
        )
    
    def show_single_curve(self):
        """Mostrar curva individual - placeholder"""
        self.show_triple_combo()
    
    def show_multiple_curves(self):
        """Mostrar múltiples curvas - placeholder"""
        self.show_triple_combo()
    
    def show_integrated_analysis(self):
        """Mostrar análisis integrado - placeholder"""
        self.show_triple_combo()
    
    def run_petrophysical_analysis(self):
        """Ejecutar análisis petrofísico completo - VERSIÓN CORREGIDA"""
        if not self.current_well:
            self.show_warning("⚠️ Seleccione un pozo primero")
            return
            
        well = self.wells[self.current_well]
        df = well['df']
        
        # Validar curvas mínimas requeridas
        if 'GR' not in df.columns or 'RHOB' not in df.columns:
            self.show_error("❌ Se requieren curvas GR y RHOB para el análisis básico")
            return
        
        logger.info(f"Iniciando análisis petrofísico para {self.current_well}")
        
        try:
            # Crear y configurar hilo de cálculo
            self.calc_thread = AdvancedPetroCalculationThread(
                df=df,
                params=self.petro_params,
                well_name=self.current_well
            )
            
            # Conectar señales
            self.calc_thread.progress_updated.connect(self.on_analysis_progress)
            self.calc_thread.calculation_finished.connect(self.on_analysis_finished)
            self.calc_thread.error_occurred.connect(self.on_analysis_error)
            self.calc_thread.warning_emitted.connect(self.on_analysis_warning)
            
            # Configurar y mostrar diálogo de progreso
            self.progress_dialog = QProgressDialog(
                "Iniciando análisis petrofísico...", 
                "Cancelar", 0, 100, self
            )
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setWindowTitle("GeoMind - Análisis en Progreso")
            self.progress_dialog.show()
            
            # INICIAR EL HILO - ESTA ES LA LÍNEA CRÍTICA
            self.calc_thread.start()
            
            self.statusBar().showMessage("🔄 Ejecutando análisis petrofísico...")
            
        except Exception as e:
            self.show_error(f"Error iniciando análisis: {str(e)}")
            logger.error(f"Error iniciando análisis: {e}")
    
    def on_analysis_progress(self, value, message):
        """Manejar actualización de progreso del análisis"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setValue(value)
            self.progress_dialog.setLabelText(message)
    
    def on_analysis_finished(self, results):
        """Manejar finalización exitosa del análisis - VERSIÓN CORREGIDA"""
        logger.info(f"Análisis completado para {self.current_well}")
        
        # Cerrar diálogo de progreso
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
        
        # Guardar resultados
        if self.current_well:
            self.wells[self.current_well]['analysis'] = results
            self.analysis_results[self.current_well] = results
            
            # ACTUALIZAR INTERFAZ CON RESULTADOS - ESTO ES CRÍTICO
            self.display_analysis_results(results)
            self.update_results_table(results)
            self.update_visualization()  # Actualizar gráficos con resultados
            
        self.show_success("✅ Análisis petrofísico completado exitosamente")
        self.statusBar().showMessage(f"✅ Análisis completado - {self.current_well}")
        
        # Cambiar a pestaña de análisis para mostrar resultados
        self.tab_widget.setCurrentIndex(1)
    
    def on_analysis_error(self, error_msg):
        """Manejar error en el análisis"""
        logger.error(f"Error en análisis: {error_msg}")
        
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            
        self.show_error(f"❌ Error en análisis: {error_msg}")
        self.statusBar().showMessage("❌ Error en análisis")
    
    def on_analysis_warning(self, warning_msg):
        """Manejar advertencias del análisis"""
        logger.warning(f"Advertencia en análisis: {warning_msg}")
        self.statusBar().showMessage(f"⚠️ {warning_msg}")
    
    def display_analysis_results(self, results):
        """Mostrar resultados del análisis en el widget de texto - VERSIÓN CORREGIDA"""
        report = "=" * 70 + "\n"
        report += "         GEO MIND PETROPHYSICS - REPORTE DE ANÁLISIS\n"
        report += "=" * 70 + "\n\n"
        
        if 'statistics' in results and results['statistics']:
            stats = results['statistics']
            
            # Encabezado de estadísticas
            report += "📊 ESTADÍSTICAS PETROFÍSICAS\n"
            report += "-" * 50 + "\n\n"
            
            # Propiedades calculadas
            calculated_params = ['vsh', 'phi', 'k']
            for param in calculated_params:
                if param in stats:
                    values = stats[param]
                    report += f"🔹 {param.upper()}:\n"
                    report += f"   Mínimo: {values['min']:.4f}\n"
                    report += f"   Máximo: {values['max']:.4f}\n"
                    report += f"   Promedio: {values['mean']:.4f}\n"
                    report += f"   Mediana: {values['median']:.4f}\n"
                    report += f"   Desviación: {values['std']:.4f}\n"
                    report += f"   Puntos válidos: {values['count']:,}\n\n"
            
            # Interpretación cualitativa
            report += "🎯 INTERPRETACIÓN CUALITATIVA\n"
            report += "-" * 50 + "\n\n"
            
            if 'summary' in results and results['summary']:
                for line in results['summary']:
                    report += f"{line}\n"
            else:
                report += "Ejecute análisis completo para interpretación detallada\n"
            
            # Intervalos prospectivos
            if 'prospect_intervals' in results and results['prospect_intervals']:
                intervals = results['prospect_intervals']
                report += f"\n🔍 INTERVALOS PROSPECTIVOS DETECTADOS: {len(intervals)}\n"
                report += "-" * 50 + "\n\n"
                
                for i, interval in enumerate(intervals, 1):
                    report += f"Zona {i} ({interval['quality']}):\n"
                    report += f"  • Top: {interval['top']:.1f} m\n"
                    report += f"  • Base: {interval['base']:.1f} m\n"
                    report += f"  • Espesor: {interval['thickness']:.1f} m\n\n"
            
        else:
            report += "No se pudieron calcular resultados. Verifique los datos de entrada.\n"
        
        report += "\n" + "=" * 70 + "\n"
        report += "Fin del reporte - GeoMind Petrophysics\n"
        report += "=" * 70
        
        # ACTUALIZAR EL WIDGET DE TEXTO - ESTO ES CRÍTICO
        self.analysis_results_text.setPlainText(report)
        
        logger.info("Resultados del análisis mostrados en la interfaz")
    
    def update_results_table(self, results):
        """Actualizar tabla de resultados con estadísticas"""
        if 'statistics' not in results:
            return
            
        stats = results['statistics']
        
        # Filtrar parámetros calculados (excluir curvas originales)
        calculated_params = {k: v for k, v in stats.items() 
                           if not k.startswith('original_')}
        
        self.results_table.setRowCount(len(calculated_params))
        
        for i, (param, values) in enumerate(calculated_params.items()):
            self.results_table.setItem(i, 0, QTableWidgetItem(param.upper()))
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{values['min']:.4f}"))
            self.results_table.setItem(i, 2, QTableWidgetItem(f"{values['max']:.4f}"))
            self.results_table.setItem(i, 3, QTableWidgetItem(f"{values['mean']:.4f}"))
            self.results_table.setItem(i, 4, QTableWidgetItem(f"{values['median']:.4f}"))
            self.results_table.setItem(i, 5, QTableWidgetItem(f"{values['std']:.4f}"))
    
    def detect_prospect_intervals(self):
        """Ejecutar detección de intervalos prospectivos"""
        self.run_petrophysical_analysis()  # Reutilizar el análisis completo
    
    def show_parameters_dialog(self):
        """Mostrar diálogo de parámetros - placeholder"""
        self.show_info("El diálogo de parámetros estará disponible en la próxima versión")
    
    def export_results(self):
        """Exportar resultados - placeholder"""
        self.show_info("La exportación de resultados estará disponible en la próxima versión")
    
    def generate_wells_map(self):
        """Generar mapa de ubicación de pozos"""
        try:
            # Crear mapa base centrado en América del Sur
            m = folium.Map(location=[-15, -60], zoom_start=4)
            
            # Añadir cada pozo al mapa
            for well_name, well_data in self.wells.items():
                coords = self._get_well_coordinates(well_data)
                if coords:
                    # Popup con información del pozo
                    popup_content = f"""
                    <div style='width: 250px;'>
                        <h4 style='color: {COLORS["primary"]}; margin: 5px 0;'>{well_name}</h4>
                        <hr style='margin: 5px 0;'>
                        <p><b>Curvas:</b> {len(well_data['df'].columns)}</p>
                        <p><b>Registros:</b> {len(well_data['df']):,}</p>
                        <p><b>Topes:</b> {len(well_data.get('tops', {}))}</p>
                        <p><b>Campo:</b> {well_data['metadata'].get('field', 'N/A')}</p>
                    </div>
                    """
                    
                    folium.Marker(
                        location=coords,
                        popup=folium.Popup(popup_content, max_width=300),
                        tooltip=well_name,
                        icon=folium.Icon(color='red', icon='info-sign')
                    ).add_to(m)
            
            # Guardar mapa temporal
            tmp_path = os.path.join(tempfile.gettempdir(), "geomind_wells_map.html")
            m.save(tmp_path)
            self.map_view.load(QUrl.fromLocalFile(os.path.abspath(tmp_path)))
            
        except Exception as e:
            logger.warning(f"Error generando mapa: {e}")
    
    def _get_well_coordinates(self, well_data):
        """Obtener coordenadas del pozo desde metadatos"""
        try:
            if well_data.get('metadata') and well_data['metadata'].get('coords'):
                coords_str = well_data['metadata']['coords']
                if ',' in coords_str:
                    lat, lon = map(float, coords_str.split(','))
                    return [lat, lon]
        except:
            pass
        return None
    
    def refresh_wells_list(self):
        """Actualizar lista de pozos cargados"""
        self.wells_list.clear()
        for well_name in sorted(self.wells.keys()):
            self.wells_list.addItem(well_name)
    
    # =========================================================================
    # MÉTODOS DE UTILIDAD MEJORADOS
    # =========================================================================
    
    def show_success(self, message):
        """Mostrar mensaje de éxito"""
        QMessageBox.information(self, "✅ Éxito", message)
        self.statusBar().showMessage(f"✅ {message}")
        logger.info(message)
    
    def show_warning(self, message):
        """Mostrar mensaje de advertencia"""
        QMessageBox.warning(self, "⚠️ Advertencia", message)
        self.statusBar().showMessage(f"⚠️ {message}")
        logger.warning(message)
    
    def show_error(self, message):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, "❌ Error", message)
        self.statusBar().showMessage(f"❌ {message}")
        logger.error(message)
    
    def show_info(self, message):
        """Mostrar mensaje informativo"""
        QMessageBox.information(self, "ℹ️ Información", message)
        self.statusBar().showMessage(f"ℹ️ {message}")

# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

def main():
    """Función principal de la aplicación"""
    try:
        # Configurar aplicación
        app = QApplication(sys.argv)
        app.setApplicationName("GeoMind Petrophysics")
        app.setApplicationVersion("3.0.0")
        app.setOrganizationName("GeoMind Solutions")
        app.setOrganizationDomain("geomind-solutions.com")
        
        # Crear y mostrar ventana principal
        window = GeoMindPetrophysicsApp()
        window.showMaximized()
        
        logger.info("Aplicación GeoMind Petrophysics ejecutándose")
        
        # Ejecutar loop principal
        return app.exec_()
        
    except Exception as e:
        logger.critical(f"Error crítico iniciando aplicación: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())