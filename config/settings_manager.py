"""
Settings Manager for Jarvis

This module provides centralized settings management for the Jarvis application,
including user preferences, feature toggles, and configuration.
"""
import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import threading

# For Qt settings
try:
    from PySide6.QtCore import QSettings
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

logger = logging.getLogger(__name__)

# Default settings file path
DEFAULT_SETTINGS_PATH = Path.home() / ".jarvis" / "settings.json"

class FeatureToggle:
    """
    Represents a toggleable feature in the Jarvis application.
    """
    def __init__(self, 
                feature_id: str, 
                name: str, 
                description: str, 
                default_enabled: bool = True,
                category: str = "general",
                requires: Optional[List[str]] = None,
                conflicts_with: Optional[List[str]] = None,
                resource_impact: int = 0):  # 0-10 scale
        """
        Initialize a feature toggle.
        
        Args:
            feature_id: Unique identifier for the feature
            name: Display name for the feature
            description: Description of what the feature does
            default_enabled: Whether the feature is enabled by default
            category: Category for grouping features in UI
            requires: List of feature IDs that must be enabled for this feature
            conflicts_with: List of feature IDs that cannot be enabled with this feature
            resource_impact: Impact on system resources (0-10 scale, higher = more impact)
        """
        self.feature_id = feature_id
        self.name = name
        self.description = description
        self.default_enabled = default_enabled
        self.category = category
        self.requires = requires or []
        self.conflicts_with = conflicts_with or []
        self.resource_impact = resource_impact


class SettingsManager:
    """
    Centralized manager for application settings.
    
    Handles:
    - User preferences
    - Feature toggles
    - Configuration persistence
    - Settings validation
    """
    def __init__(self, settings_path: Optional[Path] = None):
        """
        Initialize the settings manager.
        
        Args:
            settings_path: Path to the settings file (optional)
        """
        self._settings_path = settings_path or DEFAULT_SETTINGS_PATH
        
        # Initialize settings dictionary
        self._settings: Dict[str, Any] = {}
        
        # Initialize feature toggles
        self._features: Dict[str, FeatureToggle] = {}
        self._feature_states: Dict[str, bool] = {}
        
        # For thread safety
        self._lock = threading.RLock()
        
        # Qt settings for desktop app
        self._qt_settings = None
        if HAVE_QT:
            self._qt_settings = QSettings("Jarvis", "AI Assistant")
        
        # Create settings directory if it doesn't exist
        os.makedirs(os.path.dirname(self._settings_path), exist_ok=True)
        
        # Load settings
        self._load_settings()
        
        # Register default features
        self._register_default_features()
    
    def start(self):
        """Start the settings manager."""
        logger.info("Settings Manager started")
    
    def stop(self):
        """Stop the settings manager and save settings."""
        self.save_settings()
        logger.info("Settings Manager stopped")
    
    def _register_default_features(self):
        """Register default feature toggles."""
        # Language Model
        self.register_feature(FeatureToggle(
            feature_id="language_model",
            name="Language Model",
            description="Core AI model for understanding and generating responses",
            default_enabled=True,
            category="core",
            resource_impact=8
        ))
        
        # Speech Recognition
        self.register_feature(FeatureToggle(
            feature_id="speech_recognition",
            name="Speech Recognition",
            description="Convert speech to text using Whisper",
            default_enabled=True,
            category="voice",
            resource_impact=5
        ))
        
        # Text-to-Speech
        self.register_feature(FeatureToggle(
            feature_id="text_to_speech",
            name="Text-to-Speech",
            description="Convert text to spoken audio using Coqui TTS",
            default_enabled=True,
            category="voice",
            resource_impact=5
        ))
        
        # Screen Observation
        self.register_feature(FeatureToggle(
            feature_id="screen_observation",
            name="Screen Observation",
            description="Capture and analyze screen content when requested",
            default_enabled=True,
            category="context",
            resource_impact=6
        ))
        
        # Memory (Vector Database)
        self.register_feature(FeatureToggle(
            feature_id="memory",
            name="Conversation Memory",
            description="Remember past interactions using vector database",
            default_enabled=True,
            category="memory",
            resource_impact=4
        ))
        
        # Auto-Launch
        self.register_feature(FeatureToggle(
            feature_id="auto_launch",
            name="Start on Login",
            description="Automatically start Jarvis when you log in",
            default_enabled=True,
            category="system",
            resource_impact=1
        ))
    
    def register_feature(self, feature: FeatureToggle) -> None:
        """
        Register a feature toggle.
        
        Args:
            feature: The feature toggle to register
        """
        with self._lock:
            feature_id = feature.feature_id
            
            # Check if feature already exists
            if feature_id in self._features:
                logger.warning(f"Feature {feature_id} already registered, replacing")
            
            # Register the feature
            self._features[feature_id] = feature
            
            # Initialize state if not already set
            if feature_id not in self._feature_states:
                self._feature_states[feature_id] = feature.default_enabled
            
            logger.info(f"Registered feature: {feature_id}")
    
    def get_features(self) -> List[FeatureToggle]:
        """Get all registered features."""
        with self._lock:
            return list(self._features.values())
    
    def get_features_by_category(self) -> Dict[str, List[FeatureToggle]]:
        """Get features organized by category."""
        with self._lock:
            result: Dict[str, List[FeatureToggle]] = {}
            
            for feature in self._features.values():
                category = feature.category
                
                if category not in result:
                    result[category] = []
                
                result[category].append(feature)
            
            return result
    
    def is_feature_enabled(self, feature_id: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_id: ID of the feature to check
            
        Returns:
            True if the feature is enabled, False otherwise
        """
        with self._lock:
            if feature_id not in self._features:
                logger.warning(f"Unknown feature: {feature_id}")
                return False
            
            return self._feature_states.get(feature_id, False)
    
    def set_feature_enabled(self, feature_id: str, enabled: bool) -> bool:
        """
        Enable or disable a feature.
        
        Args:
            feature_id: ID of the feature to enable/disable
            enabled: Whether to enable the feature
            
        Returns:
            True if the operation was successful, False otherwise
        """
        with self._lock:
            if feature_id not in self._features:
                logger.warning(f"Cannot toggle unknown feature: {feature_id}")
                return False
            
            # Check dependencies if enabling
            if enabled:
                feature = self._features[feature_id]
                
                # Check required features
                for required in feature.requires:
                    if required not in self._features:
                        logger.warning(f"Required feature {required} not found")
                        return False
                    
                    if not self._feature_states.get(required, False):
                        logger.warning(f"Cannot enable {feature_id} because it requires {required}")
                        return False
                
                # Check conflicting features
                for conflict in feature.conflicts_with:
                    if conflict in self._features and self._feature_states.get(conflict, False):
                        logger.warning(f"Cannot enable {feature_id} because it conflicts with {conflict}")
                        return False
            
            # Update feature state
            self._feature_states[feature_id] = enabled
            
            # If disabling, also disable dependent features
            if not enabled:
                for dep_id, dep_feature in self._features.items():
                    if feature_id in dep_feature.requires:
                        self._feature_states[dep_id] = False
                        logger.info(f"Automatically disabled {dep_id} because {feature_id} was disabled")
            
            logger.info(f"Feature {feature_id} {'enabled' if enabled else 'disabled'}")
            return True
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Setting value, or default if not found
        """
        with self._lock:
            # Check Qt settings first (for UI preferences)
            if self._qt_settings is not None:
                if self._qt_settings.contains(key):
                    return self._qt_settings.value(key, default)
            
            # Then check JSON settings
            value = self._settings.get(key, default)
            return value
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        with self._lock:
            # Use Qt settings for UI preferences
            if key.startswith("ui.") and self._qt_settings is not None:
                self._qt_settings.setValue(key, value)
                self._qt_settings.sync()
            else:
                # Use JSON settings for everything else
                self._settings[key] = value
            
            logger.debug(f"Setting updated: {key}")
    
    def save_settings(self) -> None:
        """Save settings to disk."""
        with self._lock:
            try:
                # Save feature states
                self._settings["features"] = self._feature_states
                
                # Write settings to file
                with open(self._settings_path, "w") as f:
                    json.dump(self._settings, f, indent=2)
                
                logger.info(f"Settings saved to {self._settings_path}")
            except Exception as e:
                logger.error(f"Error saving settings: {e}")
    
    def _load_settings(self) -> None:
        """Load settings from disk."""
        with self._lock:
            try:
                if os.path.exists(self._settings_path):
                    with open(self._settings_path, "r") as f:
                        self._settings = json.load(f)
                    
                    # Load feature states
                    if "features" in self._settings:
                        self._feature_states = self._settings["features"]
                    
                    logger.info(f"Settings loaded from {self._settings_path}")
                else:
                    logger.info(f"Settings file {self._settings_path} not found, using defaults")
                    self._settings = {}
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                self._settings = {}
    
    def reset_settings(self) -> None:
        """Reset all settings to defaults."""
        with self._lock:
            # Clear settings
            self._settings = {}
            
            # Reset feature states to defaults
            self._feature_states = {f_id: feature.default_enabled 
                                  for f_id, feature in self._features.items()}
            
            # Clear Qt settings
            if self._qt_settings is not None:
                self._qt_settings.clear()
            
            logger.info("Settings reset to defaults")
    
    def get_resource_impact(self) -> int:
        """
        Calculate the current resource impact of enabled features.
        
        Returns:
            Sum of resource impact values for enabled features (0-100 scale)
        """
        with self._lock:
            impact = 0
            
            for feature_id, enabled in self._feature_states.items():
                if enabled and feature_id in self._features:
                    impact += self._features[feature_id].resource_impact
            
            return impact


# Create singleton instance
settings_manager = SettingsManager() 