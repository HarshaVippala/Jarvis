#!/usr/bin/env python3
"""
Test script for the energy manager.
"""
import os
import sys
import time
import logging
from pathlib import Path

# Add the jarvis directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jarvis.core.app_controller import app_controller
from jarvis.core.resource_governor import resource_governor
from jarvis.core.energy_manager import energy_manager, PowerState, PerformanceProfile
from jarvis.config.settings_manager import settings_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_energy_management():
    """Test energy management functionality."""
    print("Starting energy manager test...")
    
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
    
    app_controller.register_service(
        "energy_manager",
        energy_manager,
        dependencies=["settings_manager", "resource_governor"]
    )
    
    # Start the application controller
    app_controller.start()
    
    # Register callbacks for different power states
    def on_battery():
        print("\n🔋 BATTERY POWER DETECTED! Adjusting for power efficiency.")
        print(f"Power status: {energy_manager.get_power_status()}")
    
    def on_plugged():
        print("\n🔌 AC POWER DETECTED. Optimizing for performance.")
        print(f"Power status: {energy_manager.get_power_status()}")
    
    energy_manager.register_callback(PowerState.BATTERY, on_battery)
    energy_manager.register_callback(PowerState.PLUGGED, on_plugged)
    
    # Test manual profile switching
    print("\nTesting manual performance profile switching:")
    
    print("\n1. Switching to PERFORMANCE profile...")
    energy_manager.set_performance_profile(PerformanceProfile.PERFORMANCE)
    time.sleep(1)
    print(f"Current profile: {energy_manager.get_performance_profile()}")
    
    print("\n2. Switching to BALANCED profile...")
    energy_manager.set_performance_profile(PerformanceProfile.BALANCED)
    time.sleep(1)
    print(f"Current profile: {energy_manager.get_performance_profile()}")
    
    print("\n3. Switching to EFFICIENCY profile...")
    energy_manager.set_performance_profile(PerformanceProfile.EFFICIENCY)
    time.sleep(1)
    print(f"Current profile: {energy_manager.get_performance_profile()}")
    
    # Display power status
    print("\nCurrent power status:")
    status = energy_manager.get_power_status()
    print(f"Power state: {status['power_state']}")
    print(f"Battery percentage: {status['battery_percentage']}%")
    
    if status['battery_time_left'] is not None:
        print(f"Battery time left: {status['battery_time_left']} minutes")
    elif status['power_state'] == PowerState.PLUGGED:
        print("Battery is charging")
    else:
        print("Battery time left: Unknown")
    
    print(f"Current performance profile: {status['performance_profile']}")
    
    # Monitor for a while
    try:
        print("\nMonitoring for 60 seconds. Press Ctrl+C to stop...\n")
        print("Power state will be checked every 30 seconds by default.")
        print("If you want to test power state changes, plug/unplug your device during this time.")
        
        for i in range(60):
            time.sleep(1)
            if i % 10 == 0:
                status = energy_manager.get_power_status()
                print(f"[{i}s] Power: {status['power_state']}, Battery: {status['battery_percentage']}%, Profile: {status['performance_profile']}")
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    
    # Stop the application controller
    print("\nStopping energy manager...")
    app_controller.stop()
    
    print("Test completed.")

if __name__ == "__main__":
    test_energy_management() 