"""
Application Controller for Jarvis

This module provides the central orchestration for the Jarvis application,
managing services, dependencies, and application lifecycle.
"""
import logging
import time
from typing import Dict, List, Optional, Type, TypeVar, Any
import threading
import signal
import sys

# Define a generic type for services
T = TypeVar('T')

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """
    Registry that maintains references to all active services
    and manages service discovery.
    """
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._initialized = False

    def register(self, service_name: str, service_instance: Any, 
                dependencies: Optional[List[str]] = None) -> None:
        """
        Register a service with the registry.
        
        Args:
            service_name: Unique identifier for the service
            service_instance: The service object
            dependencies: List of service names this service depends on
        """
        if service_name in self._services:
            logger.warning(f"Service {service_name} already registered, replacing")
            
        self._services[service_name] = service_instance
        self._dependencies[service_name] = dependencies or []
        logger.info(f"Registered service: {service_name}")

    def get_service(self, service_name: str) -> Any:
        """
        Get a service by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The service instance
            
        Raises:
            KeyError: If the service is not registered
        """
        if service_name not in self._services:
            raise KeyError(f"Service {service_name} not registered")
        return self._services[service_name]

    def get_service_names(self) -> List[str]:
        """Get the names of all registered services."""
        return list(self._services.keys())

    def has_service(self, service_name: str) -> bool:
        """Check if a service is registered."""
        return service_name in self._services

    def resolve_dependencies(self) -> List[str]:
        """
        Resolve service dependencies and return a list of services
        in the order they should be initialized.
        
        Returns:
            List of service names in initialization order
        """
        # Build a dependency graph
        dependency_graph = {svc: set(deps) for svc, deps in self._dependencies.items()}
        
        # Find services with no dependencies
        resolved = []
        unresolved = set(self._services.keys())
        
        while unresolved:
            # Find a service with all dependencies resolved
            resolvable = [svc for svc in unresolved 
                         if all(dep in resolved for dep in self._dependencies.get(svc, []))]
            
            if not resolvable:
                # Circular dependency or missing dependency
                logger.error(f"Could not resolve dependencies for: {unresolved}")
                raise ValueError(f"Circular or missing dependencies in services: {unresolved}")
            
            # Add the resolvable services to the resolved list
            resolved.extend(resolvable)
            unresolved -= set(resolvable)
            
        return resolved


class ApplicationController:
    """
    Central orchestrator for the Jarvis application.
    Manages services, dependencies, and application lifecycle.
    """
    def __init__(self):
        self._registry = ServiceRegistry()
        self._stop_event = threading.Event()
        self._running = False
        self._start_time = None
        
        # Set up signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def register_service(self, service_name: str, service_instance: Any, 
                        dependencies: Optional[List[str]] = None) -> None:
        """
        Register a service with the application.
        
        Args:
            service_name: Unique identifier for the service
            service_instance: The service object
            dependencies: List of service names this service depends on
        """
        self._registry.register(service_name, service_instance, dependencies)

    def get_service(self, service_name: str) -> Any:
        """
        Get a service by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The service instance
        """
        return self._registry.get_service(service_name)

    def start(self) -> None:
        """
        Start the application and all registered services.
        Services are started in dependency order.
        """
        if self._running:
            logger.warning("Application already running")
            return
        
        logger.info("Starting Jarvis application...")
        self._start_time = time.time()
        
        try:
            # Resolve dependencies to get initialization order
            service_init_order = self._registry.resolve_dependencies()
            
            # Initialize each service in order
            for service_name in service_init_order:
                service = self._registry.get_service(service_name)
                
                # Check if the service has a start method
                if hasattr(service, 'start') and callable(getattr(service, 'start')):
                    logger.info(f"Starting service: {service_name}")
                    service.start()
                else:
                    logger.info(f"Service {service_name} has no start method, skipping")
            
            self._running = True
            logger.info(f"Jarvis application started in {time.time() - self._start_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            self.stop()
            raise

    def stop(self) -> None:
        """
        Stop all services and shut down the application gracefully.
        Services are stopped in reverse dependency order.
        """
        if not self._running:
            logger.warning("Application not running")
            return
        
        logger.info("Stopping Jarvis application...")
        
        try:
            # Get services in reverse dependency order for proper shutdown
            service_shutdown_order = self._registry.resolve_dependencies()
            service_shutdown_order.reverse()
            
            # Stop each service in order
            for service_name in service_shutdown_order:
                service = self._registry.get_service(service_name)
                
                # Check if the service has a stop method
                if hasattr(service, 'stop') and callable(getattr(service, 'stop')):
                    logger.info(f"Stopping service: {service_name}")
                    try:
                        service.stop()
                    except Exception as e:
                        logger.error(f"Error stopping service {service_name}: {e}")
            
            self._running = False
            self._stop_event.set()
            
            if self._start_time:
                uptime = time.time() - self._start_time
                logger.info(f"Jarvis application stopped. Uptime: {uptime:.2f} seconds")
            else:
                logger.info("Jarvis application stopped.")
                
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
            raise

    def wait_for_shutdown(self) -> None:
        """
        Wait for the application to be stopped via signal or explicit stop call.
        """
        self._stop_event.wait()

    def _handle_signal(self, signum: int, frame) -> None:
        """
        Handle termination signals to gracefully shut down.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def is_running(self) -> bool:
        """Check if the application is running."""
        return self._running

    @property
    def registry(self) -> ServiceRegistry:
        """Get the service registry."""
        return self._registry


# Create a singleton instance of the ApplicationController
app_controller = ApplicationController() 