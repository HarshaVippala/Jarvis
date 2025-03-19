"""
Main window for the Jarvis desktop application.
"""
import os
import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QSystemTrayIcon, QMenu, QWidget, 
    QVBoxLayout, QPushButton, QApplication, QLabel
)
from PySide6.QtCore import Qt, QSize, QPoint, QSettings, Signal, Slot, QTimer, QRect
from PySide6.QtGui import QIcon, QAction, QFont, QPixmap, QColor, QScreen, QPainter, QRadialGradient, QBrush
from openai import OpenAI

from jarvis.desktop.ui.floating_orb import FloatingOrb
from jarvis.desktop.ui.response_panel import ResponsePanel, ResponseType
from jarvis.desktop.ui.settings_panel import SettingsPanel
from jarvis.desktop.ui.activity_log_panel import ActivityLogPanel
from jarvis.desktop.controllers.voice_manager import VoiceManager
from jarvis.core.assistant import jarvis

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main window for the Jarvis desktop application."""
    
    def __init__(self, settings: QSettings):
        """Initialize the main window."""
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.settings = settings
        self.setWindowTitle("Jarvis")
        
        # Set application icon
        self._load_app_icon()
        
        # Create the main components
        self.tray_icon = None
        self.floating_orb = None
        self.response_panel = None
        self.settings_panel = None
        self.activity_log_panel = None
        self.voice_manager = None
        
        # Initialize the user interface
        self.init_ui()
        
        # Connect to Jarvis backend
        self.jarvis = jarvis
        
        # Set up a visibility check timer
        self._visibility_timer = QTimer(self)
        self._visibility_timer.timeout.connect(self.ensure_orb_visible)
        self._visibility_timer.start(2000)  # Check every 2 seconds (more frequent than before)
    
    def _load_app_icon(self):
        """Create and set a simple application icon."""
        # Create a simple icon for the application
        icon_size = 256  # Larger size for app icon
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.transparent)
        
        # Draw icon with better quality for application icon
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw blue circle with solid color for maximum visibility
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 120, 220))  # Strong blue
        painter.drawEllipse(4, 4, icon_size - 8, icon_size - 8)
        
        # Draw "J" in center with white text
        painter.setPen(QColor(255, 255, 255))  # Pure white
        font = QFont("Arial", icon_size/3, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "J")
        
        painter.end()
        
        # Set as application icon
        app_icon = QIcon(pixmap)
        self.setWindowIcon(app_icon)
        QApplication.setWindowIcon(app_icon)
        
        logger.info("Application icon loaded")
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create system tray icon
        self.create_tray_icon()
        
        # Create floating orb
        self.floating_orb = FloatingOrb(self)
        self.floating_orb.setFocus()  # Ensure orb gets focus
        
        # Position the orb on screen
        self.position_orb_on_screen()
        
        # Create response panel (initially hidden)
        self.response_panel = ResponsePanel(self)
        
        # Create settings panel (initially hidden)
        self.settings_panel = SettingsPanel(self.settings, self)
        
        # Create activity log panel (initially hidden)
        self.activity_log_panel = ActivityLogPanel(self)
        self.activity_log_panel.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.activity_log_panel.setWindowTitle("Jarvis Activity Log")
        self.activity_log_panel.resize(800, 600)  # Set initial size
        
        # Create voice manager
        self.voice_manager = VoiceManager(self)
        
        # Initialize the window size and position
        self.setFixedSize(1, 1)  # Minimal size as we're using the floating orb
        self.move_to_saved_position()
        
        # Connect signals
        self.connect_signals()
        
        # Show the orb and ensure it's visible
        self.floating_orb.show()
        self.floating_orb.raise_()  # Ensure it's on top
        self.floating_orb.activateWindow()  # Activate the window
        
        # Force ensure orb is visible by immediately calling the method
        QTimer.singleShot(100, self.ensure_orb_visible)
    
    def position_orb_on_screen(self):
        """Position the orb on screen in a sensible default location if no saved position."""
        saved_pos = self.settings.value("jarvis/position")
        
        if not saved_pos or not isinstance(saved_pos, QPoint):
            # No saved position or invalid type - always position in center
            self.floating_orb.moveToCenter()
            # Save this position
            self.settings.setValue("jarvis/position", self.floating_orb.pos())
            logger.info(f"Set orb to center position: {self.floating_orb.pos()}")
        else:
            # Use saved position but ensure it's on screen
            self.ensure_position_on_screen(saved_pos)
    
    def ensure_position_on_screen(self, pos):
        """Ensure the given position is on screen."""
        if isinstance(pos, QPoint):
            # Get primary screen geometry for simplicity
            primary_screen = QApplication.primaryScreen().availableGeometry()
            
            # Log the original position and screen
            logger.info(f"Checking orb position: {pos.x()}, {pos.y()}")
            logger.info(f"Primary screen: {primary_screen.x()}, {primary_screen.y()}, {primary_screen.width()}x{primary_screen.height()}")
            
            # Force on-screen positioning within primary screen
            # If position is completely off-screen or negative, center it
            if (pos.x() < primary_screen.x() or 
                pos.y() < primary_screen.y() or 
                pos.x() > primary_screen.x() + primary_screen.width() or
                pos.y() > primary_screen.y() + primary_screen.height()):
                
                logger.warning(f"Position {pos.x()}, {pos.y()} is off-screen. Moving to center.")
                x = primary_screen.x() + (primary_screen.width() - self.floating_orb.width()) // 2
                y = primary_screen.y() + (primary_screen.height() - self.floating_orb.height()) // 2
            else:
                # Constrain to screen boundaries
                x = max(primary_screen.x(), min(pos.x(), 
                        primary_screen.x() + primary_screen.width() - self.floating_orb.width()))
                y = max(primary_screen.y(), min(pos.y(), 
                        primary_screen.y() + primary_screen.height() - self.floating_orb.height()))
            
            adjusted_pos = QPoint(x, y)
            self.floating_orb.move(adjusted_pos)
            
            # Log the adjustment
            logger.info(f"Adjusted orb position from {pos.x()}, {pos.y()} to {adjusted_pos.x()}, {adjusted_pos.y()}")
            
            # Save adjusted position if it changed
            if adjusted_pos != pos:
                self.settings.setValue("jarvis/position", adjusted_pos)
    
    def ensure_orb_visible(self):
        """Ensure the orb is visible on screen."""
        if self.floating_orb:
            # Check if orb is visible
            if not self.floating_orb.isVisible():
                # Always move to center when showing after being hidden
                logger.info("Orb is not visible, showing and centering")
                self.floating_orb.moveToCenter()
                self.floating_orb.show()
            
            # Reposition if off-screen
            current_pos = self.floating_orb.pos()
            if current_pos.x() < 0 or current_pos.y() < 0:
                logger.warning(f"Orb is at negative position: {current_pos.x()},{current_pos.y()}. Centering.")
                self.floating_orb.moveToCenter()
            
            # Make sure it stays on top
            self.floating_orb.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.floating_orb.raise_()
            self.floating_orb.activateWindow()
            
            # Force a repaint
            self.floating_orb.update()
            
            # Log visibility state
            logger.info(f"Orb visibility check: visible={self.floating_orb.isVisible()}, at position {self.floating_orb.pos()}")
    
    def create_tray_icon(self):
        """Create the system tray icon and menu."""
        # Create the tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use a very simple approach for the icon - solid blue circle with white J
        icon_size = 64
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.transparent)
        
        # Draw a simple, high contrast icon
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw blue circle - simple solid color for maximum visibility
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 120, 220))  # Strong blue
        painter.drawEllipse(4, 4, icon_size - 8, icon_size - 8)
        
        # Draw J for Jarvis - white, bold, and centered
        painter.setPen(QColor(255, 255, 255))  # Pure white
        font = QFont("Arial", 32, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "J")
        
        painter.end()
        
        # Set the pixmap as the tray icon
        icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)  # Also set as window icon
        QApplication.setWindowIcon(icon)  # Set for the entire application
        
        # Create the tray menu
        tray_menu = QMenu()
        
        # Add actions to the menu
        show_orb_action = QAction("Show Jarvis", self)
        show_orb_action.triggered.connect(self.ensure_orb_visible)
        
        enable_action = QAction("Enable Jarvis", self)
        enable_action.setCheckable(True)
        enable_action.setChecked(self.settings.value("jarvis/enabled", True, type=bool))
        enable_action.triggered.connect(self.toggle_jarvis)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        
        activity_log_action = QAction("Activity Log", self)
        activity_log_action.triggered.connect(self.show_activity_log)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        
        # Add actions to menu
        tray_menu.addAction(show_orb_action)
        tray_menu.addAction(enable_action)
        tray_menu.addSeparator()
        tray_menu.addAction(settings_action)
        tray_menu.addAction(activity_log_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        # Set the menu for tray icon
        self.tray_icon.setContextMenu(tray_menu)
        
        # Connect activation signal
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Show the tray icon
        self.tray_icon.show()
        
        logger.info("Tray icon created")
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.Trigger:
            # Single click - toggle orb visibility
            if self.floating_orb.isVisible():
                self.floating_orb.hide()
            else:
                self.ensure_orb_visible()
    
    def connect_signals(self):
        """Connect signals between components."""
        # Connect FloatingOrb signals
        self.floating_orb.clicked.connect(self.toggle_listening)
        self.floating_orb.moved.connect(self.save_position)
        
        # Connect VoiceManager signals
        if self.voice_manager:
            self.voice_manager.listening_started.connect(self.floating_orb.show_listening)
            self.voice_manager.listening_stopped.connect(self.floating_orb.show_idle)
            self.voice_manager.processing_started.connect(self.floating_orb.show_processing)
            self.voice_manager.processing_stopped.connect(self.floating_orb.show_idle)
            self.voice_manager.transcription_received.connect(self.handle_transcription)
            self.voice_manager.error_occurred.connect(self.handle_error)
            self.voice_manager.api_usage_updated.connect(self.update_api_usage)
        
        # Connect settings panel signals
        if self.settings_panel:
            self.settings_panel.settings_changed.connect(self.handle_settings_changed)
    
    def toggle_jarvis(self, enabled):
        """Enable or disable Jarvis."""
        if self.floating_orb:
            self.floating_orb.setVisible(enabled)
        self.settings.setValue("jarvis/enabled", enabled)
    
    def toggle_listening(self):
        """Toggle between listening and idle states."""
        if self.voice_manager:
            self.voice_manager.toggle_listening()
    
    def show_settings(self):
        """Show the settings panel."""
        if self.settings_panel:
            self.settings_panel.show()
    
    def show_activity_log(self):
        """Show the activity log panel."""
        if self.activity_log_panel:
            # Center on screen
            screen_geometry = QApplication.primaryScreen().availableGeometry()
            x = (screen_geometry.width() - self.activity_log_panel.width()) // 2
            y = (screen_geometry.height() - self.activity_log_panel.height()) // 2
            self.activity_log_panel.move(x, y)
            
            # Show the panel
            self.activity_log_panel.show()
            self.activity_log_panel.raise_()
            self.activity_log_panel.activateWindow()
    
    def handle_transcription(self, text):
        """Handle transcribed text from voice input."""
        if text:
            # Add to activity log
            if self.activity_log_panel:
                self.activity_log_panel.add_log_entry("user", text)
            
            # Process the command with Jarvis
            self.floating_orb.show_processing()
            
            # Start a separate thread to process the command
            # For now we'll use a timer to simulate processing
            QTimer.singleShot(100, lambda: self.process_command(text))
    
    def handle_error(self, error_message):
        """Handle error from voice manager."""
        # Add to activity log
        if self.activity_log_panel:
            self.activity_log_panel.add_log_entry("system", f"Error: {error_message}")
        
        # Show error in response panel
        if self.response_panel:
            self.response_panel.show_text(f"Error: {error_message}", ResponseType.SIMPLE)
    
    def update_api_usage(self, tokens, cost):
        """Update API usage statistics."""
        if self.settings_panel:
            self.settings_panel.update_usage_statistics(tokens, cost)
    
    def handle_settings_changed(self, settings_dict):
        """Handle settings changes."""
        # Update OpenAI API key in voice manager if changed
        if self.voice_manager and "openai_api_key" in settings_dict:
            openai_api_key = settings_dict["openai_api_key"]
            if openai_api_key:
                self.voice_manager.openai_client = OpenAI(api_key=openai_api_key)
                self.voice_manager.openai_api_key = openai_api_key
        
        # Update voice settings
        if self.voice_manager:
            # Update voice type if changed
            if "voice_type" in settings_dict:
                self.voice_manager.set_voice_type(settings_dict["voice_type"])
            
            # Update TTS enabled/disabled
            if "tts_enabled" in settings_dict:
                self.voice_manager.set_tts_enabled(settings_dict["tts_enabled"])
                
        # Update ElevenLabs API key in voice manager if changed (for future implementation)
        if self.voice_manager and "elevenlabs_api_key" in settings_dict:
            self.voice_manager.elevenlabs_api_key = settings_dict["elevenlabs_api_key"]
    
    def process_command(self, text):
        """Process a command with Jarvis."""
        try:
            # Log the command processing
            if self.activity_log_panel:
                self.activity_log_panel.add_log_entry("action", f"Processing command: {text}")
            
            # Call the Jarvis backend
            response = self.jarvis.process_command(text)
            
            # Show the response
            self.show_response(response)
        except Exception as e:
            # Log the error
            if self.activity_log_panel:
                self.activity_log_panel.add_log_entry("system", f"Error processing command: {str(e)}")
            
            # Show error response
            self.show_response(f"Error: {str(e)}")
        finally:
            # Return to idle state
            self.floating_orb.show_idle()
    
    def show_response(self, text):
        """Show a response from Jarvis."""
        # Add to activity log
        if self.activity_log_panel:
            self.activity_log_panel.add_log_entry("assistant", text)
        
        if self.response_panel:
            self.response_panel.show_text(text)
            
            # Position near orb
            if self.floating_orb:
                orb_pos = self.floating_orb.pos()
                self.response_panel.move(orb_pos.x() + 70, orb_pos.y())
            
        # Also speak the response if voice manager is available
        if self.voice_manager:
            self.voice_manager.speak(text)
    
    def move_to_saved_position(self):
        """Move the window to the saved position."""
        # Get the saved position
        pos = self.settings.value("jarvis/position", QPoint(100, 100))
        
        # Ensure position is valid
        if isinstance(pos, QPoint):
            self.move(pos)
            
            # Also move the orb if it exists
            if self.floating_orb:
                self.ensure_position_on_screen(pos)
    
    def save_position(self, pos):
        """Save the current window position."""
        self.settings.setValue("jarvis/position", pos)
    
    def quit_application(self):
        """Quit the application."""
        # Clean up resources
        if self.voice_manager:
            self.voice_manager.cleanup()
        
        QApplication.quit()
    
    def closeEvent(self, event):
        """Handle the close event."""
        # Hide instead of close
        event.ignore()
        self.hide() 