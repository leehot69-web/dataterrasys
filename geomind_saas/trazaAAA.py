import sys
import os
import struct
import numpy as np
import sqlite3
import json
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QSlider, QComboBox, 
                             QFileDialog, QMessageBox, QProgressBar, QListWidget,
                             QSplitter, QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
import pyqtgraph as pg
from pyqtgraph import GraphicsLayoutWidget

class CustomSegyParser:
    """Parser SEG-Y personalizado y robusto"""
    
    @staticmethod
    def ibm_to_ieee(ibm_bytes):
        """Convertir formato IBM float32 a IEEE float32"""
        if len(ibm_bytes) != 4:
            return 0.0
            
        ibm = struct.unpack('>I', ibm_bytes)[0]
        
        if ibm == 0:
            return 0.0
            
        sign = (ibm >> 31) & 0x01
        exponent = (ibm >> 24) & 0x7F
        mantissa = ibm & 0x00FFFFFF
        
        # Convertir IBM a IEEE
        ieee_float = (mantissa / 16777216.0) * (16.0 ** (exponent - 64))
        
        if sign:
            ieee_float = -ieee_float
            
        return ieee_float
    
    @staticmethod
    def parse_text_header(header_bytes):
        """Parsear cabecera textual de manera robusta"""
        try:
            # Intentar decodificar como EBCDIC primero
            text = header_bytes.decode('cp500', errors='ignore')
        except:
            try:
                # Intentar como ASCII
                text = header_bytes.decode('ascii', errors='ignore')
            except:
                text = "Cabecera no legible"
        
        # Limpiar caracteres no imprimibles
        text = ''.join(char if 32 <= ord(char) <= 126 else ' ' for char in text)
        return text
    
    @staticmethod
    def parse_binary_header(header_bytes):
        """Parsear cabecera binaria"""
        header = {}
        try:
            # Leer campos principales de la cabecera binaria
            header['job_id'] = struct.unpack('>I', header_bytes[0:4])[0]
            header['line_number'] = struct.unpack('>I', header_bytes[4:8])[0]
            header['reel_number'] = struct.unpack('>I', header_bytes[8:12])[0]
            header['traces_per_ensemble'] = struct.unpack('>H', header_bytes[12:14])[0]
            header['auxiliary_traces'] = struct.unpack('>H', header_bytes[14:16])[0]
            header['sample_interval'] = struct.unpack('>H', header_bytes[16:18])[0]  # microsegundos
            header['samples_per_trace'] = struct.unpack('>H', header_bytes[20:22])[0]
            header['data_format'] = struct.unpack('>H', header_bytes[24:26])[0]
            header['ensemble_fold'] = struct.unpack('>H', header_bytes[26:28])[0]
        except Exception as e:
            print(f"Advertencia: Error parseando cabecera binaria: {e}")
        
        return header
    
    @staticmethod
    def parse_trace_header(header_bytes):
        """Parsear cabecera de traza"""
        header = {}
        try:
            header['trace_sequence'] = struct.unpack('>I', header_bytes[0:4])[0]
            header['ensemble_number'] = struct.unpack('>I', header_bytes[8:12])[0]
            header['trace_number'] = struct.unpack('>I', header_bytes[12:16])[0]
            header['coordinate_x'] = struct.unpack('>I', header_bytes[72:76])[0]
            header['coordinate_y'] = struct.unpack('>I', header_bytes[76:80])[0]
        except:
            pass
        return header

class SegyLoaderThread(QThread):
    """Hilo para cargar archivos SEG-Y sin bloquear la interfaz"""
    progress_updated = pyqtSignal(int)
    loading_finished = pyqtSignal(object, object, dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
    
    def read_trace_data(self, file, format_code, samples_per_trace, trace_size):
        """Leer datos de traza según el formato"""
        trace_data = []
        
        if format_code == 1:  # IBM float32
            for i in range(samples_per_trace):
                ibm_bytes = file.read(4)
                if len(ibm_bytes) == 4:
                    trace_data.append(CustomSegyParser.ibm_to_ieee(ibm_bytes))
                else:
                    trace_data.append(0.0)
        
        elif format_code == 5:  # IEEE float32
            for i in range(samples_per_trace):
                ieee_bytes = file.read(4)
                if len(ieee_bytes) == 4:
                    trace_data.append(struct.unpack('>f', ieee_bytes)[0])
                else:
                    trace_data.append(0.0)
        
        else:  # Para otros formatos, leer como integers de 4 bytes
            for i in range(samples_per_trace):
                int_bytes = file.read(4)
                if len(int_bytes) == 4:
                    trace_data.append(struct.unpack('>i', int_bytes)[0])
                else:
                    trace_data.append(0)
        
        return trace_data
    
    def run(self):
        try:
            self.progress_updated.emit(10)
            
            file_size = os.path.getsize(self.filename)
            traces = []
            samples = []
            metadata = {}
            
            with open(self.filename, 'rb') as file:
                # Leer cabecera textual (3200 bytes)
                text_header_bytes = file.read(3200)
                text_header = CustomSegyParser.parse_text_header(text_header_bytes)
                
                self.progress_updated.emit(20)
                
                # Leer cabecera binaria (400 bytes)
                binary_header_bytes = file.read(400)
                binary_header = CustomSegyParser.parse_binary_header(binary_header_bytes)
                
                self.progress_updated.emit(30)
                
                # Extraer información crítica
                sample_interval = binary_header.get('sample_interval', 4000)  # microsegundos
                samples_per_trace = binary_header.get('samples_per_trace', 1000)
                data_format = binary_header.get('data_format', 5)  # Por defecto IEEE float
                
                # Calcular número de trazas
                header_trace_size = 240  # bytes
                data_trace_size = samples_per_trace * 4  # 4 bytes por muestra
                total_trace_size = header_trace_size + data_trace_size
                
                remaining_bytes = file_size - 3600  # Restar cabeceras
                trace_count = remaining_bytes // total_trace_size
                
                metadata = {
                    'filename': os.path.basename(self.filename),
                    'sample_count': samples_per_trace,
                    'trace_count': trace_count,
                    'sample_interval': sample_interval / 1000.0,  # convertir a ms
                    'format': data_format,
                    'samples_per_trace': samples_per_trace,
                    'file_size': file_size
                }
                
                self.progress_updated.emit(40)
                
                # Generar array de samples (tiempos)
                samples = np.arange(samples_per_trace) * (sample_interval / 1000.0)
                
                # Leer trazas
                file.seek(3600)  # Ir al inicio de las trazas
                
                for trace_idx in range(trace_count):
                    # Leer cabecera de traza
                    trace_header_bytes = file.read(240)
                    
                    # Leer datos de la traza
                    trace_data = self.read_trace_data(file, data_format, samples_per_trace, data_trace_size)
                    traces.append(trace_data)
                    
                    if trace_idx % 100 == 0:
                        progress = 40 + int(50 * trace_idx / trace_count)
                        self.progress_updated.emit(progress)
                    
                    # Salir si llegamos al final del archivo
                    if file.tell() >= file_size:
                        break
                
                self.progress_updated.emit(95)
                
                # Convertir a numpy array y transponer para visualización
                if traces:
                    seismic_data = np.array(traces).T
                else:
                    seismic_data = np.array([])
                
                self.progress_updated.emit(100)
                self.loading_finished.emit(seismic_data, samples, metadata)
                
        except Exception as e:
            self.error_occurred.emit(f"Error al cargar archivo SEG-Y: {str(e)}")

class GeminiAnalysisThread(QThread):
    """Hilo para análisis con Gemini AI"""
    analysis_finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, image_data, analysis_type, structural_data=None, well_path=None):
        super().__init__()
        self.image_data = image_data
        self.analysis_type = analysis_type
        self.structural_data = structural_data
        self.well_path = well_path
    
    def run(self):
        try:
            # Configurar API key (debes configurar tu propia API key)
            # genai.configure(api_key="TU_API_KEY_AQUI")
            
            # Para este ejemplo, simulamos la respuesta de Gemini
            # En una implementación real, aquí iría la llamada a la API
            
            if self.analysis_type == "structural":
                # Simular análisis estructural
                result = {
                    'faults': [
                        {'x1': 50, 'y1': 100, 'x2': 150, 'y2': 300, 'confidence': 0.87},
                        {'x1': 200, 'y1': 50, 'x2': 250, 'y2': 350, 'confidence': 0.92}
                    ],
                    'horizons': [
                        {'points': [(0, 150), (100, 160), (200, 155), (300, 170)], 'confidence': 0.85},
                        {'points': [(0, 250), (100, 240), (200, 260), (300, 255)], 'confidence': 0.78}
                    ]
                }
            else:  # well_path_analysis
                # Simular análisis de trayectoria de pozo
                result = {
                    'risks': [
                        {'position': (120, 180), 'type': 'Fault Crossing', 'severity': 'High', 'confidence': 0.89},
                        {'position': (220, 280), 'type': 'Amplitude Anomaly', 'severity': 'Medium', 'confidence': 0.76}
                    ],
                    'recommendations': [
                        "Consider adjusting well path to avoid fault crossing at ~120 traces",
                        "High amplitude zone at ~220 traces may indicate hydrocarbon presence"
                    ]
                }
            
            self.analysis_finished.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(f"Error en análisis Gemini: {str(e)}")

class SeismicViewer(pg.PlotWidget):
    """Widget para visualización sísmica interactiva"""
    def __init__(self):
        super().__init__()
        self.setBackground('w')
        self.seismic_data = None
        self.samples = None
        self.metadata = None
        self.current_traces = None
        self.visible_traces = None
        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Configurar la vista
        self.getPlotItem().showGrid(True, True, 0.7)
        self.getPlotItem().setLabel('left', 'Tiempo', 'ms')
        self.getPlotItem().setLabel('bottom', 'Traces')
        
        # Para interacción
        self.drag_start = None
        self.setMouseEnabled(True, True)
        self.setAcceptDrops(True)
        
        # Elementos de visualización
        self.seismic_image = None
        self.fault_items = []
        self.horizon_items = []
        self.well_path_item = None
        self.risk_items = []
    
    def load_data(self, seismic_data, samples, metadata):
        """Cargar datos sísmicos"""
        self.seismic_data = seismic_data
        self.samples = samples
        self.metadata = metadata
        
        if seismic_data.size > 0:
            self.current_traces = np.arange(metadata['trace_count'])
            self.visible_traces = self.current_traces
            self.update_display()
        else:
            print("Advertencia: No hay datos sísmicos para mostrar")
    
    def update_display(self):
        """Actualizar visualización"""
        self.clear()
        
        if self.seismic_data is None or self.seismic_data.size == 0:
            return
        
        # Calcular rango visible
        start_trace = int(self.offset_x)
        visible_trace_count = int(self.metadata['trace_count'] / self.zoom_level)
        end_trace = min(int(self.offset_x + visible_trace_count), 
                       self.metadata['trace_count'])
        
        if start_trace >= end_trace:
            return
            
        visible_data = self.seismic_data[:, start_trace:end_trace]
        
        # Normalizar para visualización
        if visible_data.size > 0:
            data_min = np.min(visible_data)
            data_max = np.max(visible_data)
            
            if data_max != data_min:
                normalized_data = (visible_data - data_min) / (data_max - data_min)
            else:
                normalized_data = np.zeros_like(visible_data)
            
            # Crear imagen (rotar para visualización convencional)
            img_data = (normalized_data * 255).astype(np.uint8)
            height, width = img_data.shape
            
            # Crear imagen en PyQtGraph
            self.seismic_image = pg.ImageItem(image=img_data.T)
            self.addItem(self.seismic_image)
            
            # Ajustar rango de la vista
            self.setRange(xRange=[0, width], yRange=[0, height], padding=0)
    
    def wheelEvent(self, event):
        """Manejar zoom con rueda del ratón"""
        zoom_factor = 1.1
        if event.angleDelta().y() > 0:
            self.zoom_level *= zoom_factor
        else:
            self.zoom_level /= zoom_factor
        
        self.zoom_level = max(0.1, min(10.0, self.zoom_level))
        self.update_display()
        event.accept()
    
    def mousePressEvent(self, event):
        """Iniciar arrastre"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Manejar paneo"""
        if self.drag_start is not None and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.pos() - self.drag_start
            self.offset_x -= delta.x() * 0.1
            self.offset_y -= delta.y() * 0.1
            
            # Limitar offsets
            if self.metadata and self.seismic_data is not None:
                max_offset_x = max(0, self.metadata['trace_count'] - self.metadata['trace_count'] / self.zoom_level)
                self.offset_x = max(0, min(max_offset_x, self.offset_x))
                
                max_offset_y = max(0, self.metadata['sample_count'] - self.metadata['sample_count'] / self.zoom_level)
                self.offset_y = max(0, min(max_offset_y, self.offset_y))
            
            self.drag_start = event.pos()
            self.update_display()
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Finalizar arrastre"""
        self.drag_start = None
        super().mouseReleaseEvent(event)
    
    def add_faults(self, faults):
        """Añadir fallas detectadas"""
        self.clear_interpretation()
        
        for fault in faults:
            x1, y1 = fault['x1'], fault['y1']
            x2, y2 = fault['x2'], fault['y2']
            
            # Crear línea de falla
            fault_line = pg.PlotDataItem([x1, x2], [y1, y2], pen=pg.mkPen('r', width=2))
            self.addItem(fault_line)
            self.fault_items.append(fault_line)
    
    def add_horizons(self, horizons):
        """Añadir horizontes detectados"""
        for horizon in horizons:
            points = horizon['points']
            if len(points) > 1:
                x_vals = [p[0] for p in points]
                y_vals = [p[1] for p in points]
                
                horizon_line = pg.PlotDataItem(x_vals, y_vals, pen=pg.mkPen('g', width=2))
                self.addItem(horizon_line)
                self.horizon_items.append(horizon_line)
    
    def add_well_path(self, points):
        """Añadir trayectoria de pozo"""
        if self.well_path_item:
            self.removeItem(self.well_path_item)
        
        x_vals = [p[0] for p in points]
        y_vals = [p[1] for p in points]
        
        self.well_path_item = pg.PlotDataItem(x_vals, y_vals, pen=pg.mkPen('b', width=3))
        self.addItem(self.well_path_item)
    
    def add_risks(self, risks):
        """Añadir marcadores de riesgo"""
        for risk in risks:
            x, y = risk['position']
            
            # Crear marcador circular
            risk_marker = pg.ScatterPlotItem([x], [y], pen='r', brush='r', size=10, symbol='o')
            self.addItem(risk_marker)
            self.risk_items.append(risk_marker)
    
    def clear_interpretation(self):
        """Limpiar interpretación actual"""
        for item in self.fault_items + self.horizon_items + self.risk_items:
            self.removeItem(item)
        
        self.fault_items.clear()
        self.horizon_items.clear()
        self.risk_items.clear()
        
        if self.well_path_item:
            self.removeItem(self.well_path_item)
            self.well_path_item = None

class DatabaseManager:
    """Gestor de base de datos local para historial"""
    def __init__(self):
        self.db_path = "traza_segy_history.db"
        self.init_database()
    
    def init_database(self):
        """Inicializar base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                sample_count INTEGER,
                trace_count INTEGER,
                sample_interval REAL,
                load_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                analysis_type TEXT,
                results_json TEXT,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES file_history (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_file_to_history(self, filename, filepath, metadata):
        """Añadir archivo al historial"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO file_history 
            (filename, filepath, sample_count, trace_count, sample_interval)
            VALUES (?, ?, ?, ?, ?)
        ''', (filename, filepath, metadata['sample_count'], 
              metadata['trace_count'], metadata['sample_interval']))
        
        conn.commit()
        conn.close()
    
    def get_file_history(self):
        """Obtener historial de archivos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, filepath, sample_count, trace_count, 
                   sample_interval, load_date 
            FROM file_history 
            ORDER BY load_date DESC
        ''')
        
        history = cursor.fetchall()
        conn.close()
        return history

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""
    def __init__(self):
        super().__init__()
        self.seismic_data = None
        self.samples = None
        self.metadata = None
        self.db_manager = DatabaseManager()
        self.current_filepath = None
        
        self.init_ui()
        self.load_file_history()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle("TRAZA SEG-Y - Visualizador Sísmico")
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Panel izquierdo (controles)
        left_panel = self.create_left_panel()
        left_panel.setMaximumWidth(300)
        
        # Área de visualización principal
        right_panel = self.create_right_panel()
        
        # Splitter para redimensionar
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 1100])
        
        main_layout.addWidget(splitter)
    
    def create_left_panel(self):
        """Crear panel de controles izquierdo"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Grupo de carga de archivos
        file_group = QGroupBox("Carga de Archivos")
        file_layout = QVBoxLayout(file_group)
        
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.load_from_history)
        file_layout.addWidget(QLabel("Historial:"))
        file_layout.addWidget(self.history_list)
        
        self.load_btn = QPushButton("Cargar Nuevo Archivo SEG-Y")
        self.load_btn.clicked.connect(self.load_segy_file)
        file_layout.addWidget(self.load_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        file_layout.addWidget(self.progress_bar)
        
        layout.addWidget(file_group)
        
        # Grupo de visualización
        vis_group = QGroupBox("Visualización")
        vis_layout = QVBoxLayout(vis_group)
        
        vis_layout.addWidget(QLabel("Modo de Visualización:"))
        self.vis_mode = QComboBox()
        self.vis_mode.addItems(["Imagen", "Wiggle"])
        vis_layout.addWidget(self.vis_mode)
        
        vis_layout.addWidget(QLabel("Ganancia:"))
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(1, 100)
        self.gain_slider.setValue(50)
        vis_layout.addWidget(self.gain_slider)
        
        layout.addWidget(vis_group)
        
        # Grupo de Análisis IA
        ai_group = QGroupBox("Análisis con IA (Gemini)")
        ai_layout = QVBoxLayout(ai_group)
        
        self.structural_btn = QPushButton("Interpretación Estructural")
        self.structural_btn.clicked.connect(self.run_structural_analysis)
        self.structural_btn.setEnabled(False)
        ai_layout.addWidget(self.structural_btn)
        
        self.well_path_btn = QPushButton("Análisis Trayectoria Pozo")
        self.well_path_btn.clicked.connect(self.run_well_path_analysis)
        self.well_path_btn.setEnabled(False)
        ai_layout.addWidget(self.well_path_btn)
        
        layout.addWidget(ai_group)
        
        # Información del archivo
        info_group = QGroupBox("Información del Archivo")
        info_layout = QVBoxLayout(info_group)
        
        self.info_label = QLabel("No hay archivo cargado")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        return panel
    
    def create_right_panel(self):
        """Crear panel de visualización derecho"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Visualizador sísmico principal
        self.seismic_viewer = SeismicViewer()
        layout.addWidget(self.seismic_viewer)
        
        # Controles de navegación
        nav_layout = QHBoxLayout()
        
        self.zoom_in_btn = QPushButton("Zoom +")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        nav_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = QPushButton("Zoom -")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        nav_layout.addWidget(self.zoom_out_btn)
        
        self.reset_view_btn = QPushButton("Vista Completa")
        self.reset_view_btn.clicked.connect(self.reset_view)
        nav_layout.addWidget(self.reset_view_btn)
        
        nav_layout.addStretch()
        
        self.clear_interpretation_btn = QPushButton("Limpiar Interpretación")
        self.clear_interpretation_btn.clicked.connect(self.clear_interpretation)
        self.clear_interpretation_btn.setEnabled(False)
        nav_layout.addWidget(self.clear_interpretation_btn)
        
        layout.addLayout(nav_layout)
        
        return panel
    
    def load_file_history(self):
        """Cargar historial de archivos"""
        self.history_list.clear()
        history = self.db_manager.get_file_history()
        
        for item in history:
            file_id, filename, filepath, sample_count, trace_count, interval, date = item
            display_text = f"{filename}\nTraces: {trace_count}, Samples: {sample_count}"
            self.history_list.addItem(display_text)
            self.history_list.item(self.history_list.count()-1).setData(Qt.ItemDataRole.UserRole, filepath)
    
    def load_segy_file(self):
        """Cargar archivo SEG-Y"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo SEG-Y", "", "SEG-Y Files (*.sgy *.segy *.sgys)"
        )
        
        if filename:
            self.load_file(filename)
    
    def load_from_history(self, item):
        """Cargar archivo desde historial"""
        filepath = item.data(Qt.ItemDataRole.UserRole)
        if os.path.exists(filepath):
            self.load_file(filepath)
        else:
            QMessageBox.warning(self, "Error", "El archivo ya no existe en la ubicación guardada.")
    
    def load_file(self, filename):
        """Cargar archivo específico"""
        self.progress_bar.setVisible(True)
        self.load_btn.setEnabled(False)
        self.current_filepath = filename
        
        # Ejecutar carga en hilo separado
        self.loader_thread = SegyLoaderThread(filename)
        self.loader_thread.progress_updated.connect(self.progress_bar.setValue)
        self.loader_thread.loading_finished.connect(self.on_loading_finished)
        self.loader_thread.error_occurred.connect(self.on_loading_error)
        self.loader_thread.start()
    
    def on_loading_finished(self, seismic_data, samples, metadata):
        """Manejar finalización de carga"""
        self.seismic_data = seismic_data
        self.samples = samples
        self.metadata = metadata
        
        self.seismic_viewer.load_data(seismic_data, samples, metadata)
        
        # Actualizar información del archivo
        info_text = f"""
        <b>Archivo:</b> {metadata['filename']}<br>
        <b>Traces:</b> {metadata['trace_count']}<br>
        <b>Samples:</b> {metadata['sample_count']}<br>
        <b>Intervalo de Muestreo:</b> {metadata['sample_interval']} ms<br>
        <b>Formato:</b> {metadata['format']}<br>
        <b>Tamaño:</b> {metadata['file_size'] / (1024*1024):.2f} MB
        """
        self.info_label.setText(info_text)
        
        # Habilitar controles
        self.structural_btn.setEnabled(True)
        self.well_path_btn.setEnabled(True)
        self.clear_interpretation_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.load_btn.setEnabled(True)
        
        # Guardar en historial
        self.db_manager.add_file_to_history(
            metadata['filename'], 
            self.current_filepath, 
            metadata
        )
        self.load_file_history()
    
    def on_loading_error(self, error_message):
        """Manejar error de carga"""
        QMessageBox.critical(self, "Error de Carga", error_message)
        self.progress_bar.setVisible(False)
        self.load_btn.setEnabled(True)
    
    def run_structural_analysis(self):
        """Ejecutar análisis estructural con Gemini"""
        if self.seismic_data is None:
            return
        
        # Simular captura del canvas
        image_data = "simulated_canvas_data"
        
        self.analysis_thread = GeminiAnalysisThread(image_data, "structural")
        self.analysis_thread.analysis_finished.connect(self.on_structural_analysis_finished)
        self.analysis_thread.error_occurred.connect(self.on_analysis_error)
        self.analysis_thread.start()
        
        QMessageBox.information(self, "Análisis en Progreso", 
                               "El análisis estructural con Gemini está en progreso...")
    
    def run_well_path_analysis(self):
        """Ejecutar análisis de trayectoria de pozo con Gemini"""
        if self.seismic_data is None:
            return
        
        # Simular trayectoria de pozo
        well_path = [(50, 100), (150, 200), (250, 300)]
        self.seismic_viewer.add_well_path(well_path)
        
        image_data = "simulated_canvas_data_with_well_path"
        
        self.analysis_thread = GeminiAnalysisThread(
            image_data, "well_path_analysis", 
            well_path=well_path
        )
        self.analysis_thread.analysis_finished.connect(self.on_well_path_analysis_finished)
        self.analysis_thread.error_occurred.connect(self.on_analysis_error)
        self.analysis_thread.start()
        
        QMessageBox.information(self, "Análisis en Progreso", 
                               "El análisis de trayectoria de pozo con Gemini está en progreso...")
    
    def on_structural_analysis_finished(self, results):
        """Manejar resultados del análisis estructural"""
        self.seismic_viewer.add_faults(results['faults'])
        self.seismic_viewer.add_horizons(results['horizons'])
        
        QMessageBox.information(self, "Análisis Completado", 
                               f"Se detectaron {len(results['faults'])} fallas y {len(results['horizons'])} horizontes.")
    
    def on_well_path_analysis_finished(self, results):
        """Manejar resultados del análisis de trayectoria de pozo"""
        self.seismic_viewer.add_risks(results['risks'])
        
        message = "Análisis de riesgo completado:\n\n"
        for risk in results['risks']:
            message += f"- {risk['type']} (Severidad: {risk['severity']})\n"
        
        message += "\nRecomendaciones:\n"
        for rec in results['recommendations']:
            message += f"- {rec}\n"
        
        QMessageBox.information(self, "Análisis de Trayectoria", message)
    
    def on_analysis_error(self, error_message):
        """Manejar error de análisis"""
        QMessageBox.critical(self, "Error de Análisis", error_message)
    
    def zoom_in(self):
        """Aumentar zoom"""
        self.seismic_viewer.zoom_level *= 1.2
        self.seismic_viewer.zoom_level = min(10.0, self.seismic_viewer.zoom_level)
        self.seismic_viewer.update_display()
    
    def zoom_out(self):
        """Disminuir zoom"""
        self.seismic_viewer.zoom_level /= 1.2
        self.seismic_viewer.zoom_level = max(0.1, self.seismic_viewer.zoom_level)
        self.seismic_viewer.update_display()
    
    def reset_view(self):
        """Restablecer vista completa"""
        self.seismic_viewer.zoom_level = 1.0
        self.seismic_viewer.offset_x = 0
        self.seismic_viewer.offset_y = 0
        self.seismic_viewer.update_display()
    
    def clear_interpretation(self):
        """Limpiar interpretación actual"""
        self.seismic_viewer.clear_interpretation()

def main():
    """Función principal"""
    app = QApplication(sys.argv)
    
    # Configurar estilo visual mejorado
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()