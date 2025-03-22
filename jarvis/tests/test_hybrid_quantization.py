#!/usr/bin/env python3
"""
Test script for hybrid model quantization.
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
from jarvis.core.energy_manager import energy_manager, PowerState, PerformanceProfile
from jarvis.brain.hybrid_model_quantization import hybrid_model_quantizer, QuantizationLevel, ModelVariant
from jarvis.config.settings_manager import settings_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_hybrid_quantization():
    """Test hybrid model quantization functionality."""
    print("Starting hybrid model quantization test...")
    
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
    
    app_controller.register_service(
        "hybrid_model_quantizer",
        hybrid_model_quantizer,
        dependencies=["settings_manager"]
    )
    
    # Start the application controller
    app_controller.start()
    
    # Wait for services to initialize
    time.sleep(1)
    
    # Print information about available models and variants
    print("\n1. Registered model variants:")
    for base_model, variants in hybrid_model_quantizer._model_variants.items():
        print(f"\n  Base model: {base_model}")
        for variant in variants:
            print(f"  - {variant.model_id} (Quantization: {variant.quantization}, "
                 f"Size: {variant.size_mb}MB, "
                 f"Performance: {variant.performance_score}/10, "
                 f"Efficiency: {variant.efficiency_score}/10)")
    
    # Test variant selection
    print("\n2. Testing variant selection in different scenarios:")
    
    # Test different system states
    test_scenarios = [
        {
            "name": "Performance Mode (Plugged In, Low Load)",
            "power_state": PowerState.PLUGGED,
            "system_load": SystemLoad.LOW,
            "performance_profile": PerformanceProfile.PERFORMANCE,
            "available_memory_mb": 16000
        },
        {
            "name": "Battery Mode (On Battery, Medium Load)",
            "power_state": PowerState.BATTERY,
            "system_load": SystemLoad.MEDIUM,
            "performance_profile": PerformanceProfile.BALANCED,
            "available_memory_mb": 16000
        },
        {
            "name": "Power Saving Mode (Low Battery, High Load)",
            "power_state": PowerState.BATTERY,
            "system_load": SystemLoad.HIGH,
            "performance_profile": PerformanceProfile.EFFICIENCY,
            "available_memory_mb": 16000
        },
        {
            "name": "Constrained Memory Mode",
            "power_state": PowerState.PLUGGED,
            "system_load": SystemLoad.LOW,
            "performance_profile": PerformanceProfile.BALANCED,
            "available_memory_mb": 3000  # Very limited memory
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        for base_model in ["mistral-7b", "llama3-8b", "phi3-mini-3.8b", "tinyllama-1.1b"]:
            variant = hybrid_model_quantizer.select_optimal_variant(
                base_model=base_model,
                power_state=scenario["power_state"],
                system_load=scenario["system_load"],
                performance_profile=scenario["performance_profile"],
                available_memory_mb=scenario["available_memory_mb"]
            )
            
            if variant:
                print(f"  - {base_model}: Selected {variant.model_id} "
                     f"({variant.quantization}, {variant.size_mb}MB)")
            else:
                print(f"  - {base_model}: No suitable variant found")
    
    # Test Ollama integration
    print("\n3. Testing Ollama integration:")
    ollama_available = hybrid_model_quantizer.is_ollama_available()
    print(f"  Ollama available: {ollama_available}")
    
    if ollama_available:
        # Test Ollama model tags
        print("\n  Testing Ollama model tags:")
        for base_model, variants in hybrid_model_quantizer._model_variants.items():
            for variant in variants:
                ollama_tag = hybrid_model_quantizer.get_ollama_model_tag(variant)
                print(f"  - {variant.model_id} -> Ollama tag: {ollama_tag}")
        
        # Test model availability check (don't actually download)
        print("\n  (Not downloading any models in this test)")
    
    # Stop the application controller
    print("\nStopping hybrid model quantizer...")
    app_controller.stop()
    
    print("Test completed.")

if __name__ == "__main__":
    test_hybrid_quantization() 