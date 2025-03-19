"""
Activity Log Panel for the Jarvis Assistant Desktop UI.
Displays a history of user interactions and assistant actions.
"""
import os
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QLineEdit, QComboBox, QCheckBox,
    QSplitter, QTextEdit, QMenu, QFileDialog, QTabWidget
)
from PySide6.QtCore import Qt, QSize, Signal, Slot, QTimer, QEvent
from PySide6.QtGui import QIcon, QAction, QColor, QPalette, QFont

from jarvis.desktop.ui.system_monitor_panel import SystemMonitorPanel

logger = logging.getLogger(__name__)

class LogEntry(QFrame):
    """A single entry in the activity log."""
    
    def __init__(
        self, 
        entry_type: str,  # "user", "assistant", "action", "system"
        content: str, 
        timestamp: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.entry_type = entry_type
        self.content = content
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components for this log entry."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Header with timestamp and entry type
        header_layout = QHBoxLayout()
        
        # Format timestamp as readable time
        time_str = datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")
        timestamp_label = QLabel(time_str)
        timestamp_label.setStyleSheet("color: #888888; font-size: 10px;")
        
        # Type icon/label varies by entry type
        type_label = QLabel()
        type_icon = ""
        type_color = "#FFFFFF"
        
        if self.entry_type == "user":
            type_icon = "👤 User"
            type_color = "#4A90E2"
        elif self.entry_type == "assistant":
            type_icon = "🤖 Assistant"
            type_color = "#50C878"
        elif self.entry_type == "action":
            type_icon = "⚡ Action"
            type_color = "#FFD700"
        elif self.entry_type == "system":
            type_icon = "⚙️ System"
            type_color = "#A9A9A9"
            
        type_label.setText(type_icon)
        type_label.setStyleSheet(f"color: {type_color}; font-weight: bold; font-size: 12px;")
        
        header_layout.addWidget(timestamp_label)
        header_layout.addStretch()
        header_layout.addWidget(type_label)
        
        # Content area
        content_edit = QTextEdit()
        content_edit.setReadOnly(True)
        content_edit.setPlainText(self.content)
        content_edit.setFixedHeight(min(80, 20 * min(5, self.content.count('\n') + 1)))
        content_edit.setStyleSheet(
            f"background-color: rgba(0, 0, 0, 0.1); border-radius: 5px; padding: 5px; "
            f"border: 1px solid {type_color}; color: #FFFFFF;"
        )
        
        # Add components to layout
        layout.addLayout(header_layout)
        layout.addWidget(content_edit)
        
        # Set frame styling
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("QFrame { background-color: rgba(30, 30, 30, 0.7); border-radius: 10px; }")
        
    def matches_filter(self, filter_text: str, entry_types: List[str]) -> bool:
        """Check if this entry matches the given filter criteria."""
        # Check entry type filter
        if self.entry_type not in entry_types:
            return False
            
        # Check text filter (if provided)
        if filter_text and filter_text.lower() not in self.content.lower():
            return False
            
        return True


class ActivityLogWidget(QWidget):
    """Widget that contains the actual activity log content."""
    
    log_added = Signal(dict)  # Signal emitted when a log entry is added
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_entries = []  # Store all log entries
        self.filtered_entries = []  # Entries after filtering
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Activity Log")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_log)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_log)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.export_btn)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addLayout(button_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter logs...")
        self.filter_input.textChanged.connect(self.apply_filters)
        
        self.filter_type = QComboBox()
        self.filter_type.addItem("All Types", "all")
        self.filter_type.addItem("User", "user")
        self.filter_type.addItem("Assistant", "assistant")
        self.filter_type.addItem("Actions", "action")
        self.filter_type.addItem("System", "system")
        self.filter_type.currentIndexChanged.connect(self.apply_filters)
        
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.filter_input)
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.filter_type)
        
        # Log entries area
        self.log_area = QScrollArea()
        self.log_area.setWidgetResizable(True)
        self.log_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.log_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(5, 5, 5, 5)
        self.log_layout.setSpacing(10)
        self.log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.log_area.setWidget(self.log_container)
        
        # Add all components to main layout
        main_layout.addLayout(title_layout)
        main_layout.addLayout(filter_layout)
        main_layout.addWidget(self.log_area, 1)  # Give the log area all available space
    
    @Slot(str, str, object)
    def add_log_entry(self, entry_type: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a new entry to the activity log."""
        # Create the log entry object
        log_entry = LogEntry(
            entry_type=entry_type,
            content=content,
            metadata=metadata,
            parent=self.log_container
        )
        
        # Add to internal lists
        self.log_entries.append(log_entry)
        
        # Check if it should be visible based on current filters
        if self._entry_matches_current_filters(log_entry):
            self.log_layout.insertWidget(0, log_entry)  # Add at the top (newest first)
            self.filtered_entries.append(log_entry)
        
        # Emit signal that a log was added
        self.log_added.emit({
            "type": entry_type,
            "content": content,
            "timestamp": log_entry.timestamp,
            "metadata": metadata or {}
        })
        
        # Keep log size reasonable (limit to 100 entries)
        if len(self.log_entries) > 100:
            self._trim_log()
    
    def _entry_matches_current_filters(self, entry: LogEntry) -> bool:
        """Check if the entry matches the current filter settings."""
        filter_text = self.filter_input.text()
        
        # Get selected type filter
        filter_type = self.filter_type.currentData()
        if filter_type == "all":
            entry_types = ["user", "assistant", "action", "system"]
        else:
            entry_types = [filter_type]
            
        return entry.matches_filter(filter_text, entry_types)
    
    @Slot()
    def apply_filters(self):
        """Apply the current filters to the log entries."""
        # Clear the current view
        for entry in self.filtered_entries:
            entry.setParent(None)  # Remove from layout
        
        self.filtered_entries = []
        
        # Get filter values
        filter_text = self.filter_input.text()
        
        # Get selected type filter
        filter_type = self.filter_type.currentData()
        if filter_type == "all":
            entry_types = ["user", "assistant", "action", "system"]
        else:
            entry_types = [filter_type]
        
        # Apply filters and rebuild the view
        for entry in self.log_entries:
            if entry.matches_filter(filter_text, entry_types):
                self.log_layout.addWidget(entry)
                self.filtered_entries.append(entry)
    
    @Slot()
    def clear_log(self):
        """Clear all log entries."""
        for entry in self.log_entries:
            entry.deleteLater()
            
        self.log_entries = []
        self.filtered_entries = []
    
    @Slot()
    def export_log(self):
        """Export the log to a file."""
        # Open file dialog to get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Log", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w') as f:
                for entry in reversed(self.log_entries):  # Oldest to newest
                    timestamp = datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] [{entry.entry_type.upper()}]\n")
                    f.write(f"{entry.content}\n\n")
                    
            logger.info(f"Log exported to {file_path}")
        except Exception as e:
            logger.error(f"Error exporting log: {e}")
    
    def _trim_log(self):
        """Trim the log to maintain a reasonable size."""
        # Remove oldest entries if we have too many
        while len(self.log_entries) > 100:
            oldest = self.log_entries.pop(-1)  # Remove from list
            
            # Also remove from filtered list if present
            if oldest in self.filtered_entries:
                self.filtered_entries.remove(oldest)
                
            oldest.deleteLater()  # Clean up UI component


class ActivityLogPanel(QWidget):
    """
    A panel that displays the history of user interactions and assistant actions.
    Features:
    - Shows user inputs (both voice and text)
    - Displays assistant responses
    - Records actions taken by the assistant
    - Provides filtering and search capabilities
    - Allows exporting logs for troubleshooting
    - Includes system monitoring features
    """
    
    log_added = Signal(dict)  # Signal emitted when a log entry is added
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3E3E42;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D30;
                color: #FFFFFF;
                padding: 8px 20px;
                border: 1px solid #3E3E42;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                border-bottom: 2px solid #007ACC;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3E3E42;
            }
        """)
        
        # Create the activity log tab
        self.activity_log = ActivityLogWidget()
        self.tab_widget.addTab(self.activity_log, "Activity Log")
        
        # Create the system monitor tab
        self.system_monitor = SystemMonitorPanel()
        self.tab_widget.addTab(self.system_monitor, "System Monitor")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Connect signals
        self.activity_log.log_added.connect(self.log_added)
        
        # Set panel styling
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3E3E42;
            }
            QLineEdit, QComboBox {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                padding: 5px;
                border-radius: 5px;
            }
            QScrollArea {
                border: none;
            }
        """)
    
    @Slot(str, str, object)
    def add_log_entry(self, entry_type: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a new entry to the activity log."""
        # Forward to the activity log widget
        self.activity_log.add_log_entry(entry_type, content, metadata)
    
    @Slot()
    def clear_log(self):
        """Clear all log entries."""
        self.activity_log.clear_log()
    
    @Slot()
    def export_log(self):
        """Export the log to a file."""
        self.activity_log.export_log()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Make sure the system monitor starts updating when shown
        if self.tab_widget.currentWidget() == self.system_monitor:
            self.system_monitor.update_stats()
    
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        # No special handling needed here, the system monitor already stops updates when hidden 