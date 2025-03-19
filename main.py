#!/usr/bin/env python3
"""
Main entry point for the Jarvis assistant.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Add the jarvis directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jarvis.core.app_controller import app_controller
from jarvis.brain.model_manager import model_manager
from jarvis.brain.ollama_service import ollama_service
from jarvis.brain.language_model_service import language_model_service
from jarvis.brain.langchain_service import langchain_service
from jarvis.config.settings_manager import settings_manager
from jarvis.core.assistant import jarvis
from jarvis.context.context_manager import context_manager
from jarvis.tools.system_tools import register_system_tools
from jarvis.tools.file_tools import register_file_tools
from jarvis.tools.web_tools import register_web_tools
from jarvis.utils.config import config_manager
from jarvis.config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / ".jarvis" / "jarvis.log")
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Jarvis AI Assistant")
    parser.add_argument(
        "--interactive", "-i", 
        action="store_true", 
        help="Start in interactive mode"
    )
    parser.add_argument(
        "--command", "-c", 
        type=str, 
        help="Execute a single command and exit"
    )
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Start in daemon mode (for desktop app)"
    )
    return parser.parse_args()

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
    
    # Register LangChain service (depends on language model service)
    app_controller.register_service(
        "langchain_service",
        langchain_service,
        dependencies=["language_model_service"]
    )
    
    # Register context manager service
    app_controller.register_service(
        "context_manager",
        context_manager,
        dependencies=["settings_manager"]
    )
    
    # Register core assistant (depends on language model service, langchain service, and context manager)
    app_controller.register_service(
        "jarvis_assistant",
        jarvis,
        dependencies=["language_model_service", "langchain_service", "context_manager"]
    )
    
    logger.info("Core services registered")

def register_tools():
    """Register tools with the LangChain service."""
    logger.info("Registering tools...")
    
    # Make sure LangChain service is active
    if not langchain_service.active:
        langchain_service.start()
    
    # Register system tools
    register_system_tools()
    
    # Register file tools
    register_file_tools()
    
    # Register web tools
    register_web_tools()
    
    logger.info("Tools registered")

def interactive_mode():
    """Run Jarvis in interactive text mode."""
    print(f"🤖 {settings.ASSISTANT_NAME} Assistant is ready. Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input("\nYou: ")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print(f"\n{settings.ASSISTANT_NAME}: Goodbye!")
                break
            
            # Process the user's command
            response = jarvis.process_command(user_input)
            print(f"\n{settings.ASSISTANT_NAME}: {response}")
            
        except KeyboardInterrupt:
            print(f"\n{settings.ASSISTANT_NAME}: Interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {str(e)}")
            print(f"\n{settings.ASSISTANT_NAME}: I encountered an error: {str(e)}")

def daemon_mode():
    """Run Jarvis as a daemon for the desktop app."""
    logger.info("Starting Jarvis in daemon mode")
    
    # The application controller will keep services running
    # Just wait for shutdown signal
    app_controller.wait_for_shutdown()
    
    logger.info("Jarvis daemon stopping")

def main():
    """Main entry point for the application."""
    # Create logs directory if it doesn't exist
    logs_dir = Path.home() / ".jarvis"
    logs_dir.mkdir(exist_ok=True)
    
    # Parse command line arguments
    args = parse_arguments()
    
    try:
        # Register services
        register_services()
        
        # Start the application controller
        app_controller.start()
        
        # Register tools
        register_tools()
        
        # Validate configuration
        if not config_manager.validate_all():
            logger.error("Configuration validation failed. Please check your settings.")
            app_controller.stop()
            sys.exit(1)
        
        if args.daemon:
            # Run in daemon mode for desktop app
            daemon_mode()
        elif args.command:
            # Execute a single command
            response = jarvis.process_command(args.command)
            print(f"{settings.ASSISTANT_NAME}: {response}")
        else:
            # Start interactive mode
            interactive_mode()
        
        # Stop the application controller
        app_controller.stop()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"Error: {str(e)}")
        
        # Ensure application controller is stopped
        try:
            app_controller.stop()
        except Exception:
            pass
            
        sys.exit(1)

if __name__ == "__main__":
    main()
