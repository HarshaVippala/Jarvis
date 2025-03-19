"""
Floating orb widget for the Jarvis desktop application.
"""
import os
import sys
from enum import Enum
import math
from pathlib import Path
import logging

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QSize, QPoint, Signal, QPropertyAnimation, QEasingCurve, Property, QTimer, QRect
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QCursor, 
    QLinearGradient, QRadialGradient, QConicalGradient, QPixmap
)

logger = logging.getLogger(__name__)

class OrbState(Enum):
    """Enum for orb states."""
    IDLE = 0
    LISTENING = 1
    PROCESSING = 2

class FloatingOrb(QWidget):
    """Floating orb widget that can be dragged around the screen."""
    
    # Define signals
    clicked = Signal()
    moved = Signal(QPoint)
    
    def __init__(self, parent=None):
        """Initialize the floating orb."""
        # Use a simpler set of flags that works better on macOS
        # Regular window with no decorations, stays on top
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Store parent reference but don't set as Qt parent
        self._parent = parent
        
        # Set up the widget
        self.setWindowTitle("Jarvis Orb")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(150, 150)  # Set size to 150x150 for consistency
        
        # Initialize properties
        self._state = OrbState.IDLE
        self._opacity = 1.0
        self._drag_position = None
        self._color = QColor(0, 120, 220)  # Strong blue color
        
        # Add a border for better visibility
        self._border_color = QColor(255, 255, 255, 180)  # Semi-transparent white
        self._border_width = 3  # Wider border
        
        # Load Jarvis logo
        self._logo_pixmap = None
        self._load_logo()
        
        # Animation properties
        self._pulse_phase = 0
        self._rotation_angle = 0
        self._processing_timer = QTimer(self)
        self._processing_timer.timeout.connect(self._update_processing_animation)
        self._processing_timer.setInterval(50)  # 20 fps
        
        # Set up the animation
        self._pulse_animation = QPropertyAnimation(self, b"opacity")
        self._pulse_animation.setDuration(1200)
        self._pulse_animation.setStartValue(0.8)
        self._pulse_animation.setEndValue(1.0)
        self._pulse_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._pulse_animation.setLoopCount(-1)  # Infinite loop
        
        # Set up animation for state transitions
        self._color_animation = QPropertyAnimation(self, b"color")
        self._color_animation.setDuration(300)
        self._color_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Add a debug timer to log visibility status
        self._debug_timer = QTimer(self)
        self._debug_timer.timeout.connect(self._log_visibility_status)
        self._debug_timer.start(1000)  # Every second for better debugging
        
        # Force active window state
        self.setFocus(Qt.OtherFocusReason)
        self.activateWindow()
        
        print(f"Orb initialized - Size: {self.width()}x{self.height()}, Flags: {int(self.windowFlags())}")
        logger.info("FloatingOrb initialized with size: %d x %d", self.width(), self.height())
    
    def _load_logo(self):
        """Load the Jarvis logo pixmap."""
        # Try various case combinations of the filename
        possible_paths = [
            Path(__file__).parents[2] / "jarvis.PNG",
            Path(__file__).parents[2] / "jarvis.png",
            Path(__file__).parents[2] / "Jarvis.PNG",
            Path(__file__).parents[2] / "Jarvis.png",
            Path(__file__).parents[2] / "JARVIS.PNG",
            Path(__file__).parents[2] / "JARVIS.png",
            Path(__file__).parents[2] / "jarvis.jpg",  # Also try JPG format
            Path(__file__).parents[2] / "jarvis.jpeg"
        ]
        
        # Try each possible path
        for logo_path in possible_paths:
            if logo_path.exists():
                print(f"Found logo at: {logo_path}")
                logger.info("Loading logo from: %s", logo_path)
                self._logo_pixmap = QPixmap(str(logo_path))
                if self._logo_pixmap.isNull():
                    continue  # Try next path if this one fails
                else:
                    print(f"Successfully loaded logo: {logo_path.name} ({self._logo_pixmap.width()}x{self._logo_pixmap.height()})")
                    logger.info("Logo loaded successfully: %dx%d", 
                               self._logo_pixmap.width(), self._logo_pixmap.height())
                    return
        
        # If we get here, no valid logo was found
        self._logo_pixmap = None
        print("ERROR: Could not find or load any logo file. Will use text 'J' instead.")
        logger.error("Could not find or load any logo file")
    
    def _log_visibility_status(self):
        """Log visibility status of the orb for debugging purposes."""
        logger.info("Orb visibility status: visible=%s, position=%s, size=%dx%d", 
                  self.isVisible(), self.pos(), self.width(), self.height())
    
    def get_opacity(self):
        """Get the opacity value."""
        return self._opacity
    
    def set_opacity(self, opacity):
        """Set the opacity value."""
        self._opacity = opacity
        self.update()
    
    # Define the opacity property for animation
    opacity = Property(float, get_opacity, set_opacity)
    
    def get_color(self):
        """Get the color value."""
        return self._color
    
    def set_color(self, color):
        """Set the color value."""
        self._color = color
        self.update()
    
    # Define the color property for animation
    color = Property(QColor, get_color, set_color)
    
    def _update_processing_animation(self):
        """Update the processing animation."""
        self._rotation_angle = (self._rotation_angle + 10) % 360
        self._pulse_phase += 0.15
        self.update()
    
    def paintEvent(self, event):
        """Paint the floating orb."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Set up the painter
        path = QPainterPath()
        rect = self.rect().adjusted(5, 5, -5, -5)
        path.addEllipse(rect)
        
        # Draw the shadow
        shadow_offset = 5
        shadow_color = QColor(0, 0, 0, 120)  # Darker shadow for better visibility
        
        # Draw shadow
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(rect.adjusted(shadow_offset, shadow_offset, shadow_offset, shadow_offset))
        
        # Determine orb color based on state
        if self._state == OrbState.IDLE:
            # Blue for idle state
            orb_color = QColor(0, 120, 220, int(255 * self._opacity))  # Strong blue
        elif self._state == OrbState.LISTENING:
            # Green for listening state
            orb_color = QColor(40, 200, 120, int(255 * self._opacity))  # Strong green
        elif self._state == OrbState.PROCESSING:
            # Orange for processing state
            orb_color = QColor(240, 150, 50, int(255 * self._opacity))  # Strong orange
            
        # Draw the orb
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(orb_color))
        painter.drawPath(path)
        
        # Draw highlight (simple ellipse in top-left quadrant)
        highlight_width = rect.width() * 0.4
        highlight_height = rect.height() * 0.4
        highlight_x = rect.x() + rect.width() * 0.15
        highlight_y = rect.y() + rect.height() * 0.15
        
        # Set up highlight brush
        highlight_color = QColor(255, 255, 255, 70)  # Semi-transparent white
        painter.setBrush(QBrush(highlight_color))
        painter.drawEllipse(int(highlight_x), int(highlight_y), 
                           int(highlight_width), int(highlight_height))
        
        # Draw the 'J' logo in the center of the orb
        if self._logo_pixmap and not self._logo_pixmap.isNull():
            # Scale the logo to fit in the center
            scaled_logo = self._logo_pixmap.scaled(
                int(rect.width() * 0.6),  # Larger size for better visibility
                int(rect.height() * 0.6),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Calculate position to center the logo
            logo_x = rect.center().x() - scaled_logo.width() / 2
            logo_y = rect.center().y() - scaled_logo.height() / 2
            
            # Draw the logo
            painter.drawPixmap(int(logo_x), int(logo_y), scaled_logo)
        else:
            # If no logo, draw a 'J' as text
            painter.setPen(QColor(255, 255, 255))  # Pure white
            font = QFont("Arial", 50, QFont.Bold)  # Larger font size
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, "J")
        
        # Draw processing animation if in processing state
        if self._state == OrbState.PROCESSING:
            self._draw_processing_animation(painter, rect)
        
        painter.end()
    
    def _draw_processing_animation(self, painter, rect):
        """Draw the processing animation."""
        pen = QPen(QColor(255, 255, 255, 220), 3.0)  # Increased from 180 to 220 opacity, 2.5 to 3.0 width
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Draw dots around a circle
        center = rect.center()
        radius = rect.width() * 0.3  # Increased from 0.28 to 0.3
        num_dots = 8
        
        for i in range(num_dots):
            # Calculate position
            angle = (self._rotation_angle + (i * 360 / num_dots)) % 360
            radians = math.radians(angle)
            x = center.x() + radius * math.cos(radians)
            y = center.y() + radius * math.sin(radians)
            
            # Calculate opacity based on position in rotation
            relative_pos = (angle - self._rotation_angle) % 360
            opacity = 255 - min(255, relative_pos / 360 * 255 * 1.5)
            
            # Draw dot
            dot_color = QColor(255, 255, 255, opacity)
            painter.setBrush(QBrush(dot_color))
            painter.setPen(Qt.NoPen)
            
            dot_size = 4.0  # Increased from 3.5 to 4.0
            painter.drawEllipse(QPoint(int(x), int(y)), dot_size, dot_size)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            logger.debug("Mouse press event at position: %s", event.globalPosition().toPoint())
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging."""
        if event.buttons() & Qt.LeftButton and self._drag_position is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_position
            self.move(new_pos)
            self.moved.emit(new_pos)
            logger.debug("Moved orb to position: %s", new_pos)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton:
            # If drag distance is small, consider it a click
            if self._drag_position is not None and (event.globalPosition().toPoint() - self.frameGeometry().topLeft() - self._drag_position).manhattanLength() < 3:
                self.clicked.emit()
                logger.debug("Orb clicked")
            self._drag_position = None
    
    def enterEvent(self, event):
        """Handle mouse enter events."""
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._opacity = 1.0
        self.update()
    
    def leaveEvent(self, event):
        """Handle mouse leave events."""
        self.setCursor(QCursor(Qt.ArrowCursor))
        self._opacity = 0.95  # Less dimming when mouse leaves
        self.update()
    
    def show_idle(self):
        """Show the idle state."""
        # Stop any ongoing animations
        self._processing_timer.stop()
        
        # Animate color change to idle state
        self._color_animation.stop()
        self._color_animation.setStartValue(self._color)
        self._color_animation.setEndValue(QColor(30, 144, 255))  # Dodger Blue - more vibrant
        self._color_animation.start()
        
        # Update state
        self._state = OrbState.IDLE
        self.update()
        logger.debug("Orb state changed to IDLE")
    
    def show_listening(self):
        """Show the listening state."""
        # Stop any ongoing animations
        self._processing_timer.stop()
        
        # Animate color change to listening state
        self._color_animation.stop()
        self._color_animation.setStartValue(self._color)
        self._color_animation.setEndValue(QColor(0, 200, 140))  # Brighter teal
        self._color_animation.start()
        
        # Start pulse animation for listening state
        self._pulse_animation.stop()
        self._pulse_animation.start()
        
        # Update state
        self._state = OrbState.LISTENING
        self.update()
        logger.debug("Orb state changed to LISTENING")
    
    def show_processing(self):
        """Show the processing state."""
        # Stop any ongoing animations
        self._pulse_animation.stop()
        
        # Animate color change to processing state
        self._color_animation.stop()
        self._color_animation.setStartValue(self._color)
        self._color_animation.setEndValue(QColor(120, 120, 255))  # Brighter blue-purple
        self._color_animation.start()
        
        # Start processing animation
        self._processing_timer.start()
        
        # Update state
        self._state = OrbState.PROCESSING
        self.update()
        logger.debug("Orb state changed to PROCESSING")
    
    def show(self):
        """Show the widget with a fade-in effect."""
        print(f"SHOWING ORB at position: {self.pos()}")
        logger.info("Showing orb at position: %s", self.pos())
        
        # Ensure window flags are set for maximum visibility
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.BypassWindowManagerHint, True)
        self.setWindowFlag(Qt.Tool, True)
        
        super().show()
        
        # Start with transparent and animate to normal opacity
        fade_in = QPropertyAnimation(self, b"windowOpacity")
        fade_in.setDuration(250)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.start()
        
        # Force raise to top
        QTimer.singleShot(10, self.raiseOrb)
        QTimer.singleShot(100, self.raiseOrb)
        QTimer.singleShot(500, self.raiseOrb)
    
    def raiseOrb(self):
        """Raise the orb to the top and activate it."""
        # Ensure stays on top
        if not self.testAttribute(Qt.WA_ShowWithoutActivating):
            self.setAttribute(Qt.WA_ShowWithoutActivating, True)
            
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.raise_()
        self.activateWindow()
        self.update()
        print(f"RAISED orb to top, visible: {self.isVisible()}")
        logger.debug("Raised orb to top")
        
    def moveToCenter(self):
        """Move the orb to the center of the primary screen."""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        logger.info("Moved orb to center position: %d,%d", x, y) 