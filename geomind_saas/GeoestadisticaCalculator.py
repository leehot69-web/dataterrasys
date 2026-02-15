class GeoestadisticaCalculator:
    """Calculadora geoestadística - MÓDULO COMPLETO"""

# IMPORTACIONES FALTANTES
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
from scipy import stats
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from scipy.interpolate import Rbf
import numpy as np
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import os
from datetime import datetime


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

# =============================================================================
# WIDGETS BASE DE MATPLOTLIB
# =============================================================================

class MplCanvas(FigureCanvas):
    """Widget de Matplotlib integrado"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

# =============================================================================
# CLASES DE VISUALIZACIÓN MEJORADAS - GRÁFICOS PROFESIONALES
# =============================================================================

class InteractiveWellPlot(QWidget):
    """Widget de gráfico de pozo interactivo y profesional"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.tracks = []
        self.depth_range = [0, 1]
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Toolbar superior
        toolbar_layout = QHBoxLayout()
        
        self.btn_add_track = QPushButton("➕ Agregar Track")
        self.btn_clear = QPushButton("🗑️ Limpiar")
        self.btn_snapshot = QPushButton("📸 Captura")
        self.btn_export = QPushButton("💾 Exportar")
        
        toolbar_layout.addWidget(self.btn_add_track)
        toolbar_layout.addWidget(self.btn_clear)
        toolbar_layout.addWidget(self.btn_snapshot)
        toolbar_layout.addWidget(self.btn_export)
        toolbar_layout.addStretch()
        
        # Controles de profundidad
        toolbar_layout.addWidget(QLabel("Profundidad:"))
        self.slider_depth = QSlider(Qt.Orientation.Horizontal)
        self.slider_depth.setRange(0, 100)
        self.slider_depth.setValue(100)
        toolbar_layout.addWidget(self.slider_depth)
        
        layout.addLayout(toolbar_layout)
        
        # Área de gráfico principal
        self.figure = Figure(figsize=(12, 10), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        # Conectar señales
        self.btn_add_track.clicked.connect(self.add_default_track)
        self.btn_clear.clicked.connect(self.clear_plot)
        self.btn_snapshot.clicked.connect(self.take_snapshot)
        self.btn_export.clicked.connect(self.export_plot)
        self.slider_depth.valueChanged.connect(self.update_depth_range)
    
    def set_data(self, data):
        """Establece los datos y configura el gráfico"""
        self.data = data
        if data is not None and len(data) > 0:
            depth_col = data.columns[0]
            self.depth_range = [data[depth_col].min(), data[depth_col].max()]
            self.slider_depth.setRange(0, 100)
            self.slider_depth.setValue(100)
        self.clear_plot()
    
    def add_default_track(self):
        """Agrega un track profesional por defecto"""
        if self.data is None:
            return
        
        track_configs = [
            {'curves': ['GR'], 'color': 'green', 'xlim': (0, 150), 'title': 'Gamma Ray'},
            {'curves': ['RHOB'], 'color': 'red', 'xlim': (1.95, 2.95), 'title': 'Density'},
            {'curves': ['NPHI'], 'color': 'blue', 'xlim': (0.45, -0.15), 'title': 'Neutron'},
            {'curves': ['RT'], 'color': 'black', 'xlim': (0.2, 2000), 'title': 'Resistivity', 'scale': 'log'}
        ]
        
        for config in track_configs:
            available_curves = [c for c in config['curves'] if c in self.data.columns]
            if available_curves:
                self.add_track(available_curves[0], config)
    
    def add_track(self, curve_name, config=None):
        """Agrega un track específico"""
        if self.data is None or curve_name not in self.data.columns:
            return
        
        if config is None:
            config = {
                'color': np.random.choice(['red', 'blue', 'green', 'purple', 'orange']),
                'xlim': self.get_smart_limits(self.data[curve_name]),
                'title': curve_name,
                'scale': 'linear'
            }
        
        track = {
            'curve': curve_name,
            'config': config,
            'ax': None
        }
        
        self.tracks.append(track)
        self.update_plot()
    
    def get_smart_limits(self, data):
        """Calcula límites inteligentes para el eje X"""
        clean_data = data.dropna()
        if len(clean_data) == 0:
            return (0, 1)
        
        q1, q3 = np.percentile(clean_data, [5, 95])
        iqr = q3 - q1
        lower = max(clean_data.min(), q1 - 1.5 * iqr)
        upper = min(clean_data.max(), q3 + 1.5 * iqr)
        
        # Ajustar para evitar límites muy estrechos
        if upper - lower < 0.1 * (clean_data.max() - clean_data.min()):
            lower = clean_data.min()
            upper = clean_data.max()
        
        return (lower, upper)
    
    def update_plot(self):
        """Actualiza el gráfico completo"""
        if self.data is None or len(self.tracks) == 0:
            return
        
        self.figure.clear()
        
        # Crear grid de subplots
        n_tracks = len(self.tracks)
        gs = gridspec.GridSpec(1, n_tracks, width_ratios=[1]*n_tracks)
        
        depth_col = self.data.columns[0]
        depth_data = self.data[depth_col]
        
        # Aplicar rango de profundidad
        depth_mask = (depth_data >= self.depth_range[0]) & (depth_data <= self.depth_range[1])
        filtered_data = self.data[depth_mask]
        
        for i, track in enumerate(self.tracks):
            ax = self.figure.add_subplot(gs[i])
            track['ax'] = ax
            
            curve_data = filtered_data[track['curve']]
            config = track['config']
            
            # Graficar curva principal
            ax.plot(curve_data, filtered_data[depth_col], 
                   color=config['color'], linewidth=1, label=track['curve'])
            
            # Configurar ejes
            ax.set_xlim(config['xlim'])
            ax.set_ylim(self.depth_range[::-1])  # Invertir para profundidad
            
            if config.get('scale') == 'log':
                ax.set_xscale('log')
            
            # Solo mostrar etiqueta Y en el primer track
            if i == 0:
                ax.set_ylabel('Profundidad', fontweight='bold')
            else:
                ax.set_yticklabels([])
            
            # Título y grid
            ax.set_title(config['title'], fontweight='bold', fontsize=10)
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # Formato profesional
            ax.tick_params(axis='both', which='major', labelsize=8)
            
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_depth_range(self, value):
        """Actualiza el rango de profundidad basado en el slider"""
        if self.data is None:
            return
        
        depth_col = self.data.columns[0]
        full_range = self.data[depth_col].max() - self.data[depth_col].min()
        current_range = full_range * (value / 100)
        
        start_depth = self.data[depth_col].min()
        self.depth_range = [start_depth, start_depth + current_range]
        
        self.update_plot()
    
    def clear_plot(self):
        """Limpia todos los tracks"""
        self.tracks.clear()
        self.figure.clear()
        self.canvas.draw()
    
    def take_snapshot(self):
        """Toma una captura del gráfico actual"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar captura", "", "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)"
        )
        if file_path:
            try:
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight', 
                                  facecolor=self.figure.get_facecolor())
                QMessageBox.information(self, "Éxito", f"Captura guardada en {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar: {str(e)}")
    
    def export_plot(self):
        """Exporta datos del gráfico"""
        if self.data is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar datos", "", "CSV (*.csv);;Excel (*.xlsx)"
        )
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.data.to_csv(file_path, index=False)
                else:
                    self.data.to_excel(file_path, index=False)
                QMessageBox.information(self, "Éxito", f"Datos exportados a {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo exportar: {str(e)}")

class AdvancedCrossPlot(QWidget):
    """Crossplot avanzado con análisis estadístico"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Controles avanzados
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
        
        controls_layout.addWidget(QLabel("Tamaño por:"), 3, 0)
        self.combo_size = QComboBox()
        self.combo_size.addItem("Constante")
        controls_layout.addWidget(self.combo_size, 3, 1)
        
        # Opciones avanzadas
        self.cb_trend = QCheckBox("Línea de tendencia")
        self.cb_trend.setChecked(True)
        controls_layout.addWidget(self.cb_trend, 4, 0)
        
        self.cb_density = QCheckBox("Mapa de densidad")
        controls_layout.addWidget(self.cb_density, 4, 1)
        
        self.cb_clusters = QCheckBox("Detección de clusters")
        controls_layout.addWidget(self.cb_clusters, 5, 0)
        
        self.btn_plot = QPushButton("🔄 Generar Crossplot Avanzado")
        controls_layout.addWidget(self.btn_plot, 6, 0, 1, 2)
        
        layout.addLayout(controls_layout)
        
        # Gráfico
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        self.btn_plot.clicked.connect(self.generate_advanced_plot)
    
    def set_data(self, data):
        self.data = data
        self.combo_x.clear()
        self.combo_y.clear()
        self.combo_color.clear()
        self.combo_size.clear()
        
        if data is not None:
            columns = data.columns.tolist()
            self.combo_x.addItems(columns)
            self.combo_y.addItems(columns)
            self.combo_color.addItem("Ninguno")
            self.combo_color.addItems(columns)
            self.combo_size.addItem("Constante")
            self.combo_size.addItems(columns)
    
    def generate_advanced_plot(self):
        if self.data is None:
            return
        
        x_col = self.combo_x.currentText()
        y_col = self.combo_y.currentText()
        color_col = self.combo_color.currentText()
        size_col = self.combo_size.currentText()
        
        if not x_col or not y_col:
            return
        
        # Limpiar datos
        plot_data = self.data[[x_col, y_col]].dropna()
        if color_col != "Ninguno":
            plot_data[color_col] = self.data[color_col]
        if size_col != "Constante":
            plot_data[size_col] = self.data[size_col]
        
        if len(plot_data) < 2:
            QMessageBox.warning(self, "Error", "No hay suficientes datos para graficar")
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Configurar tamaño y color
        sizes = 20
        colors = 'blue'
        alpha = 0.6
        
        if size_col != "Constante" and size_col in plot_data.columns:
            sizes = 50 * (plot_data[size_col] - plot_data[size_col].min()) / (plot_data[size_col].max() - plot_data[size_col].min()) + 10
        
        if color_col != "Ninguno" and color_col in plot_data.columns:
            scatter = ax.scatter(plot_data[x_col], plot_data[y_col], 
                               c=plot_data[color_col], s=sizes, alpha=alpha, 
                               cmap='viridis', edgecolors='black', linewidth=0.5)
            self.figure.colorbar(scatter, ax=ax, label=color_col)
        else:
            ax.scatter(plot_data[x_col], plot_data[y_col], s=sizes, alpha=alpha, 
                      color='blue', edgecolors='black', linewidth=0.5)
        
        # Línea de tendencia
        if self.cb_trend.isChecked() and len(plot_data) > 1:
            z = np.polyfit(plot_data[x_col], plot_data[y_col], 1)
            p = np.poly1d(z)
            x_trend = np.linspace(plot_data[x_col].min(), plot_data[x_col].max(), 100)
            ax.plot(x_trend, p(x_trend), "r--", alpha=0.8, linewidth=2, label='Tendencia')
        
        # Mapa de densidad
        if self.cb_density.isChecked() and len(plot_data) > 10:
            try:
                # Calcular densidad 2D
                x = plot_data[x_col].values
                y = plot_data[y_col].values
                
                # Crear grid para densidad
                xi = np.linspace(x.min(), x.max(), 50)
                yi = np.linspace(y.min(), y.max(), 50)
                xi, yi = np.meshgrid(xi, yi)
                
                # Calcular densidad kernel
                values = np.vstack([x, y])
                kernel = stats.gaussian_kde(values)
                zi = kernel(np.vstack([xi.flatten(), yi.flatten()]))
                
                # Plot densidad
                ax.contourf(xi, yi, zi.reshape(xi.shape), alpha=0.3, cmap='Blues')
            except:
                pass
        
        # Detección de clusters
        if self.cb_clusters.isChecked() and len(plot_data) > 10:
            try:
                X = plot_data[[x_col, y_col]].values
                X_scaled = StandardScaler().fit_transform(X)
                
                clustering = DBSCAN(eps=0.5, min_samples=5).fit(X_scaled)
                labels = clustering.labels_
                
                # Plot clusters
                unique_labels = set(labels)
                colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(unique_labels))]
                
                for k, col in zip(unique_labels, colors):
                    if k == -1:
                        col = [0, 0, 0, 1]  # Ruido en negro
                    
                    class_member_mask = (labels == k)
                    xy = X[class_member_mask]
                    ax.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
                           markeredgecolor='k', markersize=8 if k == -1 else 6,
                           alpha=0.6, label=f'Cluster {k}' if k != -1 else 'Ruido')
                
                ax.legend()
            except Exception as e:
                print(f"Error en clustering: {e}")
        
        ax.set_xlabel(x_col, fontweight='bold')
        ax.set_ylabel(y_col, fontweight='bold')
        ax.set_title(f'Crossplot Avanzado: {x_col} vs {y_col}', fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Estadísticas avanzadas
        stats_text = self.calculate_advanced_stats(plot_data[x_col], plot_data[y_col])
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def calculate_advanced_stats(self, x, y):
        """Calcula estadísticas avanzadas para el crossplot"""
        correlation = x.corr(y)
        r_squared = correlation ** 2
        
        stats_text = f"""Estadísticas:
Correlación: {correlation:.3f}
R²: {r_squared:.3f}
N: {len(x)}
Media X: {x.mean():.3f}
Media Y: {y.mean():.3f}"""
        
        return stats_text

class AdvancedGeoMap(QWidget):
    """Mapa geoestadístico avanzado con 3D"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pozos = {}
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.btn_add_pozo = QPushButton("Agregar Pozo")
        self.btn_interpolate = QPushButton("Interpolar Superficie")
        self.btn_3d_view = QPushButton("Vista 3D")
        self.combo_method = QComboBox()
        self.combo_method.addItems(["Kriging", "IDW", "RBF", "Vecinos Más Cercanos"])
        
        controls_layout.addWidget(self.btn_add_pozo)
        controls_layout.addWidget(QLabel("Método:"))
        controls_layout.addWidget(self.combo_method)
        controls_layout.addWidget(self.btn_interpolate)
        controls_layout.addWidget(self.btn_3d_view)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Gráfico principal
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        # Conectar señales
        self.btn_add_pozo.clicked.connect(self.agregar_pozo_simulado)
        self.btn_interpolate.clicked.connect(self.interpolar_superficie)
        self.btn_3d_view.clicked.connect(self.mostrar_vista_3d)
    
    def agregar_pozo_simulado(self):
        """Agrega pozos simulados para demostración"""
        pozo_id = f"Pozo_{len(self.pozos) + 1}"
        
        # Generar coordenadas realistas
        x = np.random.uniform(0, 1000)
        y = np.random.uniform(0, 1000)
        
        # Generar valor de propiedad realista
        # Simular tendencia espacial
        center_x, center_y = 500, 500
        distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        valor_base = 0.2 * np.exp(-distance/500) + np.random.normal(0, 0.05)
        valor = max(0.05, min(0.35, valor_base))
        
        self.pozos[pozo_id] = {'x': x, 'y': y, 'valor': valor}
        self.actualizar_mapa()
    
    def actualizar_mapa(self):
        """Actualiza el mapa con los pozos actuales"""
        if not self.pozos:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        x = [p['x'] for p in self.pozos.values()]
        y = [p['y'] for p in self.pozos.values()]
        valores = [p['valor'] for p in self.pozos.values()]
        
        # Scatter plot de pozos
        scatter = ax.scatter(x, y, c=valores, s=100, cmap='viridis', 
                           edgecolors='black', linewidth=1.5)
        
        # Añadir etiquetas
        for i, (pozo_id, datos) in enumerate(self.pozos.items()):
            ax.annotate(pozo_id, (datos['x'], datos['y']), 
                       xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        ax.set_xlabel('Coordenada X (m)')
        ax.set_ylabel('Coordenada Y (m)')
        ax.set_title('Mapa de Pozos - Distribución Espacial')
        ax.grid(True, alpha=0.3)
        
        # Barra de color
        cbar = self.figure.colorbar(scatter, ax=ax)
        cbar.set_label('Valor de Propiedad')
        
        self.canvas.draw()
    
    def interpolar_superficie(self):
        """Interpola superficie usando el método seleccionado"""
        if len(self.pozos) < 3:
            QMessageBox.warning(self, "Error", "Se necesitan al menos 3 pozos para interpolar")
            return
        
        x_known = np.array([p['x'] for p in self.pozos.values()])
        y_known = np.array([p['y'] for p in self.pozos.values()])
        z_known = np.array([p['valor'] for p in self.pozos.values()])
        
        # Crear grid
        xi = np.linspace(min(x_known) - 100, max(x_known) + 100, 100)
        yi = np.linspace(min(y_known) - 100, max(y_known) + 100, 100)
        XI, YI = np.meshgrid(xi, yi)
        
        method = self.combo_method.currentText()
        
        try:
            if method == "Kriging":
                ZI = self.kriging_interpolation(x_known, y_known, z_known, XI, YI)
            elif method == "IDW":
                ZI = self.idw_interpolation(x_known, y_known, z_known, XI, YI)
            elif method == "RBF":
                ZI = self.rbf_interpolation(x_known, y_known, z_known, XI, YI)
            else:  # Vecinos más cercanos
                ZI = self.nearest_interpolation(x_known, y_known, z_known, XI, YI)
            
            self.mostrar_superficie_interpolada(XI, YI, ZI, x_known, y_known, z_known, method)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en interpolación: {str(e)}")
    
    def kriging_interpolation(self, x, y, z, xi, yi):
        """Interpolación por Kriging ordinario"""
        # Implementación simplificada de Kriging
        zi = np.zeros(xi.shape)
        
        for i in range(xi.shape[0]):
            for j in range(xi.shape[1]):
                distances = np.sqrt((x - xi[i,j])**2 + (y - yi[i,j])**2)
                weights = 1 / (distances + 1e-8)**2
                weights = weights / np.sum(weights)
                zi[i,j] = np.sum(weights * z)
        
        return zi
    
    def idw_interpolation(self, x, y, z, xi, yi, power=2):
        """Inverse Distance Weighting interpolation"""
        zi = np.zeros(xi.shape)
        
        for i in range(xi.shape[0]):
            for j in range(xi.shape[1]):
                distances = np.sqrt((x - xi[i,j])**2 + (y - yi[i,j])**2)
                weights = 1 / (distances + 1e-8)**power
                weights = weights / np.sum(weights)
                zi[i,j] = np.sum(weights * z)
        
        return zi
    
    def rbf_interpolation(self, x, y, z, xi, yi):
        """Radial Basis Function interpolation"""
        rbf = Rbf(x, y, z, function='multiquadric')
        return rbf(xi, yi)
    
    def nearest_interpolation(self, x, y, z, xi, yi):
        """Interpolación por vecino más cercano"""
        points = np.column_stack((x, y))
        return griddata(points, z, (xi, yi), method='nearest')
    
    def mostrar_superficie_interpolada(self, XI, YI, ZI, x_known, y_known, z_known, method):
        """Muestra la superficie interpolada"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Contour plot
        contour = ax.contourf(XI, YI, ZI, levels=20, alpha=0.7, cmap='viridis')
        
        # Líneas de contorno
        ax.contour(XI, YI, ZI, levels=10, colors='black', alpha=0.3, linewidths=0.5)
        
        # Pozos originales
        scatter = ax.scatter(x_known, y_known, c=z_known, s=100, 
                           edgecolors='black', linewidth=1.5, cmap='viridis')
        
        ax.set_xlabel('Coordenada X (m)')
        ax.set_ylabel('Coordenada Y (m)')
        ax.set_title(f'Superficie Interpolada - {method}')
        ax.grid(True, alpha=0.3)
        
        # Barra de color
        cbar = self.figure.colorbar(contour, ax=ax)
        cbar.set_label('Valor de Propiedad')
        
        self.canvas.draw()
    
    def mostrar_vista_3d(self):
        """Muestra vista 3D de la superficie"""
        if len(self.pozos) < 3:
            QMessageBox.warning(self, "Error", "Se necesitan al menos 3 pozos para 3D")
            return
        
        # Crear datos interpolados para 3D
        x_known = np.array([p['x'] for p in self.pozos.values()])
        y_known = np.array([p['y'] for p in self.pozos.values()])
        z_known = np.array([p['valor'] for p in self.pozos.values()])
        
        xi = np.linspace(min(x_known) - 100, max(x_known) + 100, 50)
        yi = np.linspace(min(y_known) - 100, max(y_known) + 100, 50)
        XI, YI = np.meshgrid(xi, yi)
        ZI = self.idw_interpolation(x_known, y_known, z_known, XI, YI)
        
        # Crear figura 3D
        fig_3d = plt.figure(figsize=(10, 8))
        ax_3d = fig_3d.add_subplot(111, projection='3d')
        
        # Surface plot
        surf = ax_3d.plot_surface(XI, YI, ZI, cmap='viridis', alpha=0.8, 
                                 linewidth=0, antialiased=True)
        
        # Scatter de pozos
        ax_3d.scatter(x_known, y_known, z_known, c='red', s=50, 
                     edgecolors='black', depthshade=True)
        
        ax_3d.set_xlabel('X (m)')
        ax_3d.set_ylabel('Y (m)')
        ax_3d.set_zlabel('Valor')
        ax_3d.set_title('Vista 3D - Distribución Espacial')
        
        # Barra de color
        fig_3d.colorbar(surf, ax=ax_3d, shrink=0.5, aspect=5)
        
        plt.tight_layout()
        plt.show()

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

class EnhancedVisualizationTab(QWidget):
    """Pestaña de visualización mejorada con gráficos profesionales"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Tabs de visualización mejorada
        self.viz_tabs = QTabWidget()
        
        # Sub-pestaña: Tracks de pozo avanzados
        self.well_plot_tab = InteractiveWellPlot()
        self.viz_tabs.addTab(self.well_plot_tab, "🎯 Tracks de Pozo Avanzados")
        
        # Sub-pestaña: Crossplots avanzados
        self.crossplot_tab = AdvancedCrossPlot()
        self.viz_tabs.addTab(self.crossplot_tab, "📊 Crossplots Avanzados")
        
        # Sub-pestaña: Mapas geoestadísticos
        self.geomap_tab = AdvancedGeoMap()
        self.viz_tabs.addTab(self.geomap_tab, "🗺️ Mapas Geoestadísticos")
        
        # Sub-pestaña: Histogramas avanzados
        self.histogram_tab = self.create_advanced_histogram_tab()
        self.viz_tabs.addTab(self.histogram_tab, "📈 Histogramas Avanzados")
        
        layout.addWidget(self.viz_tabs)
        self.setLayout(layout)
    
    def create_advanced_histogram_tab(self):
        """Crea pestaña de histogramas avanzados"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.combo_hist_curve = QComboBox()
        self.btn_histogram = QPushButton("🔄 Generar Histograma Avanzado")
        self.cb_cumulative = QCheckBox("Acumulativo")
        self.cb_density = QCheckBox("Densidad")
        self.cb_fit = QCheckBox("Ajuste Distribución")
        
        controls_layout.addWidget(QLabel("Curva:"))
        controls_layout.addWidget(self.combo_hist_curve)
        controls_layout.addWidget(self.btn_histogram)
        controls_layout.addWidget(self.cb_cumulative)
        controls_layout.addWidget(self.cb_density)
        controls_layout.addWidget(self.cb_fit)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Gráfico
        self.hist_figure = Figure(figsize=(10, 8))
        self.hist_canvas = FigureCanvas(self.hist_figure)
        self.hist_toolbar = NavigationToolbar(self.hist_canvas, self)
        
        layout.addWidget(self.hist_toolbar)
        layout.addWidget(self.hist_canvas)
        
        widget.setLayout(layout)
        
        self.btn_histogram.clicked.connect(self.generate_advanced_histogram)
        
        return widget
    
    def update_data(self):
        """Actualiza todos los widgets con los datos actuales"""
        data = self.main_window.project_manager.current_data
        if data is not None:
            self.well_plot_tab.set_data(data)
            self.crossplot_tab.set_data(data)
            
            # Actualizar combos
            self.combo_hist_curve.clear()
            self.combo_hist_curve.addItems(data.columns)
    
    def generate_advanced_histogram(self):
        """Genera histograma avanzado con múltiples opciones"""
        data = self.main_window.project_manager.current_data
        if data is None:
            return
        
        curve = self.combo_hist_curve.currentText()
        if not curve:
            return
        
        curve_data = data[curve].dropna()
        if len(curve_data) == 0:
            return
        
        self.hist_figure.clear()
        ax = self.hist_figure.add_subplot(111)
        
        # Configurar histograma basado en opciones
        hist_kwargs = {
            'bins': 30,
            'alpha': 0.7,
            'edgecolor': 'black',
            'density': self.cb_density.isChecked()
        }
        
        if self.cb_cumulative.isChecked():
            hist_kwargs['cumulative'] = True
        
        n, bins, patches = ax.hist(curve_data, **hist_kwargs)
        
        # Ajuste de distribución
        if self.cb_fit.isChecked() and len(curve_data) > 10:
            try:
                # Ajustar distribución normal
                mu, sigma = stats.norm.fit(curve_data)
                x = np.linspace(curve_data.min(), curve_data.max(), 100)
                y = stats.norm.pdf(x, mu, sigma)
                
                if self.cb_density.isChecked():
                    ax.plot(x, y, 'r-', linewidth=2, label='Distribución Normal')
                else:
                    # Escalar para que coincida con el histograma
                    y = y * len(curve_data) * (bins[1] - bins[0])
                    ax.plot(x, y, 'r-', linewidth=2, label='Distribución Normal')
                
                ax.legend()
            except:
                pass
        
        ax.set_xlabel(curve, fontweight='bold')
        ylabel = 'Densidad' if self.cb_density.isChecked() else 'Frecuencia'
        if self.cb_cumulative.isChecked():
            ylabel = 'Frecuencia Acumulada'
        ax.set_ylabel(ylabel, fontweight='bold')
        
        title = f'Histograma de {curve}'
        if self.cb_cumulative.isChecked():
            title += ' (Acumulativo)'
        if self.cb_density.isChecked():
            title += ' - Densidad'
        
        ax.set_title(title, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Estadísticas avanzadas
        stats_text = self.calculate_histogram_stats(curve_data)
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        self.hist_figure.tight_layout()
        self.hist_canvas.draw()
    
    def calculate_histogram_stats(self, data):
        """Calcula estadísticas avanzadas para el histograma"""
        stats_text = f"""Estadísticas:
N: {len(data)}
Media: {data.mean():.3f}
Mediana: {data.median():.3f}
Desv. Est.: {data.std():.3f}
Mín: {data.min():.3f}
Máx: {data.max():.3f}
Asimetría: {data.skew():.3f}
Curtosis: {data.kurtosis():.3f}"""
        
        return stats_text

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
        self.visualization_tab = EnhancedVisualizationTab(self)
        self.geoestadistica_tab = GeoestadisticaTab(self)
        self.simulacion_tab = SimulacionTab(self)
        self.reportes_tab = ReportesTab(self)
        
        # Agregar pestañas
        self.tabs.addTab(self.project_tab, "📁 Proyectos")
        self.tabs.addTab(self.import_tab, "📊 Importación")
        self.tabs.addTab(self.petrofisica_tab, "🧮 Petrofísica")
        self.tabs.addTab(self.visualization_tab, "📈 Visualización Avanzada")
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