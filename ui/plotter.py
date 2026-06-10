import pyqtgraph as pg
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout

class PerformancePlotter(QWidget):
    def __init__(self, max_points=1200): # 1200 points @ 3sec = 1 hour
        super().__init__()
        self.max_points = max_points
        
        # Circular buffers
        self.cpu_data = np.zeros(self.max_points, dtype=np.float32)
        self.ram_data = np.zeros(self.max_points, dtype=np.float32)
        self.ptr = 0
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('#1e1e2e')
        self.graph_widget.setTitle("استهلاك المعالج والذاكرة عبر الزمن", color='#cdd6f4', size='12pt')
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        self.graph_widget.setYRange(0, 100, padding=0)
        
        # Styles
        cpu_pen = pg.mkPen(color='#f38ba8', width=2)
        ram_pen = pg.mkPen(color='#89b4fa', width=2)
        
        self.cpu_curve = self.graph_widget.plot(self.cpu_data, pen=cpu_pen, name="CPU %")
        self.ram_curve = self.graph_widget.plot(self.ram_data, pen=ram_pen, name="RAM %")
        
        # Legend
        self.graph_widget.addLegend()
        
        layout.addWidget(self.graph_widget)

    def update_plot(self, cpu_val, ram_val):
        """تحديث المصفوفات الثابتة لتجنب تسرب الذاكرة"""
        self.cpu_data[self.ptr] = cpu_val
        self.ram_data[self.ptr] = ram_val
        
        self.ptr += 1
        if self.ptr >= self.max_points:
            self.ptr = 0
            
        # Draw current valid data
        # We need to roll the array so the latest point is at the end, or just plot up to ptr
        # Better: plot the filled portion if not wrapped, else roll
        
        if self.cpu_data[-1] == 0.0 and self.ptr < self.max_points:
            # Not yet wrapped
            self.cpu_curve.setData(self.cpu_data[:self.ptr])
            self.ram_curve.setData(self.ram_data[:self.ptr])
        else:
            # Wrapped, we roll data to show oldest to newest
            self.cpu_curve.setData(np.roll(self.cpu_data, -self.ptr))
            self.ram_curve.setData(np.roll(self.ram_data, -self.ptr))
