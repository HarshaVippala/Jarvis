#!/usr/bin/env python3
"""
Test script for the resource governor.
"""
import os
import sys
import time
import logging
from pathlib import Path

# Add the jarvis directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jarvis.core.app_controller import app_controller
from jarvis.core.resource_governor import resource_governor, SystemLoad
from jarvis.config.settings_manager import settings_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_resource_monitoring():
    """Test resource monitoring functionality."""
    print("Starting resource governor test...")
    
    # Register services
    app_controller.register_service(
        "settings_manager",
        settings_manager,
        dependencies=[]
    )
    
    app_controller.register_service(
        "resource_governor",
        resource_governor,
        dependencies=["settings_manager"]
    )
    
    # Start the application controller
    app_controller.start()
    
    # Register callbacks for different load levels
    def on_high_load():
        print("\n⚠️ HIGH LOAD DETECTED! System resources are constrained.")
        print(f"Resource status: {resource_governor.get_resource_status()}")
    
    def on_medium_load():
        print("\n🔶 MEDIUM LOAD DETECTED. Resource allocation adjusted.")
        print(f"Resource status: {resource_governor.get_resource_status()}")
    
    def on_low_load():
        print("\n✅ LOW LOAD DETECTED. Resources are available.")
        print(f"Resource status: {resource_governor.get_resource_status()}")
    
    resource_governor.register_callback(SystemLoad.HIGH, on_high_load)
    resource_governor.register_callback(SystemLoad.MEDIUM, on_medium_load)
    resource_governor.register_callback(SystemLoad.LOW, on_low_load)
    
    print("\nResource Governor initialized. Monitoring system resources...")
    print("Resource status:")
    print(f"CPU usage: {resource_governor.get_system_usage()[0]:.1f}%")
    print(f"Memory usage: {resource_governor.get_system_usage()[1]:.1f}%")
    print(f"Jarvis memory usage: {resource_governor.get_system_usage()[2]:.1f} MB")
    print(f"Current load level: {resource_governor.get_current_load()}")
    
    # Monitor for a while
    try:
        print("\nMonitoring for 60 seconds. Press Ctrl+C to stop...\n")
        for i in range(60):
            time.sleep(1)
            if i % 10 == 0:
                cpu, mem, jarvis_mem = resource_governor.get_system_usage()
                print(f"[{i}s] CPU: {cpu:.1f}%, Memory: {mem:.1f}%, Jarvis: {jarvis_mem:.1f}MB")
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    
    # Stop the application controller
    print("\nStopping resource governor...")
    app_controller.stop()
    
    print("Test completed.")

if __name__ == "__main__":
    test_resource_monitoring() 