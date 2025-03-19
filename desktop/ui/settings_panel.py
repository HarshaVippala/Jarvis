"""
Settings panel for configuring Jarvis.
"""
import os
import sys
import json
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTabWidget, QLineEdit, QCheckBox, QComboBox, QGroupBox,
    QFormLayout, QScrollArea, QSlider, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QSettings, QSize, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont

from jarvis.config import settings as jarvis_settings

class SettingsPanel(QWidget):
    """Panel for configuring Jarvis settings."""
    
    settings_changed = Signal(dict)
    
    def __init__(self, settings: QSettings, parent=None):
        """Initialize the settings panel."""
        super().__init__(parent, Qt.Window | Qt.WindowCloseButtonHint)
        
        # Set up the widget
        self.setWindowTitle("Jarvis Settings")
        self.resize(500, 400)
        
        # Save settings object
        self.settings = settings
        
        # Initialize UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.create_general_tab()
        self.create_voice_tab()
        self.create_api_tab()
        self.create_usage_tab()
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.reset_button.clicked.connect(self.reset_to_defaults)
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.close)
        
        buttons_layout.addWidget(self.reset_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        
        # Add buttons layout to main layout
        main_layout.addLayout(buttons_layout)
        
        # Set the layout
        self.setLayout(main_layout)
    
    def create_general_tab(self):
        """Create the general settings tab."""
        general_tab = QWidget()
        layout = QFormLayout(general_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Start at login
        self.start_at_login = QCheckBox()
        layout.addRow("Start at login:", self.start_at_login)
        
        # Follow active screen
        self.follow_active_screen = QCheckBox()
        layout.addRow("Follow active screen:", self.follow_active_screen)
        
        # Display duration
        self.display_duration = QComboBox()
        self.display_duration.addItems(["Short", "Medium", "Long", "Auto"])
        layout.addRow("Response display duration:", self.display_duration)
        
        # Theme
        self.theme = QComboBox()
        self.theme.addItems(["Dark", "Light"])
        layout.addRow("Theme:", self.theme)
        
        # Add spacer
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding))
        
        # Add tab
        self.tab_widget.addTab(general_tab, "General")
    
    def create_voice_tab(self):
        """Create the voice settings tab."""
        voice_tab = QWidget()
        layout = QFormLayout(voice_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Enable voice
        self.enable_voice = QCheckBox()
        layout.addRow("Enable voice:", self.enable_voice)
        
        # Voice type
        self.voice_type = QComboBox()
        
        # OpenAI voice options
        openai_voices = {
            "alloy": "Alloy (Neutral)",
            "echo": "Echo (Male)",
            "fable": "Fable (Female)",
            "onyx": "Onyx (Male, deep)",
            "nova": "Nova (Female, warm)",
            "shimmer": "Shimmer (Female, clear)"
        }
        
        for voice_id, voice_name in openai_voices.items():
            self.voice_type.addItem(voice_name, voice_id)
            
        layout.addRow("Voice type:", self.voice_type)
        
        # Wake word
        self.wake_word = QLineEdit()
        self.wake_word.setPlaceholderText("Jarvis")
        layout.addRow("Wake word:", self.wake_word)
        
        # Voice volume
        volume_layout = QHBoxLayout()
        self.voice_volume = QSlider(Qt.Horizontal)
        self.voice_volume.setRange(0, 100)
        self.voice_volume.setValue(80)
        self.voice_volume_label = QLabel("80%")
        self.voice_volume.valueChanged.connect(
            lambda v: self.voice_volume_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.voice_volume)
        volume_layout.addWidget(self.voice_volume_label)
        layout.addRow("Voice volume:", volume_layout)
        
        # Add spacer
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding))
        
        # Add tab
        self.tab_widget.addTab(voice_tab, "Voice")
    
    def create_api_tab(self):
        """Create the API settings tab."""
        api_tab = QWidget()
        layout = QFormLayout(api_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # OpenAI API Key
        self.openai_api_key = QLineEdit()
        self.openai_api_key.setPlaceholderText("sk-...")
        self.openai_api_key.setEchoMode(QLineEdit.Password)
        layout.addRow("OpenAI API Key:", self.openai_api_key)
        
        # OpenAI Model
        self.openai_model = QComboBox()
        self.openai_model.addItems(["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"])
        layout.addRow("OpenAI Model:", self.openai_model)
        
        # ElevenLabs API Key
        self.elevenlabs_api_key = QLineEdit()
        self.elevenlabs_api_key.setPlaceholderText("Optional, for text-to-speech")
        self.elevenlabs_api_key.setEchoMode(QLineEdit.Password)
        layout.addRow("ElevenLabs API Key:", self.elevenlabs_api_key)
        
        # ElevenLabs Voice ID
        self.elevenlabs_voice_id = QLineEdit()
        self.elevenlabs_voice_id.setPlaceholderText("Optional voice ID")
        layout.addRow("ElevenLabs Voice ID:", self.elevenlabs_voice_id)
        
        # Add spacer
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding))
        
        # Add tab
        self.tab_widget.addTab(api_tab, "API Keys")
    
    def create_usage_tab(self):
        """Create the usage statistics tab."""
        usage_tab = QWidget()
        layout = QVBoxLayout(usage_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Current session
        session_group = QGroupBox("Current Session")
        session_layout = QFormLayout()
        
        self.session_cost = QLabel("$0.00")
        self.session_tokens = QLabel("0")
        self.session_requests = QLabel("0")
        
        session_layout.addRow("Cost:", self.session_cost)
        session_layout.addRow("Tokens used:", self.session_tokens)
        session_layout.addRow("API Requests:", self.session_requests)
        
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)
        
        # Total usage
        total_group = QGroupBox("Total Usage")
        total_layout = QFormLayout()
        
        self.total_cost = QLabel("$0.00")
        self.total_tokens = QLabel("0")
        self.total_requests = QLabel("0")
        self.last_reset = QLabel("Never")
        
        total_layout.addRow("Total cost:", self.total_cost)
        total_layout.addRow("Total tokens:", self.total_tokens)
        total_layout.addRow("Total requests:", self.total_requests)
        total_layout.addRow("Last reset:", self.last_reset)
        
        total_group.setLayout(total_layout)
        layout.addWidget(total_group)
        
        # Reset button
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        
        self.reset_usage_button = QPushButton("Reset Usage Statistics")
        self.reset_usage_button.clicked.connect(self.reset_usage_statistics)
        
        reset_layout.addWidget(self.reset_usage_button)
        layout.addLayout(reset_layout)
        
        # Add spacer
        layout.addStretch()
        
        # Add tab
        self.tab_widget.addTab(usage_tab, "Usage")
    
    def load_settings(self):
        """Load settings from QSettings."""
        # General settings
        self.start_at_login.setChecked(self.settings.value("jarvis/start_at_login", False, bool))
        self.follow_active_screen.setChecked(self.settings.value("jarvis/follow_active_screen", True, bool))
        self.display_duration.setCurrentText(self.settings.value("jarvis/display_duration", "Auto", str))
        self.theme.setCurrentText(self.settings.value("jarvis/theme", "Dark", str))
        
        # Voice settings
        self.enable_voice.setChecked(self.settings.value("jarvis/tts_enabled", True, bool))
        
        # Find the index for the voice type
        voice_id = self.settings.value("jarvis/voice_type", "alloy", str)
        for i in range(self.voice_type.count()):
            if self.voice_type.itemData(i) == voice_id:
                self.voice_type.setCurrentIndex(i)
                break
                
        self.wake_word.setText(self.settings.value("jarvis/wake_word", "Jarvis", str))
        self.voice_volume.setValue(self.settings.value("jarvis/voice_volume", 80, int))
        
        # API settings
        self.openai_api_key.setText(self.settings.value("jarvis/openai_api_key", "", str))
        self.openai_model.setCurrentText(self.settings.value("jarvis/openai_model", "gpt-4o", str))
        self.elevenlabs_api_key.setText(self.settings.value("jarvis/elevenlabs_api_key", "", str))
        self.elevenlabs_voice_id.setText(self.settings.value("jarvis/elevenlabs_voice_id", "", str))
        
        # Usage statistics
        self.session_cost.setText(f"${self.settings.value('jarvis/session_cost', 0.0, float):.2f}")
        self.session_tokens.setText(str(self.settings.value("jarvis/session_tokens", 0, int)))
        self.session_requests.setText(str(self.settings.value("jarvis/session_requests", 0, int)))
        
        self.total_cost.setText(f"${self.settings.value('jarvis/total_cost', 0.0, float):.2f}")
        self.total_tokens.setText(str(self.settings.value("jarvis/total_tokens", 0, int)))
        self.total_requests.setText(str(self.settings.value("jarvis/total_requests", 0, int)))
        
        last_reset = self.settings.value("jarvis/last_reset", "", str)
        if last_reset:
            self.last_reset.setText(last_reset)
        else:
            self.last_reset.setText("Never")
    
    def save_settings(self):
        """Save settings to QSettings."""
        # General settings
        self.settings.setValue("jarvis/start_at_login", self.start_at_login.isChecked())
        self.settings.setValue("jarvis/follow_active_screen", self.follow_active_screen.isChecked())
        self.settings.setValue("jarvis/display_duration", self.display_duration.currentText())
        self.settings.setValue("jarvis/theme", self.theme.currentText())
        
        # Voice settings
        self.settings.setValue("jarvis/tts_enabled", self.enable_voice.isChecked())
        # Get the voice ID from the ComboBox item data
        voice_id = self.voice_type.currentData()
        self.settings.setValue("jarvis/voice_type", voice_id)
        self.settings.setValue("jarvis/wake_word", self.wake_word.text())
        self.settings.setValue("jarvis/voice_volume", self.voice_volume.value())
        
        # API settings
        self.settings.setValue("jarvis/openai_api_key", self.openai_api_key.text())
        self.settings.setValue("jarvis/openai_model", self.openai_model.currentText())
        self.settings.setValue("jarvis/elevenlabs_api_key", self.elevenlabs_api_key.text())
        self.settings.setValue("jarvis/elevenlabs_voice_id", self.elevenlabs_voice_id.text())
        
        # Signal that settings have changed
        settings_dict = {
            "openai_api_key": self.openai_api_key.text(),
            "openai_model": self.openai_model.currentText(),
            "elevenlabs_api_key": self.elevenlabs_api_key.text(),
            "elevenlabs_voice_id": self.elevenlabs_voice_id.text(),
            "tts_enabled": self.enable_voice.isChecked(),
            "voice_type": voice_id,
            "wake_word": self.wake_word.text(),
            "voice_volume": self.voice_volume.value(),
            "theme": self.theme.currentText(),
            "display_duration": self.display_duration.currentText(),
        }
        self.settings_changed.emit(settings_dict)
        
        # Close the panel
        self.close()
    
    def reset_to_defaults(self):
        """Reset settings to defaults."""
        # General settings
        self.start_at_login.setChecked(False)
        self.follow_active_screen.setChecked(True)
        self.display_duration.setCurrentText("Auto")
        self.theme.setCurrentText("Dark")
        
        # Voice settings
        self.enable_voice.setChecked(True)
        # Find the index for the default voice type (alloy)
        for i in range(self.voice_type.count()):
            if self.voice_type.itemData(i) == "alloy":
                self.voice_type.setCurrentIndex(i)
                break
        self.wake_word.setText("Jarvis")
        self.voice_volume.setValue(80)
        
        # API settings
        # Don't reset API keys
        self.openai_model.setCurrentText("gpt-4o")
    
    def reset_usage_statistics(self):
        """Reset usage statistics."""
        # Only reset session stats
        self.settings.setValue("jarvis/session_cost", 0.0)
        self.settings.setValue("jarvis/session_tokens", 0)
        self.settings.setValue("jarvis/session_requests", 0)
        
        # Update last reset time
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.settings.setValue("jarvis/last_reset", now)
        
        # Update UI
        self.session_cost.setText("$0.00")
        self.session_tokens.setText("0")
        self.session_requests.setText("0")
        self.last_reset.setText(now)
    
    def update_usage_statistics(self, tokens_used, cost):
        """Update usage statistics."""
        # Update session stats
        session_cost = self.settings.value("jarvis/session_cost", 0.0, float) + cost
        session_tokens = self.settings.value("jarvis/session_tokens", 0, int) + tokens_used
        session_requests = self.settings.value("jarvis/session_requests", 0, int) + 1
        
        self.settings.setValue("jarvis/session_cost", session_cost)
        self.settings.setValue("jarvis/session_tokens", session_tokens)
        self.settings.setValue("jarvis/session_requests", session_requests)
        
        # Update total stats
        total_cost = self.settings.value("jarvis/total_cost", 0.0, float) + cost
        total_tokens = self.settings.value("jarvis/total_tokens", 0, int) + tokens_used
        total_requests = self.settings.value("jarvis/total_requests", 0, int) + 1
        
        self.settings.setValue("jarvis/total_cost", total_cost)
        self.settings.setValue("jarvis/total_tokens", total_tokens)
        self.settings.setValue("jarvis/total_requests", total_requests)
        
        # Update UI if visible
        if self.isVisible():
            self.session_cost.setText(f"${session_cost:.2f}")
            self.session_tokens.setText(str(session_tokens))
            self.session_requests.setText(str(session_requests))
            
            self.total_cost.setText(f"${total_cost:.2f}")
            self.total_tokens.setText(str(total_tokens))
            self.total_requests.setText(str(total_requests)) 