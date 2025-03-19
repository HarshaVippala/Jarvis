#!/usr/bin/env python3
"""
Main entry point for the Jarvis desktop application.
"""
import os
import sys
import logging
import threading
import signal
import atexit
from pathlib import Path

# Add parent directory to path so we can import jarvis modules
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QIcon

from jarvis.desktop.ui.main_window import MainWindow
from jarvis.core.app_controller import app_controller
from jarvis.brain.model_manager import model_manager
from jarvis.brain.ollama_service import ollama_service
from jarvis.brain.language_model_service import language_model_service
from jarvis.config.settings_manager import settings_manager
from jarvis.core.assistant import jarvis
from jarvis.config import settings as jarvis_settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / ".jarvis" / "desktop.log")
    ]
)
logger = logging.getLogger(__name__)

# Global references for proper shutdown
app = None
main_window = None
check_timer = None

def register_services():
    """Register core services with the application controller."""
    logger.info("Registering core services...")
    
    # Register settings manager (no dependencies)
    app_controller.register_service(
        "settings_manager",
        settings_manager,
        dependencies=[]
    )
    
    # Register model manager (depends on settings)
    app_controller.register_service(
        "model_manager",
        model_manager,
        dependencies=["settings_manager"]
    )
    
    # Register Ollama service (depends on model manager)
    app_controller.register_service(
        "ollama_service",
        ollama_service,
        dependencies=["model_manager"]
    )
    
    # Register language model service (depends on Ollama and model manager)
    app_controller.register_service(
        "language_model_service",
        language_model_service,
        dependencies=["ollama_service", "model_manager"]
    )
    
    # Register core assistant (depends on language model service)
    app_controller.register_service(
        "jarvis_assistant",
        jarvis,
        dependencies=["language_model_service"]
    )
    
    logger.info("Core services registered")

def start_app_controller():
    """Start the application controller in a background thread."""
    app_controller.start()
    logger.info("Application controller started")

def shutdown_application():
    """Clean up resources and ensure proper shutdown."""
    global app, main_window, check_timer
    
    logger.info("Shutting down Jarvis...")
    
    # Stop any timers
    if check_timer is not None and check_timer.isActive():
        check_timer.stop()
    
    # Close main window
    if main_window is not None:
        main_window.close()
    
    # Stop app controller and all services
    try:
        if app_controller.is_running:
            logger.info("Stopping app controller...")
            app_controller.stop()
    except Exception as e:
        logger.error(f"Error stopping app controller: {e}")
    
    # Quit the application if it's still running
    if app is not None:
        try:
            app.quit()
        except Exception as e:
            logger.error(f"Error quitting application: {e}")
    
    logger.info("Shutdown complete")

def signal_handler(sig, frame):
    """Handle system signals for graceful shutdown."""
    logger.info(f"Received signal {sig}, shutting down...")
    shutdown_application()
    sys.exit(0)

def main():
    """Main entry point for the desktop application."""
    global app, main_window, check_timer
    
    try:
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Register shutdown function to be called at exit
        atexit.register(shutdown_application)
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Jarvis")
        app.setOrganizationName("JarvisAI")
        
        # Set application icon
        icon_path = Path(__file__).parent.parent / "jarvis.PNG"
        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
            app.setWindowIcon(app_icon)
        
        # Create settings for storing app state
        settings = QSettings()
        
        # Register and start services in a background thread
        threading.Thread(target=register_services, daemon=True).start()
        threading.Thread(target=start_app_controller, daemon=True).start()
        
        # Create main window
        main_window = MainWindow(settings)
        
        # Connect aboutToQuit signal to our shutdown function
        app.aboutToQuit.connect(shutdown_application)
        
        # Force ensure orb visibility after a delay
        def force_show_orb():
            print("Forcing orb to appear...")
            if hasattr(main_window, 'floating_orb') and main_window.floating_orb:
                # Move to center of screen
                main_window.floating_orb.moveToCenter()
                # Force show
                main_window.floating_orb.show()
                main_window.floating_orb.raise_()
                main_window.floating_orb.activateWindow()
                # Trigger again in case first attempt doesn't work
                QTimer.singleShot(1000, force_show_orb)
        
        # Call once right away and again after a short delay
        QTimer.singleShot(100, force_show_orb)
        QTimer.singleShot(500, force_show_orb)
        QTimer.singleShot(2000, force_show_orb)
        
        # Set up check for app controller status - notify user if backend is not ready
        def check_app_controller():
            if not app_controller.is_running:
                logger.warning("App controller not running...")
                # TODO: Show notification to the user that the backend is not ready
        
        # Check periodically
        check_timer = QTimer()
        check_timer.timeout.connect(check_app_controller)
        check_timer.start(5000)  # Check every 5 seconds
        
        # Start the application event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.exception(f"Fatal error in main: {str(e)}")
        # Ensure app controller is stopped
        shutdown_application()
        sys.exit(1)

if __name__ == "__main__":
    main() 