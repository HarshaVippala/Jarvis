#!/usr/bin/env python3
"""
Test script to verify that the SoundDevice voice system is functioning properly.
This script initializes and tests the core audio recording functionality.
"""
import os
import sys
import time
import logging
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import sounddevice as sd
import numpy as np

# Configure logging before imports
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Now import from the speech module
try:
    from jarvis.speech import VoiceSystem, VoiceManager, USE_SOUNDDEVICE
    
    if USE_SOUNDDEVICE is not True:
        print("ERROR: SoundDevice backend is not being used. Test cannot continue.")
        sys.exit(1)
except ImportError as e:
    print(f"ERROR: Failed to import voice system: {e}")
    sys.exit(1)

def list_audio_devices():
    """List all available audio devices"""
    print("\n=== Available Audio Devices ===")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        is_input = "Yes" if device.get('max_input_channels', 0) > 0 else "No"
        is_default_input = "<-- DEFAULT INPUT" if i == sd.default.device[0] else ""
        print(f"{i}: {device['name']} (Input: {is_input}) {is_default_input}")

def test_basic_recording(duration=3):
    """Test basic audio recording using sounddevice directly"""
    print(f"\n=== Testing basic recording for {duration} seconds ===")
    
    # Device info
    device_id = sd.default.device[0]
    device_info = sd.query_devices(device_id, 'input')
    samplerate = int(device_info['default_samplerate'])
    channels = 1
    
    print(f"Recording from device {device_id}: {device_info['name']}")
    print(f"Sample rate: {samplerate} Hz, Channels: {channels}")
    
    # Record audio
    recording = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=channels,
        dtype='float32'
    )
    
    print("Recording...")
    sd.sleep(int(duration * 1000))
    sd.stop()
    
    # Analyze recording
    if recording is not None:
        print(f"Recording shape: {recording.shape}")
        print(f"Mean amplitude: {np.mean(np.abs(recording))}")
        print(f"Max amplitude: {np.max(np.abs(recording))}")
        
        if np.max(np.abs(recording)) < 0.01:
            print("WARNING: Very low audio levels detected. Microphone might not be working properly.")
    else:
        print("ERROR: Recording is None. Failed to capture audio.")

def test_voice_manager():
    """Test the VoiceManager component"""
    print("\n=== Testing VoiceManager ===")
    
    # Create voice manager
    vm = VoiceManager()
    
    # Define a simple callback
    def on_transcription(text):
        print(f"Transcription: {text}")
    
    # Capture audio
    print("Recording for 5 seconds, please speak...")
    vm.start_listening(on_transcription)
    
    # Wait for recording to complete
    time.sleep(5)
    
    # Stop listening
    vm.stop_listening()
    print("Recording stopped.")

def test_voice_system():
    """Test the full VoiceSystem"""
    print("\n=== Testing VoiceSystem ===")
    
    # Create voice system
    vs = VoiceSystem()
    
    # Try to initialize
    print("Initializing voice system...")
    vs.start()
    
    # Wait to ensure initialization completes
    time.sleep(2)
    
    if not vs.is_ready:
        print("Voice system is not ready after initialization.")
        return
    
    # Define a callback
    def on_transcription(text):
        print(f"Transcription: {text}")
    
    vs.on_transcription = on_transcription
    
    # Start listening
    print("Testing listening for 5 seconds, please speak...")
    vs.start_listening()
    
    # Wait for recording to complete
    time.sleep(5)
    
    # Stop listening
    vs.stop_listening()
    print("Listening stopped.")
    
    # Clean up
    vs.shutdown()
    print("Voice system shut down.")

def main():
    """Run all tests"""
    print("=== SoundDevice Voice System Test ===")
    
    # List audio devices
    list_audio_devices()
    
    # Test basic recording
    test_basic_recording()
    
    # Test voice manager
    test_voice_manager()
    
    # Test voice system
    test_voice_system()

if __name__ == "__main__":
    main() 