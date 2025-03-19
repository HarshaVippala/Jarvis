import os
import logging
from typing import Optional, Callable, List

from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QComboBox, QCheckBox, QSlider, QGroupBox
)

class VoicePanel(QWidget):
    """UI panel for voice interactions and settings."""
    
    # Define signals
    listenRequested = Signal()  # Request to start listening
    stopListeningRequested = Signal()  # Request to stop listening
    speakRequested = Signal(str)  # Request to speak text
    localWhisperToggled = Signal(bool)  # Local Whisper mode toggled
    whisperModelChanged = Signal(str)  # Whisper model size changed
    ttsVoiceChanged = Signal(str)  # TTS voice changed
    wakeWordDetectionToggled = Signal(bool)  # Wake word detection toggled
    wakeWordSensitivityChanged = Signal(float)  # Wake word sensitivity changed
    wakeWordsChanged = Signal(list)  # Active wake words changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # UI state
        self.is_listening = False
        self.is_speaking = False
        self.is_wake_word_active = False
        self.available_wake_words = ["jarvis", "hey jarvis", "computer"]
        
        # Set up UI
        self._setup_ui()
        
        self.logger.info("Voice Panel initialized")
    
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Voice Control")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Status indicator
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self.status_label)
        
        # Microphone button
        self.mic_button = QPushButton()
        self.mic_button.setIcon(QIcon.fromTheme("audio-input-microphone"))
        self.mic_button.setIconSize(QSize(24, 24))
        self.mic_button.setToolTip("Start/Stop Listening")
        self.mic_button.setCheckable(True)
        self.mic_button.clicked.connect(self._on_mic_button_clicked)
        status_layout.addWidget(self.mic_button)
        
        # Wake word toggle button
        self.wake_word_button = QPushButton()
        self.wake_word_button.setIcon(QIcon.fromTheme("audio-headset"))
        self.wake_word_button.setIconSize(QSize(24, 24))
        self.wake_word_button.setToolTip("Toggle Wake Word Detection")
        self.wake_word_button.setCheckable(True)
        self.wake_word_button.clicked.connect(self._on_wake_word_button_clicked)
        status_layout.addWidget(self.wake_word_button)
        
        main_layout.addLayout(status_layout)
        
        # Transcription display
        transcription_group = QGroupBox("Transcription")
        transcription_layout = QVBoxLayout()
        
        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setMinimumHeight(80)
        transcription_layout.addWidget(self.transcription_text)
        
        transcription_group.setLayout(transcription_layout)
        main_layout.addWidget(transcription_group)
        
        # Text-to-speech controls
        tts_group = QGroupBox("Text-to-Speech")
        tts_layout = QVBoxLayout()
        
        self.tts_input = QTextEdit()
        self.tts_input.setPlaceholderText("Type text to speak...")
        self.tts_input.setMaximumHeight(60)
        tts_layout.addWidget(self.tts_input)
        
        tts_controls = QHBoxLayout()
        
        self.speak_button = QPushButton("Speak")
        self.speak_button.clicked.connect(self._on_speak_button_clicked)
        tts_controls.addWidget(self.speak_button)
        
        self.voice_selector = QComboBox()
        self.voice_selector.addItems(["female_standard", "male_standard", "female_fast", "multilingual"])
        self.voice_selector.currentTextChanged.connect(self._on_voice_changed)
        tts_controls.addWidget(self.voice_selector)
        
        tts_layout.addLayout(tts_controls)
        tts_group.setLayout(tts_layout)
        main_layout.addWidget(tts_group)
        
        # Wake word settings
        wake_word_group = QGroupBox("Wake Word Detection")
        wake_word_layout = QVBoxLayout()
        
        # Wake word selection
        wake_word_selection = QHBoxLayout()
        wake_word_selection.addWidget(QLabel("Active Wake Words:"))
        
        self.wake_word_selector = QComboBox()
        self.wake_word_selector.addItems(self.available_wake_words)
        self.wake_word_selector.setCurrentText("jarvis")
        wake_word_selection.addWidget(self.wake_word_selector)
        
        self.add_wake_word_button = QPushButton("+")
        self.add_wake_word_button.setMaximumWidth(30)
        self.add_wake_word_button.clicked.connect(self._on_add_wake_word_clicked)
        wake_word_selection.addWidget(self.add_wake_word_button)
        
        wake_word_layout.addLayout(wake_word_selection)
        
        # Active wake words display
        self.active_wake_words_label = QLabel("Active: jarvis")
        wake_word_layout.addWidget(self.active_wake_words_label)
        
        # Wake word sensitivity slider
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("Sensitivity:"))
        
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setMinimum(0)
        self.sensitivity_slider.setMaximum(100)
        self.sensitivity_slider.setValue(50)
        self.sensitivity_slider.setTickPosition(QSlider.TicksBelow)
        self.sensitivity_slider.setTickInterval(10)
        self.sensitivity_slider.valueChanged.connect(self._on_sensitivity_changed)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        
        self.sensitivity_value_label = QLabel("0.5")
        sensitivity_layout.addWidget(self.sensitivity_value_label)
        
        wake_word_layout.addLayout(sensitivity_layout)
        
        wake_word_group.setLayout(wake_word_layout)
        main_layout.addWidget(wake_word_group)
        
        # Speech recognition settings
        stt_group = QGroupBox("Speech Recognition")
        stt_layout = QVBoxLayout()
        
        self.local_whisper_checkbox = QCheckBox("Use Local Whisper Model")
        self.local_whisper_checkbox.toggled.connect(self._on_local_whisper_toggled)
        stt_layout.addWidget(self.local_whisper_checkbox)
        
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model Size:"))
        
        self.model_selector = QComboBox()
        self.model_selector.addItems(["tiny", "base", "small", "medium", "large"])
        self.model_selector.setCurrentText("tiny")
        self.model_selector.setEnabled(False)  # Disabled until local mode is enabled
        self.model_selector.currentTextChanged.connect(self._on_model_changed)
        model_layout.addWidget(self.model_selector)
        
        stt_layout.addLayout(model_layout)
        stt_group.setLayout(stt_layout)
        main_layout.addWidget(stt_group)
        
        # Add spacer at the end
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    @Slot()
    def _on_mic_button_clicked(self):
        """Handle microphone button click."""
        if self.mic_button.isChecked():
            self.start_listening()
        else:
            self.stop_listening()
    
    @Slot()
    def _on_wake_word_button_clicked(self):
        """Handle wake word button click."""
        if self.wake_word_button.isChecked():
            self.start_wake_word_detection()
        else:
            self.stop_wake_word_detection()
    
    @Slot()
    def _on_speak_button_clicked(self):
        """Handle speak button click."""
        text = self.tts_input.toPlainText().strip()
        if text:
            self.speakRequested.emit(text)
    
    @Slot(str)
    def _on_voice_changed(self, voice: str):
        """Handle voice selection change."""
        self.ttsVoiceChanged.emit(voice)
    
    @Slot(bool)
    def _on_local_whisper_toggled(self, checked: bool):
        """Handle local Whisper mode toggle."""
        self.model_selector.setEnabled(checked)
        self.localWhisperToggled.emit(checked)
    
    @Slot(str)
    def _on_model_changed(self, model: str):
        """Handle Whisper model selection change."""
        if self.local_whisper_checkbox.isChecked():
            self.whisperModelChanged.emit(model)
    
    @Slot()
    def _on_add_wake_word_clicked(self):
        """Handle add wake word button click."""
        selected_word = self.wake_word_selector.currentText()
        
        # Parse current active wake words
        current_text = self.active_wake_words_label.text().replace("Active: ", "")
        active_words = current_text.split(", ") if current_text else []
        
        # Add selected word if not already in the list
        if selected_word not in active_words:
            active_words.append(selected_word)
            
            # Update the label
            self.active_wake_words_label.setText(f"Active: {', '.join(active_words)}")
            
            # Emit signal with updated list
            self.wakeWordsChanged.emit(active_words)
    
    @Slot(int)
    def _on_sensitivity_changed(self, value: int):
        """Handle sensitivity slider change."""
        # Convert 0-100 to 0.0-1.0
        sensitivity = value / 100.0
        self.sensitivity_value_label.setText(f"{sensitivity:.1f}")
        self.wakeWordSensitivityChanged.emit(sensitivity)
    
    def set_available_wake_words(self, wake_words: List[str]):
        """Set available wake words for the dropdown."""
        self.available_wake_words = wake_words
        
        # Save current selection
        current_selection = self.wake_word_selector.currentText()
        
        # Update dropdown
        self.wake_word_selector.clear()
        self.wake_word_selector.addItems(wake_words)
        
        # Restore selection if possible
        if current_selection in wake_words:
            self.wake_word_selector.setCurrentText(current_selection)
    
    def start_listening(self):
        """Start listening for voice input."""
        if not self.is_listening:
            self.is_listening = True
            self.listenRequested.emit()
            self.status_label.setText("Listening...")
            self.status_label.setStyleSheet("color: #22a;")
            self.mic_button.setChecked(True)
    
    def stop_listening(self):
        """Stop listening for voice input."""
        if self.is_listening:
            self.is_listening = False
            self.stopListeningRequested.emit()
            
            if self.is_wake_word_active:
                self.status_label.setText("Listening for wake word...")
                self.status_label.setStyleSheet("color: #2a2;")
            else:
                self.status_label.setText("Ready")
                self.status_label.setStyleSheet("color: #666;")
                
            self.mic_button.setChecked(False)
    
    def start_wake_word_detection(self):
        """Start wake word detection."""
        if not self.is_wake_word_active:
            self.is_wake_word_active = True
            self.wakeWordDetectionToggled.emit(True)
            self.status_label.setText("Listening for wake word...")
            self.status_label.setStyleSheet("color: #2a2;")
            self.wake_word_button.setChecked(True)
    
    def stop_wake_word_detection(self):
        """Stop wake word detection."""
        if self.is_wake_word_active:
            self.is_wake_word_active = False
            self.wakeWordDetectionToggled.emit(False)
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("color: #666;")
            self.wake_word_button.setChecked(False)
    
    @Slot(str)
    def on_transcription_received(self, text: str):
        """Handle transcription received from voice system."""
        current_text = self.transcription_text.toPlainText()
        if current_text:
            current_text += "\n"
        self.transcription_text.setText(current_text + text)
        self.transcription_text.verticalScrollBar().setValue(
            self.transcription_text.verticalScrollBar().maximum()
        )
    
    @Slot(bool)
    def on_listening_state_changed(self, is_listening: bool):
        """Handle listening state change notification."""
        if is_listening != self.is_listening:
            if is_listening:
                self.start_listening()
            else:
                self.stop_listening()
    
    @Slot(bool)
    def on_speaking_state_changed(self, is_speaking: bool):
        """Handle speaking state change notification."""
        self.is_speaking = is_speaking
        self.speak_button.setEnabled(not is_speaking)
        if is_speaking:
            self.status_label.setText("Speaking...")
            self.status_label.setStyleSheet("color: #2a2;")
        else:
            if self.is_listening:
                self.status_label.setText("Listening...")
                self.status_label.setStyleSheet("color: #22a;")
            elif self.is_wake_word_active:
                self.status_label.setText("Listening for wake word...")
                self.status_label.setStyleSheet("color: #2a2;")
            else:
                self.status_label.setText("Ready")
                self.status_label.setStyleSheet("color: #666;")
    
    @Slot(bool)
    def on_wake_word_state_changed(self, is_active: bool):
        """Handle wake word detection state change notification."""
        if is_active != self.is_wake_word_active:
            if is_active:
                self.start_wake_word_detection()
            else:
                self.stop_wake_word_detection()
    
    @Slot(str)
    def on_wake_word_detected(self, wake_word: str):
        """Handle wake word detection notification."""
        # Add indicator to transcription
        current_text = self.transcription_text.toPlainText()
        if current_text:
            current_text += "\n"
        self.transcription_text.setText(current_text + f"[Wake word detected: {wake_word}]")
        self.transcription_text.verticalScrollBar().setValue(
            self.transcription_text.verticalScrollBar().maximum()
        )
    
    @Slot(str)
    def on_error_occurred(self, error_message: str):
        """Handle error notification."""
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("color: #a22;")
        
        # Auto-reset after a few seconds
        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.on_listening_state_changed(self.is_listening)) 