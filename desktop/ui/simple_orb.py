"""
Simple floating orb widget for Jarvis that prioritizes visibility.
Stripped down to ensure it will definitely appear on macOS.
"""
import logging
from pathlib import Path

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QPushButton
from PySide6.QtCore import Qt, QPoint, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QPainter, QPainterPath, QBrush, QPen, QRegion

logger = logging.getLogger(__name__)

class SimpleOrb(QWidget):
    """A super simplified orb that should definitely appear on screen."""
    
    # Define signals
    clicked = Signal()
    
    def __init__(self, parent=None):
        """Initialize the simple orb."""
        super().__init__(None)  # No parent, no special flags to start with
        
        # Set up window properties
        self.setWindowTitle("Jarvis")
        self.setFixedSize(150, 150)
        
        # Remove window frame
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        
        # Force this window to be a solid color, not transparent
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Set up the drag properties
        self._drag_position = None
        
        # Try to load the icon
        self.icon_pixmap = None
        self._load_icon()
        
        # Set up a periodic raise timer
        self._raise_timer = QTimer(self)
        self._raise_timer.timeout.connect(self.raiseWindow)
        self._raise_timer.start(1000)  # Every second
        
        # Position in center of screen
        self.moveToCenter()
        
        print(f"SimpleOrb created with size: {self.width()}x{self.height()}")
    
    def _load_icon(self):
        """Load the Jarvis icon pixmap."""
        possible_paths = [
            Path(__file__).parents[2] / "jarvis.PNG",
            Path(__file__).parents[2] / "jarvis.png"
        ]
        
        for icon_path in possible_paths:
            if icon_path.exists():
                print(f"Loading icon from: {icon_path}")
                self.icon_pixmap = QPixmap(str(icon_path))
                if not self.icon_pixmap.isNull():
                    print(f"Successfully loaded icon: {icon_path.name} ({self.icon_pixmap.width()}x{self.icon_pixmap.height()})")
                    # Set window icon as well
                    self.setWindowIcon(QIcon(str(icon_path)))
                    QApplication.setWindowIcon(QIcon(str(icon_path)))
                    return
        
        print("ERROR: Could not find or load any icon file.")
    
    def paintEvent(self, event):
        """Custom paint event to create a circular window."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set up the circular shape
        rect = self.rect()
        radius = min(rect.width(), rect.height()) / 2
        center = rect.center()
        
        # Create circular path
        path = QPainterPath()
        path.addEllipse(center, radius, radius)
        
        # Make the window region circular for mouse events and visuals
        window_region = QRegion(
            center.x() - radius, 
            center.y() - radius,
            int(radius * 2), 
            int(radius * 2), 
            QRegion.Ellipse
        )
        self.setMask(window_region)
        
        # No background color or border - just draw the icon
        if self.icon_pixmap and not self.icon_pixmap.isNull():
            # Scale the icon to fit the entire circle
            icon_size = int(radius * 2)  # Make it fill the entire circle
            scaled_pixmap = self.icon_pixmap.scaled(
                icon_size, icon_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Position the icon in the center
            icon_x = center.x() - scaled_pixmap.width() / 2
            icon_y = center.y() - scaled_pixmap.height() / 2
            
            # Draw the icon
            painter.drawPixmap(int(icon_x), int(icon_y), scaled_pixmap)
        else:
            # Draw a 'J' as fallback with a subtle background
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 120, 255, 100)))  # Semi-transparent blue
            painter.drawEllipse(center, radius, radius)
            
            # Draw the J
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            font = QFont("Arial", 40, QFont.Bold)  # Larger font
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, "J")
    
    def raiseWindow(self):
        """Ensure the window is on top."""
        self.raise_()
        self.activateWindow()
    
    def moveToCenter(self):
        """Move to center of screen."""
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        print(f"Moved SimpleOrb to center: {x},{y}")
    
    def mousePressEvent(self, event):
        """Handle mouse press events for dragging and clicking."""
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.clicked.emit()
            print("SimpleOrb clicked")
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging."""
        if event.buttons() & Qt.LeftButton and self._drag_position is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_position
            self.move(new_pos)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton:
            self._drag_position = None 