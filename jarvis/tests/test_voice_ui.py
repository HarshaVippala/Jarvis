#!/usr/bin/env python3
"""
Test script for voice UI integration.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt, QTimer

from jarvis.desktop.controllers.voice_controller import VoiceController
from jarvis.desktop.ui.voice_panel import VoicePanel

class VoiceTestWindow(QMainWindow):
    """Test window for the voice system with UI integration."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Set up window properties
        self.setWindowTitle("Jarvis Voice System Test")
        self.setMinimumSize(500, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create voice panel
        self.voice_panel = VoicePanel()
        layout.addWidget(self.voice_panel)
        
        # Create voice controller
        self.voice_controller = VoiceController()
        
        # Connect signals/slots
        self._connect_signals()
        
        # Initialize voice system in the background
        QTimer.singleShot(100, self.voice_controller.initialize)
        
        # Show help message
        QTimer.singleShot(500, self._show_help_message)
        
        self.logger.info("Voice Test Window initialized")
    
    def _connect_signals(self):
        """Connect signals between voice panel and controller."""
        # Panel -> Controller
        self.voice_panel.listenRequested.connect(self.voice_controller.start_listening)
        self.voice_panel.stopListeningRequested.connect(self.voice_controller.stop_listening)
        self.voice_panel.speakRequested.connect(self.voice_controller.speak)
        self.voice_panel.localWhisperToggled.connect(self.voice_controller.toggle_local_whisper)
        self.voice_panel.whisperModelChanged.connect(self.voice_controller.set_whisper_model_size)
        self.voice_panel.ttsVoiceChanged.connect(self.voice_controller.set_tts_voice)
        self.voice_panel.wakeWordDetectionToggled.connect(
            lambda enabled: self.voice_controller.start_wake_word_detection() if enabled 
            else self.voice_controller.stop_wake_word_detection()
        )
        self.voice_panel.wakeWordSensitivityChanged.connect(self.voice_controller.set_wake_word_sensitivity)
        self.voice_panel.wakeWordsChanged.connect(self.voice_controller.set_active_wake_words)
        
        # Controller -> Panel
        self.voice_controller.transcriptionReceived.connect(self.voice_panel.on_transcription_received)
        self.voice_controller.listeningStateChanged.connect(self.voice_panel.on_listening_state_changed)
        self.voice_controller.speakingStateChanged.connect(self.voice_panel.on_speaking_state_changed)
        self.voice_controller.wakeWordStateChanged.connect(self.voice_panel.on_wake_word_state_changed)
        self.voice_controller.wakeWordDetected.connect(self.voice_panel.on_wake_word_detected)
        self.voice_controller.errorOccurred.connect(self.voice_panel.on_error_occurred)
        self.voice_controller.initializationComplete.connect(self._on_initialization_complete)
    
    def _on_initialization_complete(self, success):
        """Handle voice system initialization completion."""
        if success:
            # Get available wake words
            self.voice_controller.get_available_wake_words(self.voice_panel.set_available_wake_words)
        else:
            QMessageBox.warning(self, "Initialization Failed", 
                                "Voice system initialization failed. Some features may not work correctly.")
    
    def _show_help_message(self):
        """Show a help message with usage instructions."""
        help_text = (
            "<b>Voice System Test Application</b><br><br>"
            "<b>Manual Mode:</b><br>"
            "- Click the microphone button to start/stop listening<br>"
            "- Type text in the box and click Speak to test TTS<br><br>"
            "<b>Wake Word Mode:</b><br>"
            "- Click the headset button to enable wake word detection<br>"
            "- Say 'Jarvis' to activate voice recognition<br>"
            "- Add additional wake words using the + button<br>"
            "- Adjust sensitivity if needed<br><br>"
            "<b>Speech Recognition Settings:</b><br>"
            "- Toggle local Whisper model for offline recognition<br>"
            "- Select model size (larger = more accurate but slower)<br><br>"
            "Note: First-time use will download required models"
        )
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Usage Instructions")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(help_text)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.info("Closing application, shutting down voice system...")
        self.voice_controller.shutdown()
        event.accept()

def main():
    """Main entry point for the voice test application."""
    app = QApplication(sys.argv)
    
    window = VoiceTestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 