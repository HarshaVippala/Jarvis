"""
Response panel for displaying Jarvis's responses.
"""
import os
import sys
from enum import Enum
import time

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
    QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import (
    Qt, QSize, QPoint, QTimer, Signal, Property, 
    QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, 
    QFont, QFontMetrics, QIcon
)

from jarvis.core.events import event_bus, EventType

class ResponseType(Enum):
    """Type of response to display."""
    SIMPLE = 0  # Brief confirmation (1-2 seconds)
    INFO = 1    # Information display (3-5 seconds)
    COMPLEX = 2 # Complex information (8-10 seconds)
    REFERENCE = 3 # Reference material (until dismissed)
    STREAMING = 4 # Streaming response (until complete)

class ResponsePanel(QWidget):
    """Panel that displays responses from Jarvis."""
    
    dismissed = Signal()
    
    def __init__(self, parent=None):
        """Initialize the response panel."""
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # Set up the widget
        self.setWindowTitle("Jarvis Response")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(350, 100)
        self.setMaximumSize(500, 400)
        
        # Initialize properties
        self._opacity = 0.95
        self._text = ""
        self._full_text = ""  # For streaming responses
        self._type = ResponseType.SIMPLE
        self._is_streaming = False
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.hide)
        
        # Initialize UI
        self.init_ui()
        
        # Set up animations
        self._fade_in = QPropertyAnimation(self, b"windowOpacity")
        self._fade_in.setDuration(200)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        self._fade_out = QPropertyAnimation(self, b"windowOpacity")
        self._fade_out.setDuration(200)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.InCubic)
        self._fade_out.finished.connect(self._on_fade_out_finished)
        
        # Connect to event bus for streaming updates
        event_bus.on(EventType.STREAMING_RESPONSE, self._on_streaming_response)
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Title label
        self.title_label = QLabel("Jarvis")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        # Content frame with scrollable area
        self.content_frame = QFrame()
        self.content_frame.setFrameShape(QFrame.NoFrame)
        self.content_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.content_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background-color: transparent;
                font-size: 13px;
            }
        """)
        
        content_layout.addWidget(self.content_label)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(self.content_frame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 30);
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 100);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Actions layout
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(5)
        
        # Add pin button
        self.pin_button = QPushButton("📌")
        self.pin_button.setFixedSize(24, 24)
        self.pin_button.setToolTip("Pin this panel")
        self.pin_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 30);
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 50);
            }
        """)
        self.pin_button.clicked.connect(self.toggle_pin)
        
        # Add copy button
        self.copy_button = QPushButton("Copy")
        self.copy_button.setFixedHeight(24)
        self.copy_button.setToolTip("Copy to clipboard")
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 30);
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 0 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 50);
            }
        """)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        
        # Add close button
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setToolTip("Dismiss")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 30);
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 70);
            }
        """)
        self.close_button.clicked.connect(self.hide_panel)
        
        # Add buttons to actions layout
        actions_layout.addWidget(self.pin_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self.copy_button)
        actions_layout.addWidget(self.close_button)
        
        # Add all widgets to main layout
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(actions_layout)
        
        # Set the layout
        self.setLayout(main_layout)
    
    def paintEvent(self, event):
        """Paint the response panel background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded rect path
        background_rect = self.rect().adjusted(0, 0, 0, 0)
        path = QPainterPath()
        path.addRoundedRect(background_rect, 15, 15)
        
        # Draw shadow (simple version)
        shadow_color = QColor(0, 0, 0, 80)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawRoundedRect(background_rect.adjusted(3, 3, 3, 3), 15, 15)
        
        # Draw background - Make it darker to ensure text is visible
        background_color = QColor(40, 44, 52, int(255 * self._opacity))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(background_color))
        painter.drawPath(path)
        
        # Draw border
        border_color = QColor(70, 130, 180, 100)  # Steel Blue with transparency
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
    
    def show_text(self, text, response_type=None):
        """Show text in the response panel.
        
        Args:
            text: The text to display.
            response_type: The type of response (determines duration).
                If None, the type will be determined automatically.
        """
        self._text = text
        self._full_text = text  # Initialize full text
        
        # Determine response type if not provided
        if response_type is None:
            # Simple heuristic to determine response type
            word_count = len(text.split())
            if word_count < 15:
                self._type = ResponseType.SIMPLE
            elif word_count < 50:
                self._type = ResponseType.INFO
            elif word_count < 200:
                self._type = ResponseType.COMPLEX
            else:
                self._type = ResponseType.REFERENCE
        else:
            self._type = response_type
        
        # Set the text
        self.content_label.setText(text)
        
        # Adjust the size based on the content
        self.adjust_size()
        
        # Show the panel
        if not self.isVisible():
            self.setWindowOpacity(0.0)
            self.show()
            self._fade_in.start()
        
        # Set auto-hide timer based on response type
        if self._type == ResponseType.SIMPLE:
            delay = 3000  # 3 seconds
        elif self._type == ResponseType.INFO:
            delay = 5000  # 5 seconds
        elif self._type == ResponseType.COMPLEX:
            delay = 10000  # 10 seconds
        elif self._type == ResponseType.STREAMING:
            # Don't auto-hide for streaming responses
            self._auto_hide_timer.stop()
            return
        else:  # REFERENCE
            # Don't auto-hide for reference material
            self._auto_hide_timer.stop()
            return
        
        # Start the auto-hide timer
        self._auto_hide_timer.start(delay)
        
    def start_streaming(self):
        """Start streaming mode for real-time responses."""
        self._is_streaming = True
        self._full_text = ""
        self.show_text("", ResponseType.STREAMING)
        
    def _on_streaming_response(self, text_chunk):
        """Handle streaming response chunks from the event bus."""
        if not self._is_streaming:
            # If we're not already in streaming mode, start it
            self.start_streaming()
        
        # Append the chunk to our full text
        self._full_text += text_chunk
        
        # Update the displayed text
        self.content_label.setText(self._full_text)
        
        # Adjust the size based on new content
        self.adjust_size()
        
        # Make sure the panel is visible
        if not self.isVisible():
            self.setWindowOpacity(0.0)
            self.show()
            self._fade_in.start()
        
    def finish_streaming(self):
        """End streaming mode and display the complete text."""
        self._is_streaming = False
        # Determine response type based on final text
        self.show_text(self._full_text)
    
    def adjust_size(self):
        """Adjust the panel size based on content."""
        # Get the size of the text
        font_metrics = QFontMetrics(self.content_label.font())
        text_rect = font_metrics.boundingRect(
            0, 0, 400, 1000,
            Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop,
            self._text
        )
        
        # Calculate new height (text + margins + buttons)
        new_height = min(text_rect.height() + 100, 400)
        
        # Resize the panel
        self.resize(400, new_height)
    
    def hide_panel(self):
        """Hide the panel with animation."""
        self._auto_hide_timer.stop()
        self._fade_out.start()
    
    def _on_fade_out_finished(self):
        """Handle fade out animation finished."""
        self.hide()
        self.dismissed.emit()
    
    def toggle_pin(self):
        """Toggle pinned state (prevent auto-hide)."""
        if self._auto_hide_timer.isActive():
            self._auto_hide_timer.stop()
            self.pin_button.setText("📍")  # Pinned icon
        else:
            # Re-enable auto-hide based on type
            if self._type != ResponseType.REFERENCE:
                if self._type == ResponseType.SIMPLE:
                    self._auto_hide_timer.start(2000)
                elif self._type == ResponseType.INFO:
                    self._auto_hide_timer.start(5000)
                elif self._type == ResponseType.COMPLEX:
                    self._auto_hide_timer.start(10000)
            self.pin_button.setText("📌")  # Unpinned icon
    
    def copy_to_clipboard(self):
        """Copy content to clipboard."""
        QApplication.clipboard().setText(self._text) 