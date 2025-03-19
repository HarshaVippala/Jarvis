"""
System Monitor Panel for the Jarvis Assistant Desktop UI.
Displays real-time CPU and memory usage statistics.
"""
import os
import logging
import time
import psutil
from datetime import datetime
import threading
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy, QProgressBar, QTableWidget, 
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QSize, Signal, Slot, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QLinearGradient

logger = logging.getLogger(__name__)

class PerformanceGraph(QWidget):
    """A widget that displays a real-time performance graph."""
    
    def __init__(self, title: str, color: QColor, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self.history = [0] * 60  # Store 60 data points (60 seconds of history)
        self.setMinimumHeight(100)
        self.setMinimumWidth(250)
        
        # Styling
        self.bg_color = QColor(30, 30, 30)
        self.grid_color = QColor(60, 60, 60)
        self.text_color = QColor(200, 200, 200)
        
        # Data and display properties
        self.max_value = 100.0  # Default maximum (percentage)
        self.current_value = 0.0
        self.suffix = "%"  # Default suffix for values
        
    def update_value(self, value: float):
        """Update the current value and history."""
        self.current_value = value
        self.history.pop(0)  # Remove oldest value
        self.history.append(value)  # Add new value
        self.update()  # Trigger repaint
        
    def paintEvent(self, event):
        """Draw the performance graph."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        # Draw background
        painter.fillRect(0, 0, width, height, self.bg_color)
        
        # Draw grid lines
        painter.setPen(QPen(self.grid_color, 1))
        for i in range(1, 4):  # Draw 3 horizontal grid lines
            y = height * (i / 4)
            painter.drawLine(0, y, width, y)
            
        for i in range(1, 6):  # Draw 5 vertical grid lines
            x = width * (i / 6)
            painter.drawLine(x, 0, x, height)
        
        # Draw title
        painter.setPen(QPen(self.text_color, 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(10, 20, self.title)
        
        # Draw current value
        value_text = f"{self.current_value:.1f}{self.suffix}"
        painter.drawText(width - 70, 20, value_text)
        
        # Draw graph
        if len(self.history) > 1:
            # Create path for the graph
            path = QPainterPath()
            
            # Scale points to fit the graph area
            point_width = width / (len(self.history) - 1)
            scale_factor = height / self.max_value
            
            # Start at the bottom-left for the first point
            path.moveTo(0, height - (self.history[0] * scale_factor))
            
            # Add points to the path
            for i in range(1, len(self.history)):
                x = i * point_width
                y = height - (self.history[i] * scale_factor)
                path.lineTo(x, y)
            
            # Draw the line
            painter.setPen(QPen(self.color, 2))
            painter.drawPath(path)
            
            # Create gradient for fill
            gradient = QLinearGradient(0, 0, 0, height)
            fill_color = QColor(self.color)
            fill_color.setAlpha(80)  # Semi-transparent
            gradient.setColorAt(0, fill_color)
            fill_color.setAlpha(10)  # Almost transparent
            gradient.setColorAt(1, fill_color)
            
            # Close the path to create a fillable shape
            path.lineTo(width, height)
            path.lineTo(0, height)
            path.closeSubpath()
            
            # Fill the shape
            painter.fillPath(path, gradient)
        
        painter.end()


class SystemStatsTable(QTableWidget):
    """A table that displays system information and statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up the table
        self.setRowCount(5)  # Initial row count
        self.setColumnCount(2)  # Key, Value
        self.setHorizontalHeaderLabels(["Metric", "Value"])
        
        # Set table styling
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                gridline-color: #3E3E42;
                border: none;
            }
            QHeaderView::section {
                background-color: #2D2D30;
                color: #FFFFFF;
                padding: 5px;
                border: 1px solid #3E3E42;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        
        # Set column stretching
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Initialize with empty data
        self.update_stats({})
    
    def update_stats(self, stats: Dict[str, str]):
        """Update the table with new statistics."""
        # Add default stats if not provided
        if not stats:
            return
            
        # Update existing rows and add new ones if needed
        row = 0
        for key, value in stats.items():
            if row >= self.rowCount():
                self.setRowCount(row + 1)
                
            # Set items
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            
            value_item = QTableWidgetItem(str(value))
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            
            self.setItem(row, 0, key_item)
            self.setItem(row, 1, value_item)
            row += 1
        
        # Remove any extra rows
        if row < self.rowCount():
            self.setRowCount(row)


class SystemMonitorPanel(QWidget):
    """
    A panel that displays real-time system resource usage information.
    Features:
    - CPU usage graph
    - Memory usage graph
    - Disk usage information
    - System information table
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
        # Set up timer for updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # Update every second
        
        # Initial stats update
        self.update_stats()
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("System Monitor")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        main_layout.addWidget(title_label)
        
        # Graphs section
        graphs_layout = QHBoxLayout()
        
        # CPU graph
        self.cpu_graph = PerformanceGraph("CPU Usage", QColor(52, 152, 219))
        cpu_frame = QFrame()
        cpu_frame.setFrameShape(QFrame.StyledPanel)
        cpu_frame.setStyleSheet("background-color: #1E1E1E; border-radius: 5px;")
        cpu_layout = QVBoxLayout(cpu_frame)
        cpu_layout.addWidget(self.cpu_graph)
        
        # Memory graph
        self.memory_graph = PerformanceGraph("Memory Usage", QColor(46, 204, 113))
        memory_frame = QFrame()
        memory_frame.setFrameShape(QFrame.StyledPanel)
        memory_frame.setStyleSheet("background-color: #1E1E1E; border-radius: 5px;")
        memory_layout = QVBoxLayout(memory_frame)
        memory_layout.addWidget(self.memory_graph)
        
        # Add graphs to layout
        graphs_layout.addWidget(cpu_frame)
        graphs_layout.addWidget(memory_frame)
        main_layout.addLayout(graphs_layout)
        
        # System info table
        self.stats_table = SystemStatsTable()
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.StyledPanel)
        stats_frame.setStyleSheet("background-color: #1E1E1E; border-radius: 5px;")
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.addWidget(self.stats_table)
        
        main_layout.addWidget(stats_frame)
        
        # Set panel styling
        self.setStyleSheet("""
            QWidget {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QFrame {
                border: 1px solid #3E3E42;
            }
        """)
    
    @Slot()
    def update_stats(self):
        """Update all system statistics."""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent()
            self.cpu_graph.update_value(cpu_percent)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            self.memory_graph.update_value(memory.percent)
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            
            # Get process count
            process_count = len(list(psutil.process_iter()))
            
            # Get uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"
            
            # Get network stats
            net_io = psutil.net_io_counters()
            net_sent = f"{net_io.bytes_sent / (1024*1024):.2f} MB"
            net_recv = f"{net_io.bytes_recv / (1024*1024):.2f} MB"
            
            # Update stats table
            stats = {
                "CPU Cores": f"{psutil.cpu_count(logical=False)} (Physical), {psutil.cpu_count()} (Logical)",
                "Memory": f"{memory.used / (1024*1024*1024):.2f} GB / {memory.total / (1024*1024*1024):.2f} GB",
                "Disk": f"{disk.used / (1024*1024*1024):.2f} GB / {disk.total / (1024*1024*1024):.2f} GB ({disk.percent}%)",
                "Processes": str(process_count),
                "System Uptime": uptime_str,
                "Network (Sent/Recv)": f"{net_sent} / {net_recv}"
            }
            self.stats_table.update_stats(stats)
            
        except Exception as e:
            logger.error(f"Error updating system stats: {e}")
    
    def showEvent(self, event):
        """Handle show event to start updates."""
        super().showEvent(event)
        # Start the timer if it's not already running
        if not self.update_timer.isActive():
            self.update_timer.start(1000)
    
    def hideEvent(self, event):
        """Handle hide event to stop updates."""
        super().hideEvent(event)
        # Stop the timer when hidden to save resources
        if self.update_timer.isActive():
            self.update_timer.stop() 