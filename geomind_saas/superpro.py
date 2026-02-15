# PIAP-A PRO v4.0 - SISTEMA COMPLETO DE ANÁLISIS PETROFÍSICO
import sys
import os
import numpy as np
import pandas as pd
import lasio
from datetime import datetime
import tempfile
from scipy.interpolate import griddata
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import scipy.stats as stats

# PyQt6 Imports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QPushButton, QLabel, QMessageBox, QFileDialog,
                            QProgressBar, QGroupBox, QListWidget, QComboBox, QDoubleSpinBox,
                            QSpinBox, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                            QSplitter, QGridLayout, QCheckBox, QRadioButton, QButtonGroup,
                            QLineEdit, QScrollArea, QFrame, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter

# Matplotlib imports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

# =============================================================================
# CLASES DEL NÚCLEO - CÁLCULOS
# =============================================================================

class ProjectManager:
    """Gestor de proyectos"""
    def __init__(self):
        self.current_project = None
        self.projects = {}
        self.current_data = None
        self.well_info = {}
    
    def create_project(self, name, path):
        project_data = {
            'name': name,
            'path': path,
            'wells': {},
            'created': datetime.now(),
            'units': {'depth': 'm', 'porosity': 'v/v', 'permeability': 'mD'}
        }
        self.projects[name] = project_data
        self.current_project = name
        return True
    
    def load_project(self, path):
        try:
            project_name = os.path.basename(path)
            self.current_project = project_name
            return True
        except Exception as e:
            print(f"Error loading project: {e}")
            return False
    
    def save_current_data(self):
        """Guarda datos actuales en el proyecto"""
        if self.current_project and self.current_data is not None:
            well_name = self.well_info.get('name', 'Well_1')
            self.projects[self.current_project]['wells'][well_name] = {
                'data': self.current_data,
                'info': self.well_info,
                'loaded': datetime.now()
            }

class DataImporter:
    """Sistema de importación de datos"""
    
    def __init__(self):
        self.supported_formats = ['.las', '.csv', '.xlsx', '.xls']
    
    def can_import(self, file_path):
        return any(file_path.lower().endswith(fmt) for fmt in self.supported_formats)
    
    def import_las(self, file_path):
        """Importa archivos LAS reales"""
        try:
            las = lasio.read(file_path)
            df = las.df()
            df.reset_index(inplace=True)
            
            well_info = {
                'name': getattr(las.well, 'WELL', {}).get('value', 'Unknown'),
                'company': getattr(las.well, 'COMP', {}).get('value', 'Unknown'),
                'field': getattr(las.well, 'FLD', {}).get('value', 'Unknown'),
                'curves': list(df.columns),
                'start_depth': df.iloc[0, 0] if len(df) > 0 else 0,
                'end_depth': df.iloc[-1, 0] if len(df) > 0 else 0
            }
            
            return df, True, well_info
            
        except Exception as e:
            print(f"Error importing LAS: {e}")
            return None, False, {}
    
    def import_csv(self, file_path):
        """Importa archivos CSV"""
        try:
            df = pd.read_csv(file_path)
            
            depth_cols = [col for col in df.columns if 'depth' in col.lower() or 'prof' in col.lower()]
            if depth_cols:
                df.set_index(depth_cols[0], inplace=True)
            
            well_info = {
                'name': os.path.basename(file_path),
                'company': 'CSV Import',
                'curves': list(df.columns),
                'start_depth': df.index[0] if len(df) > 0 else 0,
                'end_depth': df.index[-1] if len(df) > 0 else 0
            }
            
            return df, True, well_info
            
        except Exception as e:
            print(f"Error importing CSV: {e}")
            return None, False, {}
    
    def import_file(self, file_path):
        """Importa cualquier archivo soportado"""
        if file_path.lower().endswith('.las'):
            return self.import_las(file_path)
        elif file_path.lower().endswith(('.csv', '.txt')):
            return self.import_csv(file_path)
        else:
            return None, False, {}

class PetrofisicaCalculator:
    """Calculadora de propiedades petrofísicas - MÓDULO COMPLETO"""
    
    @staticmethod
    def calcular_vsh(gr_curve, gr_min=None, gr_max=None, method='linear'):
        """Calcula volumen de shale usando diferentes métodos"""
        if gr_min is None:
            gr_min = np.nanpercentile(gr_curve, 5)
        if gr_max is None:
            gr_max = np.nanpercentile(gr_curve, 95)
        
        if gr_max - gr_min == 0:
            return np.zeros_like(gr_curve)
        
        vsh_linear = (gr_curve - gr_min) / (gr_max - gr_min)
        vsh_linear = np.clip(vsh_linear, 0, 1)
        
        if method == 'clavier':
            vsh = 1.7 - (3.38 - (vsh_linear + 0.7)**2)**0.5
            return np.clip(vsh, 0, 1)
        elif method == 'larionov':
            vsh = 0.083 * (2**(3.7 * vsh_linear) - 1)
            return np.clip(vsh, 0, 1)
        else:  # linear
            return vsh_linear
    
    @staticmethod
    def calcular_porosidad(rhob_curve, nphi_curve=None, method='density'):
        """Calcula porosidad usando diferentes métodos"""
        RHOB_MATRIX = 2.65
        RHOB_FLUID = 1.0
        NPHI_MATRIX = -0.05
        NPHI_FLUID = 1.0
        
        if method == 'density' or method == 'neutron-density':
            phi_density = (RHOB_MATRIX - rhob_curve) / (RHOB_MATRIX - RHOB_FLUID)
            phi_density = np.clip(phi_density, 0, 0.4)
            
            if method == 'density' or nphi_curve is None:
                return phi_density
            else:
                phi_neutron = (nphi_curve - NPHI_MATRIX) / (NPHI_FLUID - NPHI_MATRIX)
                phi_neutron = np.clip(phi_neutron, 0, 0.4)
                return (phi_density + phi_neutron) / 2
        
        elif method == 'neutron' and nphi_curve is not None:
            phi_neutron = (nphi_curve - NPHI_MATRIX) / (NPHI_FLUID - NPHI_MATRIX)
            return np.clip(phi_neutron, 0, 0.4)
        else:
            raise ValueError("Método no soportado o curvas faltantes")
    
    @staticmethod
    def calcular_sw(rt_curve, phi_curve, rw=0.05, vsh_curve=None, method='archie', 
                   a=1.0, m=2.0, n=2.0, b=1.0):
        """Calcula saturación de agua usando diferentes métodos"""
        phi_safe = np.where(phi_curve > 0.01, phi_curve, 0.01)
        rt_safe = np.where(rt_curve > 0.01, rt_curve, 0.01)
        
        if method == 'archie':
            f = a / (phi_safe ** m)
            sw = (f * rw / rt_safe) ** (1/n)
        
        elif method == 'simandoux' and vsh_curve is not None:
            f = a / (phi_safe ** m)
            rsh = 1.0  # Resistividad de shale, podría ser parámetro
            term1 = (f * rw) / (rt_safe * phi_safe**2)
            term2 = (vsh_curve**2) / (4 * rsh**2)
            sw = (-vsh_curve/(2*rsh) + (term1 + term2)**0.5)**2
        
        elif method == 'indonesia' and vsh_curve is not None:
            f = a / (phi_safe ** m)
            rsh = 1.0
            term1 = 1/rt_safe**0.5
            term2 = (vsh_curve**(1 - 0.5*vsh_curve))/rsh**0.5
            sw = ((term1 + term2**2)**0.5 * (phi_safe**(m/2) / (a*rw)**0.5))**(2/n)
        
        else:
            raise ValueError("Método no soportado o parámetros faltantes")
        
        return np.clip(sw, 0.01, 1.0)
    
    @staticmethod
    def calcular_perm_k0(phi_curve, sw_curve=None, a=100, b=3, c=1):
        """Calcula permeabilidad usando relación empírica"""
        # Relación Kozeny-Carman modificada
        perm = a * (phi_curve**b) / ((1 - phi_curve)**c)
        
        if sw_curve is not None:
            # Ajustar por saturación de agua irreducible
            sw_irreducible = 0.2
            perm = perm * ((1 - sw_curve) / (1 - sw_irreducible))**2
        
        return np.clip(perm, 0.1, 10000)

class GeoestadisticaCalculator:
    """Calculadora geoestadística - MÓDULO COMPLETO"""
    
    @staticmethod
    def calcular_variograma(x, y, z, max_lag=None, num_lags=20):
        if max_lag is None:
            max_lag = np.max([np.ptp(x), np.ptp(y)]) / 2
        
        lag_size = max_lag / num_lags
        lags = np.linspace(lag_size, max_lag, num_lags)
        semivariances = []
        
        for lag in lags:
            distances = []
            value_diffs = []
            
            for i in range(len(x)):
                for j in range(i+1, len(x)):
                    dist = np.sqrt((x[i]-x[j])**2 + (y[i]-y[j])**2)
                    if lag - lag_size/2 <= dist <= lag + lag_size/2:
                        distances.append(dist)
                        value_diffs.append((z[i] - z[j])**2)
            
            if len(value_diffs) > 0:
                semivariances.append(np.mean(value_diffs) / 2)
            else:
                semivariances.append(0)
        
        return lags, np.array(semivariances)
    
    @staticmethod
    def kriging_ordinario(x_known, y_known, z_known, x_target, y_target, variogram_range=100):
        n_known = len(x_known)
        n_target = len(x_target)
        
        z_pred = np.zeros(n_target)
        
        for i in range(n_target):
            distances = np.sqrt((x_known - x_target[i])**2 + (y_known - y_target[i])**2)
            
            # Modelo de variograma esférico
            h = distances / variogram_range
            gamma = 1.5 * np.minimum(h, 1) - 0.5 * np.minimum(h, 1)**3
            
            # Matriz de covarianza
            C = 1 - gamma
            C_matrix = np.outer(C, C)
            np.fill_diagonal(C_matrix, 1)
            
            # Vector de covarianzas
            c_vec = 1 - (1.5 * np.minimum(distances/variogram_range, 1) - 
                        0.5 * np.minimum(distances/variogram_range, 1)**3)
            
            # Resolver sistema kriging
            try:
                weights = np.linalg.solve(C_matrix, c_vec)
                weights = weights / np.sum(weights)
                z_pred[i] = np.sum(weights * z_known)
            except:
                # Fallback a inversa de distancia
                weights = 1 / (distances + 1e-8)
                weights = weights / np.sum(weights)
                z_pred[i] = np.sum(weights * z_known)
        
        return z_pred

class SimulacionYacimiento:
    """Simulador de yacimiento - MÓDULO COMPLETO"""
    
    def __init__(self):
        self.datos_produccion = {}
        self.propiedades_fluidos = {}
    
    def configurar_fluido(self, tipo_fluido, gravedad_api, rs=0, viscosidad=1.0, bo=1.2):
        self.propiedades_fluidos[tipo_fluido] = {
            'gravedad_api': gravedad_api,
            'rs': rs,
            'viscosidad': viscosidad,
            'bo': bo  # Factor de volumen de formación
        }
    
    def simular_produccion(self, volumen_inicial, presion_inicial, tipo_fluido, 
                          area=1.0, espesor=10, tiempo_meses=60, metodo='exponencial'):
        
        fluid_props = self.propiedades_fluidos.get(tipo_fluido)
        if not fluid_props:
            raise ValueError("Configurar fluido primero")
        
        tiempo = np.arange(0, tiempo_meses + 1)
        produccion_mensual = []
        presion = []
        volumen_remaining = []
        
        vol_actual = volumen_inicial
        pres_actual = presion_inicial
        
        # Parámetros de declinación según método
        if metodo == 'exponencial':
            decline_rate = 0.05
        elif metodo == 'hiperbolico':
            decline_rate = 0.1
            b_factor = 0.8
        else:  # armónico
            decline_rate = 0.15
        
        for t in tiempo:
            if metodo == 'exponencial':
                tasa_produccion = volumen_inicial * decline_rate * np.exp(-decline_rate * t)
            elif metodo == 'hiperbolico':
                tasa_produccion = volumen_inicial * decline_rate / (1 + b_factor * decline_rate * t)**(1/b_factor)
            else:  # armónico
                tasa_produccion = volumen_inicial * decline_rate / (1 + decline_rate * t)
            
            if vol_actual > tasa_produccion:
                produccion_mensual.append(tasa_produccion)
                vol_actual -= tasa_produccion
                pres_actual = presion_inicial * (vol_actual / volumen_inicial)
            else:
                produccion_mensual.append(vol_actual)
                vol_actual = 0
                pres_actual = 0
            
            volumen_remaining.append(vol_actual)
            presion.append(pres_actual)
        
        return {
            'tiempo': tiempo,
            'produccion_mensual': produccion_mensual,
            'volumen_remaining': volumen_remaining,
            'presion': presion,
            'produccion_acumulada': np.cumsum(produccion_mensual),
            'volumen_original': volumen_inicial,
            'recuperacion_final': np.sum(produccion_mensual) / volumen_inicial * 100
        }
    
    def monte_carlo_volumen(self, volumen_medio, desviacion_volumen, n_simulaciones=1000):
        """Análisis de incertidumbre con Monte Carlo"""
        volumenes = np.random.normal(volumen_medio, desviacion_volumen, n_simulaciones)
        volumenes = np.clip(volumenes, 0, volumen_medio * 3)
        
        p10 = np.percentile(volumenes, 10)
        p50 = np.percentile(volumenes, 50)
        p90 = np.percentile(volumenes, 90)
        
        return {
            'volumenes': volumenes,
            'p10': p10,
            'p50': p50,
            'p90': p90,
            'media': np.mean(volumenes),
            'desviacion': np.std(volumenes)
        }

# =============================================================================
# WIDGETS DE VISUALIZACIÓN
# =============================================================================

class MplCanvas(FigureCanvas):
    """Widget de Matplotlib integrado"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

class WellPlotWidget(QWidget):
    """Widget para gráficos de pozo con tracks múltiples"""
    def __init__(self):
        super().__init__()
        self.data = None
        self.tracks = []
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        self.btn_add_track = QPushButton("Agregar Track")
        self.btn_clear_tracks = QPushButton("Limpiar Tracks")
        toolbar_layout.addWidget(self.btn_add_track)
        toolbar_layout.addWidget(self.btn_clear_tracks)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Área de gráficos
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_widget)
        
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)
        
        # Conectar señales
        self.btn_add_track.clicked.connect(self.add_track)
        self.btn_clear_tracks.clicked.connect(self.clear_tracks)
    
    def set_data(self, data):
        self.data = data
        self.clear_tracks()
    
    def add_track(self, curve_name=None):
        if self.data is None:
            return
        
        track = SingleTrackWidget()
        track.set_data(self.data)
        if curve_name:
            track.add_curve(curve_name)
        
        self.scroll_layout.addWidget(track)
        self.tracks.append(track)
    
    def clear_tracks(self):
        for track in self.tracks:
            track.setParent(None)
        self.tracks.clear()

class SingleTrackWidget(QWidget):
    """Track individual para gráfico de pozo"""
    def __init__(self):
        super().__init__()
        self.data = None
        self.curves = []
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Controles del track
        controls_layout = QHBoxLayout()
        self.combo_curves = QComboBox()
        self.btn_add_curve = QPushButton("Agregar")
        self.btn_clear = QPushButton("Limpiar")
        
        controls_layout.addWidget(self.combo_curves)
        controls_layout.addWidget(self.btn_add_curve)
        controls_layout.addWidget(self.btn_clear)
        
        layout.addLayout(controls_layout)
        
        # Gráfico
        self.canvas = MplCanvas(self, width=3, height=8)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        # Conectar señales
        self.btn_add_curve.clicked.connect(self.add_current_curve)
        self.btn_clear.clicked.connect(self.clear_plot)
    
    def set_data(self, data):
        self.data = data
        self.combo_curves.clear()
        if data is not None:
            self.combo_curves.addItems(data.columns)
    
    def add_curve(self, curve_name):
        if self.data is None or curve_name not in self.data.columns:
            return
        
        self.curves.append(curve_name)
        self.update_plot()
    
    def add_current_curve(self):
        curve_name = self.combo_curves.currentText()
        self.add_curve(curve_name)
    
    def clear_plot(self):
        self.curves.clear()
        self.update_plot()
    
    def update_plot(self):
        if self.data is None:
            return
        
        self.canvas.fig.clear()
        ax = self.canvas.fig.add_subplot(111)
        
        depth_col = self.data.columns[0]  # Asumimos que la primera columna es profundidad
        
        for curve in self.curves:
            if curve != depth_col:
                ax.plot(self.data[curve], self.data[depth_col], label=curve, linewidth=1)
        
        ax.set_ylabel('Profundidad')
        if self.curves:
            ax.set_xlabel(', '.join(self.curves))
        ax.invert_yaxis()
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        self.canvas.draw()

class CrossPlotWidget(QWidget):
    """Widget para crossplots"""
    def __init__(self):
        super().__init__()
        self.data = None
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Controles
        controls_layout = QGridLayout()
        
        controls_layout.addWidget(QLabel("Eje X:"), 0, 0)
        self.combo_x = QComboBox()
        controls_layout.addWidget(self.combo_x, 0, 1)
        
        controls_layout.addWidget(QLabel("Eje Y:"), 1, 0)
        self.combo_y = QComboBox()
        controls_layout.addWidget(self.combo_y, 1, 1)
        
        controls_layout.addWidget(QLabel("Color por:"), 2, 0)
        self.combo_color = QComboBox()
        self.combo_color.addItem("Ninguno")
        controls_layout.addWidget(self.combo_color, 2, 1)
        
        self.btn_plot = QPushButton("Generar Crossplot")
        controls_layout.addWidget(self.btn_plot, 3, 0, 1, 2)
        
        layout.addLayout(controls_layout)
        
        # Gráfico
        self.canvas = MplCanvas(self, width=8, height=6)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        self.btn_plot.clicked.connect(self.generate_plot)
    
    def set_data(self, data):
        self.data = data
        self.combo_x.clear()
        self.combo_y.clear()
        self.combo_color.clear()
        
        if data is not None:
            self.combo_x.addItems(data.columns)
            self.combo_y.addItems(data.columns)
            self.combo_color.addItem("Ninguno")
            self.combo_color.addItems(data.columns)
    
    def generate_plot(self):
        if self.data is None:
            return
        
        x_col = self.combo_x.currentText()
        y_col = self.combo_y.currentText()
        color_col = self.combo_color.currentText()
        
        if not x_col or not y_col:
            return
        
        self.canvas.fig.clear()
        ax = self.canvas.fig.add_subplot(111)
        
        if color_col != "Ninguno":
            scatter = ax.scatter(self.data[x_col], self.data[y_col], 
                               c=self.data[color_col], alpha=0.6, cmap='viridis')
            self.canvas.fig.colorbar(scatter, ax=ax, label=color_col)
        else:
            ax.scatter(self.data[x_col], self.data[y_col], alpha=0.6)
        
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(f'Crossplot: {x_col} vs {y_col}')
        ax.grid(True, alpha=0.3)
        
        # Calcular y mostrar correlación
        correlation = self.data[x_col].corr(self.data[y_col])
        ax.text(0.05, 0.95, f'Correlación: {correlation:.3f}', 
                transform=ax.transAxes, bbox=dict(boxstyle="round", facecolor='wheat', alpha=0.5))
        
        self.canvas.draw()

# =============================================================================
# PESTAÑAS PRINCIPALES
# =============================================================================

class ProjectTab(QWidget):
    """Pestaña de Gestión de Proyectos"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Información del proyecto
        info_group = QGroupBox("Información del Proyecto")
        info_layout = QVBoxLayout()
        
        self.lbl_project_name = QLabel("No hay proyecto activo")
        self.lbl_project_path = QLabel("")
        self.lbl_well_count = QLabel("Pozos cargados: 0")
        
        info_layout.addWidget(self.lbl_project_name)
        info_layout.addWidget(self.lbl_project_path)
        info_layout.addWidget(self.lbl_well_count)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Acciones del proyecto
        actions_group = QGroupBox("Acciones")
        actions_layout = QVBoxLayout()
        
        self.btn_new_project = QPushButton("Nuevo Proyecto")
        self.btn_load_project = QPushButton("Cargar Proyecto")
        self.btn_save_project = QPushButton("Guardar Proyecto")
        
        actions_layout.addWidget(self.btn_new_project)
        actions_layout.addWidget(self.btn_load_project)
        actions_layout.addWidget(self.btn_save_project)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Configuración
        config_group = QGroupBox("Configuración")
        config_layout = QGridLayout()
        
        config_layout.addWidget(QLabel("Unidad de profundidad:"), 0, 0)
        self.combo_depth_unit = QComboBox()
        self.combo_depth_unit.addItems(["m", "ft"])
        config_layout.addWidget(self.combo_depth_unit, 0, 1)
        
        config_layout.addWidget(QLabel("Rw por defecto:"), 1, 0)
        self.spin_default_rw = QDoubleSpinBox()
        self.spin_default_rw.setValue(0.05)
        self.spin_default_rw.setSingleStep(0.01)
        config_layout.addWidget(self.spin_default_rw, 1, 1)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Conectar señales
        self.btn_new_project.clicked.connect(self.create_project)
        self.btn_load_project.clicked.connect(self.load_project)
        self.btn_save_project.clicked.connect(self.save_project)
    
    def create_project(self):
        path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta para Nuevo Proyecto")
        if path:
            name = os.path.basename(path)
            success = self.main_window.project_manager.create_project(name, path)
            if success:
                self.update_display()
                QMessageBox.information(self, "Éxito", f"Proyecto '{name}' creado")
    
    def load_project(self):
        path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta del Proyecto")
        if path:
            success = self.main_window.project_manager.load_project(path)
            if success:
                self.update_display()
                QMessageBox.information(self, "Éxito", "Proyecto cargado")
    
    def save_project(self):
        self.main_window.project_manager.save_current_data()
        QMessageBox.information(self, "Éxito", "Datos guardados en el proyecto")
    
    def update_display(self):
        pm = self.main_window.project_manager
        if pm.current_project:
            project = pm.projects[pm.current_project]
            self.lbl_project_name.setText(f"Proyecto: {pm.current_project}")
            self.lbl_project_path.setText(f"Ruta: {project['path']}")
            self.lbl_well_count.setText(f"Pozos cargados: {len(project['wells'])}")
        else:
            self.lbl_project_name.setText("No hay proyecto activo")
            self.lbl_project_path.setText("")
            self.lbl_well_count.setText("Pozos cargados: 0")

class ImportTab(QWidget):
    """Pestaña de Importación de Datos"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Importación
        import_group = QGroupBox("Importación de Datos")
        import_layout = QVBoxLayout()
        
        self.btn_import = QPushButton("Importar Archivo LAS/CSV")
        self.lbl_file_info = QLabel("No se ha cargado archivo")
        self.lbl_file_info.setWordWrap(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        import_layout.addWidget(self.btn_import)
        import_layout.addWidget(self.lbl_file_info)
        import_layout.addWidget(self.progress_bar)
        
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # Vista previa de datos
        preview_group = QGroupBox("Vista Previa de Datos")
        preview_layout = QVBoxLayout()
        
        self.table_preview = QTableWidget()
        self.table_preview.setRowCount(10)
        self.table_preview.setColumnCount(5)
        
        preview_layout.addWidget(self.table_preview)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        self.setLayout(layout)
        
        self.btn_import.clicked.connect(self.import_data)
    
    def import_data(self):
        if not self.main_window.project_manager.current_project:
            QMessageBox.warning(self, "Advertencia", "Primero crea o carga un proyecto")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo de datos", "",
            "Archivos LAS (*.las);;CSV (*.csv);;Todos los archivos (*)"
        )
        
        if file_path and self.main_window.data_importer.can_import(file_path):
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(30)
            
            df, success, well_info = self.main_window.data_importer.import_file(file_path)
            
            self.progress_bar.setValue(80)
            
            if success and df is not None:
                self.main_window.project_manager.current_data = df
                self.main_window.project_manager.well_info = well_info
                
                self.update_display(df, well_info, file_path)
                self.main_window.notify_data_loaded()
                
                self.progress_bar.setValue(100)
                QMessageBox.information(self, "Éxito", 
                                      f"Datos importados: {len(df)} registros, {len(df.columns)} curvas")
            else:
                QMessageBox.warning(self, "Error", "No se pudieron importar los datos")
            
            self.progress_bar.setVisible(False)
    
    def update_display(self, df, well_info, file_path):
        # Información del archivo
        file_info = f"Archivo: {os.path.basename(file_path)}\n"
        file_info += f"Pozo: {well_info.get('name', 'N/A')}\n"
        file_info += f"Compañía: {well_info.get('company', 'N/A')}\n"
        file_info += f"Registros: {len(df)}, Curvas: {len(df.columns)}"
        self.lbl_file_info.setText(file_info)
        
        # Vista previa de tabla
        self.table_preview.setRowCount(min(10, len(df)))
        self.table_preview.setColumnCount(min(5, len(df.columns)))
        
        # Headers
        headers = list(df.columns)[:5]
        self.table_preview.setHorizontalHeaderLabels(headers)
        
        # Datos
        for i in range(min(10, len(df))):
            for j in range(min(5, len(df.columns))):
                value = df.iloc[i, j]
                self.table_preview.setItem(i, j, QTableWidgetItem(f"{value:.4f}"))

class PetrofisicaTab(QWidget):
    """Pestaña de Cálculos Petrofísicos"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.calculator = PetrofisicaCalculator()
        self.initUI()
    
    def initUI(self):
        layout = QHBoxLayout()
        
        # Panel izquierdo - controles
        left_panel = QWidget()
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout()
        
        # Parámetros globales
        params_group = QGroupBox("Parámetros Globales")
        params_layout = QGridLayout()
        
        params_layout.addWidget(QLabel("Rw:"), 0, 0)
        self.spin_rw = QDoubleSpinBox()
        self.spin_rw.setValue(0.05)
        params_layout.addWidget(self.spin_rw, 0, 1)
        
        params_layout.addWidget(QLabel("a:"), 1, 0)
        self.spin_a = QDoubleSpinBox()
        self.spin_a.setValue(1.0)
        params_layout.addWidget(self.spin_a, 1, 1)
        
        params_layout.addWidget(QLabel("m:"), 2, 0)
        self.spin_m = QDoubleSpinBox()
        self.spin_m.setValue(2.0)
        params_layout.addWidget(self.spin_m, 2, 1)
        
        params_layout.addWidget(QLabel("n:"), 3, 0)
        self.spin_n = QDoubleSpinBox()
        self.spin_n.setValue(2.0)
        params_layout.addWidget(self.spin_n, 3, 1)
        
        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)
        
        # Selección de curvas
        curves_group = QGroupBox("Selección de Curvas")
        curves_layout = QGridLayout()
        
        curves_layout.addWidget(QLabel("GR:"), 0, 0)
        self.combo_gr = QComboBox()
        curves_layout.addWidget(self.combo_gr, 0, 1)
        
        curves_layout.addWidget(QLabel("RHOB:"), 1, 0)
        self.combo_rhob = QComboBox()
        curves_layout.addWidget(self.combo_rhob, 1, 1)
        
        curves_layout.addWidget(QLabel("NPHI:"), 2, 0)
        self.combo_nphi = QComboBox()
        curves_layout.addWidget(self.combo_nphi, 2, 1)
        
        curves_layout.addWidget(QLabel("RT:"), 3, 0)
        self.combo_rt = QComboBox()
        curves_layout.addWidget(self.combo_rt, 3, 1)
        
        curves_group.setLayout(curves_layout)
        left_layout.addWidget(curves_group)
        
        # Cálculos
        calc_group = QGroupBox("Cálculos")
        calc_layout = QVBoxLayout()
        
        self.btn_vsh = QPushButton("Calcular Vsh")
        self.btn_porosity = QPushButton("Calcular Porosidad")
        self.btn_sw = QPushButton("Calcular Sw")
        self.btn_perm = QPushButton("Calcular Permeabilidad")
        
        calc_layout.addWidget(self.btn_vsh)
        calc_layout.addWidget(self.btn_porosity)
        calc_layout.addWidget(self.btn_sw)
        calc_layout.addWidget(self.btn_perm)
        
        calc_group.setLayout(calc_layout)
        left_layout.addWidget(calc_group)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # Panel derecho - resultados
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Gráfico
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)
        
        # Tabla de resultados
        self.table_results = QTableWidget()
        self.table_results.setColumnCount(3)
        self.table_results.setHorizontalHeaderLabels(["Profundidad", "Parámetro", "Valor"])
        right_layout.addWidget(self.table_results)
        
        right_panel.setLayout(right_layout)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # Conectar señales
        self.btn_vsh.clicked.connect(self.calcular_vsh)
        self.btn_porosity.clicked.connect(self.calcular_porosidad)
        self.btn_sw.clicked.connect(self.calcular_sw)
        self.btn_perm.clicked.connect(self.calcular_perm)
    
    def update_curves(self):
        """Actualiza los combos con las curvas disponibles"""
        if self.main_window.project_manager.current_data is not None:
            curves = list(self.main_window.project_manager.current_data.columns)
            for combo in [self.combo_gr, self.combo_rhob, self.combo_nphi, self.combo_rt]:
                combo.clear()
                combo.addItems(curves)
    
    def calcular_vsh(self):
        data = self.main_window.project_manager.current_data
        if data is None:
            QMessageBox.warning(self, "Error", "No hay datos cargados")
            return
        
        gr_curve = self.combo_gr.currentText()
        if not gr_curve:
            QMessageBox.warning(self, "Error", "Selecciona curva GR")
            return
        
        vsh = self.calculator.calcular_vsh(data[gr_curve])
        self.main_window.project_manager.current_data['VSH'] = vsh
        
        self.graficar_resultado(data.iloc[:, 0], vsh, 'VSH', 'green')
        self.actualizar_tabla_resultados(data.iloc[:, 0], vsh, 'VSH')
    
    def calcular_porosidad(self):
        data = self.main_window.project_manager.current_data
        if data is None:
            QMessageBox.warning(self, "Error", "No hay datos cargados")
            return
        
        rhob_curve = self.combo_rhob.currentText()
        if not rhob_curve:
            QMessageBox.warning(self, "Error", "Selecciona curva RHOB")
            return
        
        nphi_curve = self.combo_nphi.currentText() if self.combo_nphi.currentText() else None
        nphi_data = data[nphi_curve] if nphi_curve else None
        
        phi = self.calculator.calcular_porosidad(data[rhob_curve], nphi_data)
        self.main_window.project_manager.current_data['PHI'] = phi
        
        self.graficar_resultado(data.iloc[:, 0], phi, 'Porosidad', 'blue')
        self.actualizar_tabla_resultados(data.iloc[:, 0], phi, 'PHI')
    
    def calcular_sw(self):
        data = self.main_window.project_manager.current_data
        if data is None:
            QMessageBox.warning(self, "Error", "No hay datos cargados")
            return
        
        rt_curve = self.combo_rt.currentText()
        if not rt_curve or 'PHI' not in data.columns:
            QMessageBox.warning(self, "Error", "Selecciona curva RT y calcula porosidad primero")
            return
        
        rw = self.spin_rw.value()
        a = self.spin_a.value()
        m = self.spin_m.value()
        n = self.spin_n.value()
        
        vsh_data = data['VSH'] if 'VSH' in data.columns else None
        
        sw = self.calculator.calcular_sw(data[rt_curve], data['PHI'], rw, vsh_data, 
                                       'archie', a, m, n)
        self.main_window.project_manager.current_data['SW'] = sw
        
        self.graficar_resultado(data.iloc[:, 0], sw, 'Sw', 'red')
        self.actualizar_tabla_resultados(data.iloc[:, 0], sw, 'SW')
    
    def calcular_perm(self):
        data = self.main_window.project_manager.current_data
        if data is None or 'PHI' not in data.columns:
            QMessageBox.warning(self, "Error", "Calcula porosidad primero")
            return
        
        sw_data = data['SW'] if 'SW' in data.columns else None
        perm = self.calculator.calcular_perm_k0(data['PHI'], sw_data)
        self.main_window.project_manager.current_data['PERM'] = perm
        
        self.graficar_resultado(data.iloc[:, 0], perm, 'Permeabilidad', 'purple')
        self.actualizar_tabla_resultados(data.iloc[:, 0], perm, 'PERM')
    
    def graficar_resultado(self, depth, values, nombre, color):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        ax.plot(values, depth, color=color, linewidth=1, label=nombre)
        ax.set_ylabel('Profundidad')
        ax.set_xlabel(nombre)
        ax.invert_yaxis()
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_title(f'Cálculo de {nombre}')
        
        self.canvas.draw()
    
    def actualizar_tabla_resultados(self, depth, values, parametro):
        self.table_results.setRowCount(min(100, len(depth)))
        
        for i in range(min(100, len(depth))):
            self.table_results.setItem(i, 0, QTableWidgetItem(f"{depth.iloc[i]:.2f}"))
            self.table_results.setItem(i, 1, QTableWidgetItem(parametro))
            self.table_results.setItem(i, 2, QTableWidgetItem(f"{values[i]:.4f}"))

class VisualizationTab(QWidget):
    """Pestaña de Visualización Avanzada"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Tabs de visualización
        self.viz_tabs = QTabWidget()
        
        # Sub-pestaña: Tracks de pozo
        self.well_plot_tab = WellPlotWidget()
        self.viz_tabs.addTab(self.well_plot_tab, "Tracks de Pozo")
        
        # Sub-pestaña: Crossplots
        self.crossplot_tab = CrossPlotWidget()
        self.viz_tabs.addTab(self.crossplot_tab, "Crossplots")
        
        # Sub-pestaña: Histogramas
        self.histogram_tab = QWidget()
        self.setup_histogram_tab()
        self.viz_tabs.addTab(self.histogram_tab, "Histogramas")
        
        layout.addWidget(self.viz_tabs)
        self.setLayout(layout)
    
    def setup_histogram_tab(self):
        layout = QVBoxLayout()
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.combo_hist_curve = QComboBox()
        self.btn_histogram = QPushButton("Generar Histograma")
        
        controls_layout.addWidget(QLabel("Curva:"))
        controls_layout.addWidget(self.combo_hist_curve)
        controls_layout.addWidget(self.btn_histogram)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Gráfico
        self.hist_canvas = MplCanvas(self, width=8, height=6)
        layout.addWidget(self.hist_canvas)
        
        self.histogram_tab.setLayout(layout)
        
        self.btn_histogram.clicked.connect(self.generate_histogram)
    
    def update_data(self):
        """Actualiza todos los widgets con los datos actuales"""
        data = self.main_window.project_manager.current_data
        if data is not None:
            self.well_plot_tab.set_data(data)
            self.crossplot_tab.set_data(data)
            
            # Actualizar combo de histograma
            self.combo_hist_curve.clear()
            self.combo_hist_curve.addItems(data.columns)
    
    def generate_histogram(self):
        data = self.main_window.project_manager.current_data
        if data is None:
            return
        
        curve = self.combo_hist_curve.currentText()
        if not curve:
            return
        
        self.hist_canvas.fig.clear()
        ax = self.hist_canvas.fig.add_subplot(111)
        
        ax.hist(data[curve].dropna(), bins=30, alpha=0.7, edgecolor='black')
        ax.set_xlabel(curve)
        ax.set_ylabel('Frecuencia')
        ax.set_title(f'Histograma de {curve}')
        ax.grid(True, alpha=0.3)
        
        # Estadísticas
        stats_text = f'Media: {data[curve].mean():.3f}\nDesv: {data[curve].std():.3f}'
        ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, 
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        self.hist_canvas.draw()

class GeoestadisticaTab(QWidget):
    """Pestaña de Geoestadística"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.calculator = GeoestadisticaCalculator()
        self.pozos = {}
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.btn_add_pozo = QPushButton("Agregar Pozo")
        self.btn_variograma = QPushButton("Calcular Variograma")
        self.btn_kriging = QPushButton("Interpolar con Kriging")
        
        controls_layout.addWidget(self.btn_add_pozo)
        controls_layout.addWidget(self.btn_variograma)
        controls_layout.addWidget(self.btn_kriging)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Área principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo - datos
        left_panel = QWidget()
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout()
        
        # Tabla de pozos
        self.table_pozos = QTableWidget()
        self.table_pozos.setColumnCount(5)
        self.table_pozos.setHorizontalHeaderLabels(["Pozo", "X", "Y", "Propiedad", "Valor"])
        left_layout.addWidget(self.table_pozos)
        
        left_panel.setLayout(left_layout)
        
        # Panel derecho - gráficos
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        self.geo_canvas = MplCanvas(self, width=10, height=8)
        right_layout.addWidget(self.geo_canvas)
        
        right_panel.setLayout(right_layout)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # Conectar señales
        self.btn_add_pozo.clicked.connect(self.agregar_pozo)
        self.btn_variograma.clicked.connect(self.calcular_variograma)
        self.btn_kriging.clicked.connect(self.interpolar_kriging)
    
    def agregar_pozo(self):
        pozo_id = f"Pozo_{len(self.pozos) + 1}"
        x = np.random.uniform(0, 1000)
        y = np.random.uniform(0, 1000)
        
        # Usar datos actuales si están disponibles
        data = self.main_window.project_manager.current_data
        if data is not None and 'PHI' in data.columns:
            valor = np.mean(data['PHI'].dropna())
        else:
            valor = np.random.uniform(0.1, 0.3)
        
        self.pozos[pozo_id] = {'x': x, 'y': y, 'propiedad': 'Porosidad', 'valor': valor}
        self.actualizar_tabla()
    
    def actualizar_tabla(self):
        self.table_pozos.setRowCount(len(self.pozos))
        
        for i, (pozo_id, datos) in enumerate(self.pozos.items()):
            self.table_pozos.setItem(i, 0, QTableWidgetItem(pozo_id))
            self.table_pozos.setItem(i, 1, QTableWidgetItem(f"{datos['x']:.2f}"))
            self.table_pozos.setItem(i, 2, QTableWidgetItem(f"{datos['y']:.2f}"))
            self.table_pozos.setItem(i, 3, QTableWidgetItem(datos['propiedad']))
            self.table_pozos.setItem(i, 4, QTableWidgetItem(f"{datos['valor']:.3f}"))
    
    def calcular_variograma(self):
        if len(self.pozos) < 3:
            QMessageBox.warning(self, "Advertencia", "Se necesitan al menos 3 pozos")
            return
        
        x = np.array([d['x'] for d in self.pozos.values()])
        y = np.array([d['y'] for d in self.pozos.values()])
        z = np.array([d['valor'] for d in self.pozos.values()])
        
        lags, semivariances = self.calculator.calcular_variograma(x, y, z)
        
        self.geo_canvas.fig.clear()
        ax = self.geo_canvas.fig.add_subplot(111)
        
        ax.plot(lags, semivariances, 'bo-', linewidth=2, markersize=4)
        ax.set_xlabel('Distancia (m)')
        ax.set_ylabel('Semivarianza')
        ax.set_title('Variograma Experimental')
        ax.grid(True, alpha=0.3)
        
        self.geo_canvas.draw()
    
    def interpolar_kriging(self):
        if len(self.pozos) < 2:
            QMessageBox.warning(self, "Advertencia", "Se necesitan al menos 2 pozos")
            return
        
        x_known = np.array([d['x'] for d in self.pozos.values()])
        y_known = np.array([d['y'] for d in self.pozos.values()])
        z_known = np.array([d['valor'] for d in self.pozos.values()])
        
        # Crear grid
        x_grid = np.linspace(min(x_known)-50, max(x_known)+50, 50)
        y_grid = np.linspace(min(y_known)-50, max(y_known)+50, 50)
        X, Y = np.meshgrid(x_grid, y_grid)
        
        z_pred = self.calculator.kriging_ordinario(x_known, y_known, z_known, 
                                                 X.flatten(), Y.flatten())
        Z = z_pred.reshape(X.shape)
        
        self.geo_canvas.fig.clear()
        ax = self.geo_canvas.fig.add_subplot(111)
        
        contour = ax.contourf(X, Y, Z, levels=20, alpha=0.7, cmap='viridis')
        scatter = ax.scatter(x_known, y_known, c=z_known, s=100, 
                           edgecolors='black', cmap='viridis')
        
        ax.set_xlabel('Coordenada X (m)')
        ax.set_ylabel('Coordenada Y (m)')
        ax.set_title('Mapa de Interpolación - Kriging')
        
        # Añadir barra de color
        cbar = self.geo_canvas.fig.colorbar(contour, ax=ax)
        cbar.set_label('Porosidad (v/v)')
        
        self.geo_canvas.draw()

class SimulacionTab(QWidget):
    """Pestaña de Simulación de Yacimiento"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.simulador = SimulacionYacimiento()
        self.initUI()
        self.configurar_fluidos()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Controles
        controls_group = QGroupBox("Parámetros de Simulación")
        controls_layout = QGridLayout()
        
        controls_layout.addWidget(QLabel("Tipo de Fluido:"), 0, 0)
        self.combo_fluido = QComboBox()
        self.combo_fluido.addItems(["Petróleo Liviano", "Petróleo Pesado", "Gas"])
        controls_layout.addWidget(self.combo_fluido, 0, 1)
        
        controls_layout.addWidget(QLabel("Volumen Inicial (Mbbl):"), 1, 0)
        self.spin_volumen = QDoubleSpinBox()
        self.spin_volumen.setRange(100, 100000)
        self.spin_volumen.setValue(1000)
        controls_layout.addWidget(self.spin_volumen, 1, 1)
        
        controls_layout.addWidget(QLabel("Presión Inicial (psi):"), 2, 0)
        self.spin_presion = QDoubleSpinBox()
        self.spin_presion.setRange(1000, 10000)
        self.spin_presion.setValue(5000)
        controls_layout.addWidget(self.spin_presion, 2, 1)
        
        controls_layout.addWidget(QLabel("Área (acres):"), 3, 0)
        self.spin_area = QDoubleSpinBox()
        self.spin_area.setRange(10, 10000)
        self.spin_area.setValue(100)
        controls_layout.addWidget(self.spin_area, 3, 1)
        
        controls_layout.addWidget(QLabel("Espesor (ft):"), 4, 0)
        self.spin_espesor = QDoubleSpinBox()
        self.spin_espesor.setRange(1, 500)
        self.spin_espesor.setValue(50)
        controls_layout.addWidget(self.spin_espesor, 4, 1)
        
        controls_layout.addWidget(QLabel("Meses de Simulación:"), 5, 0)
        self.spin_meses = QSpinBox()
        self.spin_meses.setRange(12, 240)
        self.spin_meses.setValue(60)
        controls_layout.addWidget(self.spin_meses, 5, 1)
        
        controls_layout.addWidget(QLabel("Método de Declinación:"), 6, 0)
        self.combo_metodo = QComboBox()
        self.combo_metodo.addItems(["Exponencial", "Hiperbólico", "Armónico"])
        controls_layout.addWidget(self.combo_metodo, 6, 1)
        
        self.btn_simular = QPushButton("Ejecutar Simulación")
        controls_layout.addWidget(self.btn_simular, 7, 0, 1, 2)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Gráficos
        self.sim_canvas = MplCanvas(self, width=10, height=8)
        layout.addWidget(self.sim_canvas)
        
        # Resultados
        self.text_resultados = QTextEdit()
        self.text_resultados.setMaximumHeight(150)
        layout.addWidget(self.text_resultados)
        
        # Monte Carlo
        mc_group = QGroupBox("Análisis de Incertidumbre (Monte Carlo)")
        mc_layout = QGridLayout()
        
        mc_layout.addWidget(QLabel("Volumen Medio (Mbbl):"), 0, 0)
        self.spin_vol_medio = QDoubleSpinBox()
        self.spin_vol_medio.setValue(1000)
        mc_layout.addWidget(self.spin_vol_medio, 0, 1)
        
        mc_layout.addWidget(QLabel("Desviación (Mbbl):"), 1, 0)
        self.spin_vol_desv = QDoubleSpinBox()
        self.spin_vol_desv.setValue(200)
        mc_layout.addWidget(self.spin_vol_desv, 1, 1)
        
        mc_layout.addWidget(QLabel("Simulaciones:"), 2, 0)
        self.spin_mc_sim = QSpinBox()
        self.spin_mc_sim.setValue(1000)
        mc_layout.addWidget(self.spin_mc_sim, 2, 1)
        
        self.btn_monte_carlo = QPushButton("Ejecutar Monte Carlo")
        mc_layout.addWidget(self.btn_monte_carlo, 3, 0, 1, 2)
        
        mc_group.setLayout(mc_layout)
        layout.addWidget(mc_group)
        
        self.setLayout(layout)
        
        # Conectar señales
        self.btn_simular.clicked.connect(self.ejecutar_simulacion)
        self.btn_monte_carlo.clicked.connect(self.ejecutar_monte_carlo)
    
    def configurar_fluidos(self):
        self.simulador.configurar_fluido("Petróleo Liviano", gravedad_api=35, 
                                       viscosidad=0.8, rs=500, bo=1.2)
        self.simulador.configurar_fluido("Petróleo Pesado", gravedad_api=15,
                                       viscosidad=15.0, rs=100, bo=1.1)
        self.simulador.configurar_fluido("Gas", gravedad_api=60,
                                       viscosidad=0.02, rs=0, bo=0.01)
    
    def ejecutar_simulacion(self):
        try:
            tipo_fluido = self.combo_fluido.currentText()
            volumen = self.spin_volumen.value()
            presion = self.spin_presion.value()
            area = self.spin_area.value()
            espesor = self.spin_espesor.value()
            meses = self.spin_meses.value()
            metodo = self.combo_metodo.currentText().lower()
            
            resultados = self.simulador.simular_produccion(
                volumen, presion, tipo_fluido, area, espesor, meses, metodo
            )
            
            self.mostrar_resultados(resultados, tipo_fluido)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en simulación: {str(e)}")
    
    def mostrar_resultados(self, resultados, tipo_fluido):
        # Gráficos
        self.sim_canvas.fig.clear()
        
        # 4 subplots
        ax1 = self.sim_canvas.fig.add_subplot(221)
        ax2 = self.sim_canvas.fig.add_subplot(222)
        ax3 = self.sim_canvas.fig.add_subplot(223)
        ax4 = self.sim_canvas.fig.add_subplot(224)
        
        # Producción mensual
        ax1.plot(resultados['tiempo'], resultados['produccion_mensual'], 'b-', linewidth=2)
        ax1.set_xlabel('Tiempo (meses)')
        ax1.set_ylabel('Producción Mensual (Mbbl)')
        ax1.set_title('Curva de Declinación')
        ax1.grid(True, alpha=0.3)
        
        # Producción acumulada
        ax2.plot(resultados['tiempo'], resultados['produccion_acumulada'], 'g-', linewidth=2)
        ax2.set_xlabel('Tiempo (meses)')
        ax2.set_ylabel('Producción Acumulada (Mbbl)')
        ax2.set_title('Producción Acumulada')
        ax2.grid(True, alpha=0.3)
        
        # Presión
        ax3.plot(resultados['tiempo'], resultados['presion'], 'r-', linewidth=2)
        ax3.set_xlabel('Tiempo (meses)')
        ax3.set_ylabel('Presión (psi)')
        ax3.set_title('Comportamiento de Presión')
        ax3.grid(True, alpha=0.3)
        
        # Volumen remanente
        ax4.plot(resultados['tiempo'], resultados['volumen_remaining'], 'purple', linewidth=2)
        ax4.set_xlabel('Tiempo (meses)')
        ax4.set_ylabel('Volumen Remanente (Mbbl)')
        ax4.set_title('Volumen en el Yacimiento')
        ax4.grid(True, alpha=0.3)
        
        self.sim_canvas.fig.tight_layout()
        self.sim_canvas.draw()
        
        # Resultados numéricos
        prod_total = resultados['produccion_acumulada'][-1]
        prod_max = max(resultados['produccion_mensual'])
        vida_util = len([p for p in resultados['produccion_mensual'] if p > 0.01 * prod_max])
        
        texto = f"""=== RESULTADOS DE SIMULACIÓN ===
Tipo de Fluido: {tipo_fluido}
Volumen Original: {resultados['volumen_original']:.0f} Mbbl
Producción Total: {prod_total:.0f} Mbbl
Vida Útil Estimada: {vida_util} meses
Producción Máxima Mensual: {prod_max:.1f} Mbbl
Recuperación Final: {resultados['recuperacion_final']:.1f}%"""
        
        self.text_resultados.setText(texto)
    
    def ejecutar_monte_carlo(self):
        vol_medio = self.spin_vol_medio.value()
        vol_desv = self.spin_vol_desv.value()
        n_sim = self.spin_mc_sim.value()
        
        resultados = self.simulador.monte_carlo_volumen(vol_medio, vol_desv, n_sim)
        
        # Mostrar resultados
        texto = f"""=== ANÁLISIS MONTE CARLO ===
Simulaciones: {n_sim}
P10: {resultados['p10']:.0f} Mbbl
P50: {resultados['p50']:.0f} Mbbl
P90: {resultados['p90']:.0f} Mbbl
Media: {resultados['media']:.0f} Mbbl
Desviación: {resultados['desviacion']:.0f} Mbbl"""
        
        self.text_resultados.setText(texto)
        
        # Histograma
        self.sim_canvas.fig.clear()
        ax = self.sim_canvas.fig.add_subplot(111)
        
        ax.hist(resultados['volumenes'], bins=50, alpha=0.7, edgecolor='black')
        ax.axvline(resultados['p10'], color='red', linestyle='--', label='P10')
        ax.axvline(resultados['p50'], color='orange', linestyle='--', label='P50')
        ax.axvline(resultados['p90'], color='green', linestyle='--', label='P90')
        
        ax.set_xlabel('Volumen (Mbbl)')
        ax.set_ylabel('Frecuencia')
        ax.set_title('Distribución de Volúmenes - Monte Carlo')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        self.sim_canvas.draw()

class ReportesTab(QWidget):
    """Pestaña de Generación de Reportes"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Configuración del reporte
        config_group = QGroupBox("Configuración del Reporte")
        config_layout = QGridLayout()
        
        config_layout.addWidget(QLabel("Título:"), 0, 0)
        self.edit_titulo = QLineEdit("Reporte de Análisis Petrofísico")
        config_layout.addWidget(self.edit_titulo, 0, 1)
        
        config_layout.addWidget(QLabel("Autor:"), 1, 0)
        self.edit_autor = QLineEdit("PIAP-A PRO")
        config_layout.addWidget(self.edit_autor, 1, 1)
        
        config_layout.addWidget(QLabel("Compañía:"), 2, 0)
        self.edit_compania = QLineEdit("")
        config_layout.addWidget(self.edit_compania, 2, 1)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Secciones a incluir
        sections_group = QGroupBox("Secciones a Incluir")
        sections_layout = QVBoxLayout()
        
        self.cb_resumen = QCheckBox("Resumen Ejecutivo")
        self.cb_datos = QCheckBox("Datos del Pozo")
        self.cb_calculos = QCheckBox("Cálculos Petrofísicos")
        self.cb_graficos = QCheckBox("Gráficos Principales")
        self.cb_resultados = QCheckBox("Resultados y Recomendaciones")
        
        sections_layout.addWidget(self.cb_resumen)
        sections_layout.addWidget(self.cb_datos)
        sections_layout.addWidget(self.cb_calculos)
        sections_layout.addWidget(self.cb_graficos)
        sections_layout.addWidget(self.cb_resultados)
        
        sections_group.setLayout(sections_layout)
        layout.addWidget(sections_group)
        
        # Generación
        generate_group = QGroupBox("Generación de Reporte")
        generate_layout = QHBoxLayout()
        
        self.btn_generar_pdf = QPushButton("Generar PDF")
        self.btn_exportar_excel = QPushButton("Exportar a Excel")
        self.btn_imprimir = QPushButton("Imprimir")
        
        generate_layout.addWidget(self.btn_generar_pdf)
        generate_layout.addWidget(self.btn_exportar_excel)
        generate_layout.addWidget(self.btn_imprimir)
        generate_layout.addStretch()
        
        generate_group.setLayout(generate_layout)
        layout.addWidget(generate_group)
        
        # Vista previa
        self.text_preview = QTextEdit()
        self.text_preview.setPlaceholderText("Vista previa del reporte aparecerá aquí...")
        layout.addWidget(self.text_preview)
        
        self.setLayout(layout)
        
        # Conectar señales
        self.btn_generar_pdf.clicked.connect(self.generar_pdf)
        self.btn_exportar_excel.clicked.connect(self.exportar_excel)
        self.btn_imprimir.clicked.connect(self.imprimir_reporte)
    
    def generar_pdf(self):
        # En una implementación real, usaríamos ReportLab o similar
        QMessageBox.information(self, "PDF", "Funcionalidad PDF en desarrollo")
        
        # Generar vista previa
        self.generar_vista_previa()
    
    def exportar_excel(self):
        data = self.main_window.project_manager.current_data
        if data is None:
            QMessageBox.warning(self, "Error", "No hay datos para exportar")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar archivo Excel", "", "Excel (*.xlsx)"
        )
        
        if file_path:
            try:
                data.to_excel(file_path, index=False)
                QMessageBox.information(self, "Éxito", f"Datos exportados a {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo exportar: {str(e)}")
    
    def imprimir_reporte(self):
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Aquí iría la lógica de impresión
            QMessageBox.information(self, "Imprimir", "Funcionalidad de impresión en desarrollo")
    
    def generar_vista_previa(self):
        pm = self.main_window.project_manager
        well_info = pm.well_info
        data = pm.current_data
        
        if data is None:
            return
        
        # Generar reporte básico
        reporte = f"""
REPORTE DE ANÁLISIS PETROFÍSICO
================================

Título: {self.edit_titulo.text()}
Autor: {self.edit_autor.text()}
Compañía: {self.edit_compania.text()}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}

INFORMACIÓN DEL POZO
--------------------
Nombre: {well_info.get('name', 'N/A')}
Compañía: {well_info.get('company', 'N/A')}
Campo: {well_info.get('field', 'N/A')}
Profundidad: {well_info.get('start_depth', 'N/A'):.1f} - {well_info.get('end_depth', 'N/A'):.1f}

RESUMEN DE DATOS
----------------
Registros: {len(data)}
Curvas disponibles: {', '.join(data.columns)}

CÁLCULOS REALIZADOS
-------------------
"""
        
        # Agregar cálculos realizados
        calculated_curves = []
        for curve in ['VSH', 'PHI', 'SW', 'PERM']:
            if curve in data.columns:
                calculated_curves.append(curve)
        
        if calculated_curves:
            reporte += f"Parámetros calculados: {', '.join(calculated_curves)}\n"
            
            for curve in calculated_curves:
                stats = data[curve].describe()
                reporte += f"\n{curve}:\n"
                reporte += f"  Media: {stats['mean']:.4f}\n"
                reporte += f"  Mín: {stats['min']:.4f}\n"
                reporte += f"  Máx: {stats['max']:.4f}\n"
        
        reporte += "\nCONCLUSIONES Y RECOMENDACIONES\n"
        reporte += "-------------------------------\n"
        reporte += "Reporte generado automáticamente por PIAP-A PRO v4.0"
        
        self.text_preview.setPlainText(reporte)

# =============================================================================
# VENTANA PRINCIPAL - VERSIÓN CORREGIDA
# =============================================================================

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación - VERSIÓN CORREGIDA"""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar componentes del núcleo
        self.project_manager = ProjectManager()
        self.data_importer = DataImporter()
        
        # Inicializar pestañas como None primero
        self.project_tab = None
        self.import_tab = None
        self.petrofisica_tab = None
        self.visualization_tab = None
        self.geoestadistica_tab = None
        self.simulacion_tab = None
        self.reportes_tab = None
        
        # Inicializar UI
        self.initUI()
        
        # Aplicar tema oscuro
        self.apply_dark_theme()
    
    def initUI(self):
        self.setWindowTitle("PIAP-A PRO v4.0 - Plataforma Integral de Análisis Petrofísico")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # PRIMERO crear las pestañas
        self.create_tabs()
        
        # LUEGO crear la barra de herramientas
        self.create_toolbar()
        
        # Barra de estado
        self.statusBar().showMessage("Sistema PIAP-A PRO v4.0 cargado correctamente")
    
    def create_tabs(self):
        """Crear todas las pestañas primero"""
        self.tabs = QTabWidget()
        
        # Crear pestañas
        self.project_tab = ProjectTab(self)
        self.import_tab = ImportTab(self)
        self.petrofisica_tab = PetrofisicaTab(self)
        self.visualization_tab = VisualizationTab(self)
        self.geoestadistica_tab = GeoestadisticaTab(self)
        self.simulacion_tab = SimulacionTab(self)
        self.reportes_tab = ReportesTab(self)
        
        # Agregar pestañas
        self.tabs.addTab(self.project_tab, "📁 Proyectos")
        self.tabs.addTab(self.import_tab, "📊 Importación")
        self.tabs.addTab(self.petrofisica_tab, "🧮 Petrofísica")
        self.tabs.addTab(self.visualization_tab, "📈 Visualización")
        self.tabs.addTab(self.geoestadistica_tab, "🗺️ Geoestadística")
        self.tabs.addTab(self.simulacion_tab, "🔄 Simulación")
        self.tabs.addTab(self.reportes_tab, "📋 Reportes")
        
        # Agregar al layout principal
        self.centralWidget().layout().addWidget(self.tabs)
    
    def create_toolbar(self):
        """Crear barra de herramientas - VERSIÓN CORREGIDA"""
        toolbar = self.addToolBar("Principal")
        
        # Acciones principales
        new_action = QPushButton("Nuevo Proyecto")
        open_action = QPushButton("Abrir Proyecto")
        save_action = QPushButton("Guardar")
        
        toolbar.addWidget(new_action)
        toolbar.addWidget(open_action)
        toolbar.addWidget(save_action)
        toolbar.addSeparator()
        
        # Conectar señales - AHORA self.project_tab existe
        new_action.clicked.connect(self.project_tab.create_project)
        open_action.clicked.connect(self.project_tab.load_project)
        save_action.clicked.connect(self.project_tab.save_project)
        
        # Botón de ayuda
        help_action = QPushButton("Ayuda")
        help_action.clicked.connect(self.show_help)
        toolbar.addWidget(help_action)
    
    def show_help(self):
        """Mostrar ayuda básica"""
        QMessageBox.information(self, "Ayuda", 
                              "PIAP-A PRO v4.0\n\n"
                              "Flujo de trabajo recomendado:\n"
                              "1. Crear/abrir proyecto\n"
                              "2. Importar datos LAS/CSV\n"
                              "3. Realizar cálculos petrofísicos\n"
                              "4. Visualizar resultados\n"
                              "5. Generar reportes")
    
    def apply_dark_theme(self):
        """Aplica un tema oscuro a la aplicación"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #3c3c3c;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #505050;
                border-bottom: 2px solid #1e90ff;
            }
            QGroupBox {
                border: 1px solid #555555;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 3px;
                border-radius: 3px;
            }
            QTableWidget {
                background-color: #404040;
                color: #ffffff;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #505050;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #555555;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 3px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #1e90ff;
            }
        """)
    
    def notify_data_loaded(self):
        """Notifica a todas las pestañas que se han cargado nuevos datos"""
        if hasattr(self, 'petrofisica_tab') and self.petrofisica_tab:
            self.petrofisica_tab.update_curves()
        if hasattr(self, 'visualization_tab') and self.visualization_tab:
            self.visualization_tab.update_data()
        if hasattr(self, 'project_tab') and self.project_tab:
            self.project_tab.update_display()
        
        if self.project_manager.current_data is not None:
            self.statusBar().showMessage(f"Datos cargados: {len(self.project_manager.current_data)} registros")


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    app = QApplication(sys.argv)
    
    # Configurar aplicación
    app.setApplicationName("PIAP-A PRO")
    app.setApplicationVersion("4.0")
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar aplicación
    sys.exit(app.exec())

if __name__ == '__main__':
    main()