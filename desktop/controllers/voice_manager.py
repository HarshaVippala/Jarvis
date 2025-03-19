"""
Voice Manager for handling speech input and output.
"""
import os
import sys
import time
import threading
import tempfile
import logging
from pathlib import Path
import queue
import wave
import base64
import json
import subprocess

from PySide6.QtCore import QObject, Signal, QSettings, QTimer
import pyaudio
import numpy as np
import openai
from openai import OpenAI

from jarvis.core.events import event_bus, EventType

class VoiceManager(QObject):
    """Manager for handling voice input and output."""
    
    # Define signals
    listening_started = Signal()
    listening_stopped = Signal()
    processing_started = Signal()
    processing_stopped = Signal()
    transcription_received = Signal(str)
    error_occurred = Signal(str)
    api_usage_updated = Signal(int, float)  # tokens, cost
    
    def __init__(self, parent=None):
        """Initialize the voice manager."""
        super().__init__(parent)
        
        # Initialize properties
        self.settings = QSettings("Jarvis", "JarvisDesktop")
        self.is_listening = False
        self.is_processing = False
        self.listening_thread = None
        self.audio_queue = queue.Queue()
        
        # Audio settings
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk_size = 1024
        self.audio = pyaudio.PyAudio()
        
        # Create the audio stream
        self.stream = None
        
        # Initialize OpenAI client for Whisper API
        self.openai_api_key = self.settings.value("jarvis/openai_api_key", "")
        if not self.openai_api_key:
            # Use the one from settings.py as fallback
            from jarvis.config import settings as jarvis_settings
            self.openai_api_key = jarvis_settings.OPENAI_API_KEY
        
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Voice settings
        self.tts_enabled = self.settings.value("jarvis/tts_enabled", True, type=bool)
        self.voice_type = self.settings.value("jarvis/voice_type", "alloy", type=str)
        
        # Available OpenAI voices
        self.available_voices = {
            "alloy": "Neutral",
            "echo": "Male",
            "fable": "Female",
            "onyx": "Male, deep",
            "nova": "Female, warm",
            "shimmer": "Female, clear"
        }
        
        # Initialize API cost tracking
        # Current pricing for Whisper API (as of this writing)
        self.whisper_cost_per_minute = 0.006  # $0.006 per minute
        self.tts_cost_per_1k_chars = 0.015  # $0.015 per 1,000 characters
        
        # Initialize ElevenLabs if key is available (for future implementation)
        self.elevenlabs_api_key = self.settings.value("jarvis/elevenlabs_api_key", "")
        self.elevenlabs_client = None  # Will be initialized later
        
        # Create streaming buffer for TTS
        self.text_buffer = []
        self.is_speaking = False
        self.speak_thread = None
        
        # Listen for streaming text events
        event_bus.on(EventType.STREAMING_RESPONSE, self._on_streaming_text)
    
    def toggle_listening(self):
        """Toggle between listening and idle states."""
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        """Start listening for voice input."""
        if self.is_listening:
            return
        
        # Update state
        self.is_listening = True
        
        # Emit signal
        self.listening_started.emit()
        
        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            # Start the stream
            self.stream.start_stream()
            
            # Start listening thread
            self.listening_thread = threading.Thread(
                target=self._process_audio,
                daemon=True
            )
            self.listening_thread.start()
            
        except Exception as e:
            self.error_occurred.emit(f"Error starting listening: {str(e)}")
            self.stop_listening()
    
    def stop_listening(self):
        """Stop listening for voice input."""
        if not self.is_listening:
            return
        
        # Update state
        self.is_listening = False
        
        # Emit signal
        self.listening_stopped.emit()
        
        # Stop the stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        # Clear the queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream."""
        # Push audio data to queue
        self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
    
    def _process_audio(self):
        """Process audio data from the queue."""
        audio_data = []
        
        try:
            # Collect audio for a few seconds
            start_time = time.time()
            silence_timeout = 1.0  # 1 second of silence to end listening
            last_sound_time = start_time
            has_sound = False
            
            while self.is_listening:
                try:
                    data = self.audio_queue.get(timeout=0.1)
                    audio_data.append(data)
                    
                    # Check for sound (very basic detection)
                    audio_array = np.frombuffer(data, dtype=np.int16)
                    if np.abs(audio_array).mean() > 500:  # Arbitrary threshold
                        has_sound = True
                        last_sound_time = time.time()
                    
                    # Check for silence timeout (only after some sound detected)
                    if has_sound and time.time() - last_sound_time > silence_timeout:
                        break
                        
                    # Also stop after a maximum time
                    if time.time() - start_time > 10.0:  # 10 seconds max
                        break
                        
                except queue.Empty:
                    continue
            
            # If we have audio data and detected sound, process it
            if audio_data and has_sound:
                self.process_transcription(audio_data)
                
        except Exception as e:
            self.error_occurred.emit(f"Error processing audio: {str(e)}")
        finally:
            # Stop listening after processing
            self.stop_listening()
    
    def process_transcription(self, audio_data):
        """Process the transcription of audio data using OpenAI Whisper API."""
        # Signal that we're processing
        self.is_processing = True
        self.processing_started.emit()
        
        try:
            # Save audio data to a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_filename = temp_audio.name
                
                # Create WAV file
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.audio.get_sample_size(self.format))
                    wf.setframerate(self.rate)
                    wf.writeframes(b''.join(audio_data))
                
                # Close the file to ensure it's written to disk
                temp_audio.close()
                
                # Calculate audio duration for cost tracking
                audio_duration_seconds = len(b''.join(audio_data)) / (self.rate * self.channels * self.audio.get_sample_size(self.format))
                audio_duration_minutes = audio_duration_seconds / 60.0
                
                # Calculate estimated cost
                estimated_cost = audio_duration_minutes * self.whisper_cost_per_minute
                
                # Send audio to Whisper API
                start_time = time.time()
                with open(temp_filename, "rb") as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-1",
                        language="en"
                    )
                
                # Extract the transcription text
                transcription = transcript.text
                
                # Send the transcription
                if transcription:
                    self.transcription_received.emit(transcription)
                    
                    # Log API usage
                    # Note: Whisper API doesn't currently provide token counts, 
                    # so we estimate based on audio duration
                    self.api_usage_updated.emit(int(audio_duration_seconds * 100), estimated_cost)
                    
                    # Log for debugging
                    logging.info(f"Whisper API: {audio_duration_seconds:.2f}s audio, est. cost: ${estimated_cost:.4f}")
                    
                else:
                    # If no transcription, emit an error
                    self.error_occurred.emit("No speech detected")
                    
                # Clean up the temporary file
                try:
                    os.unlink(temp_filename)
                except:
                    pass
            
        except Exception as e:
            self.error_occurred.emit(f"Error transcribing audio: {str(e)}")
        finally:
            # Signal that we're done processing
            self.is_processing = False
            self.processing_stopped.emit()
            
            # Automatically restart listening after speaking is complete
            # Use a timer to add a slight delay
            QTimer.singleShot(500, self.start_listening)
    
    def speak(self, text):
        """Convert text to speech and play it using OpenAI's TTS API."""
        if not text or not self.tts_enabled:
            return
            
        try:
            # Signal that we're processing
            self.is_processing = True
            self.processing_started.emit()
            
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
                temp_filename = temp_audio.name
                
                # Calculate cost for tracking (approximate)
                char_count = len(text)
                estimated_cost = (char_count / 1000) * self.tts_cost_per_1k_chars
                
                # Generate speech using OpenAI's TTS API
                response = self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice=self.voice_type,  # Use the selected voice
                    input=text
                )
                
                # Save the audio to the temporary file
                response.stream_to_file(temp_filename)
                
                # Close the file to ensure it's written to disk
                temp_audio.close()
                
                # Track API usage
                self.api_usage_updated.emit(char_count, estimated_cost)
                
                # Log for debugging
                logging.info(f"TTS API: {char_count} chars, est. cost: ${estimated_cost:.4f}")
                
                # Play the audio
                self._play_audio(temp_filename)
                
                # Clean up the temporary file
                try:
                    os.unlink(temp_filename)
                except:
                    pass
                    
        except Exception as e:
            self.error_occurred.emit(f"Error generating speech: {str(e)}")
        finally:
            # Signal that we're done processing
            self.is_processing = False
            self.processing_stopped.emit()
            
            # Automatically restart listening after speaking is complete
            # Use a timer to add a slight delay
            QTimer.singleShot(500, self.start_listening)
            
    def _on_streaming_text(self, text_chunk):
        """Handle streaming text chunks."""
        if not self.tts_enabled:
            return
            
        # Add to buffer
        self.text_buffer.append(text_chunk)
        
        # Start speaking if not already
        if not self.is_speaking:
            self.is_speaking = True
            
            # Start a thread to process the buffer
            self.speak_thread = threading.Thread(
                target=self._process_speech_buffer,
                daemon=True
            )
            self.speak_thread.start()
    
    def _process_speech_buffer(self):
        """Process text buffer for streaming speech."""
        try:
            # Signal that we're processing
            self.is_processing = True
            self.processing_started.emit()
            
            # Collect chunks until we have enough for a sentence
            full_text = ""
            sentence_end_markers = ['.', '!', '?', '\n']
            
            while self.is_speaking:
                # Process any available chunks
                while self.text_buffer:
                    chunk = self.text_buffer.pop(0)
                    full_text += chunk
                
                # Check if we have a complete sentence
                if full_text and any(marker in full_text for marker in sentence_end_markers):
                    # Create a temporary file for the audio
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
                        temp_filename = temp_audio.name
                        
                        # Calculate cost
                        char_count = len(full_text)
                        estimated_cost = (char_count / 1000) * self.tts_cost_per_1k_chars
                        
                        # Generate speech
                        response = self.openai_client.audio.speech.create(
                            model="tts-1",
                            voice=self.voice_type,
                            input=full_text
                        )
                        
                        # Save the audio
                        response.stream_to_file(temp_filename)
                        
                        # Close the file
                        temp_audio.close()
                        
                        # Track API usage
                        self.api_usage_updated.emit(char_count, estimated_cost)
                        
                        # Log for debugging
                        logging.info(f"Streaming TTS: {char_count} chars, est. cost: ${estimated_cost:.4f}")
                        
                        # Play the audio
                        self._play_audio(temp_filename)
                        
                        # Clean up
                        try:
                            os.unlink(temp_filename)
                        except:
                            pass
                    
                    # Reset for next sentence
                    full_text = ""
                
                # Stop if no more data for a while
                if not self.text_buffer:
                    time.sleep(0.5)  # Wait for more data
                    if not self.text_buffer:
                        # If still no data after wait, assume we're done
                        break
            
            # Process any remaining text
            if full_text:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
                    temp_filename = temp_audio.name
                    
                    # Generate speech for remaining text
                    response = self.openai_client.audio.speech.create(
                        model="tts-1",
                        voice=self.voice_type,
                        input=full_text
                    )
                    
                    # Save and play
                    response.stream_to_file(temp_filename)
                    temp_audio.close()
                    self._play_audio(temp_filename)
                    
                    # Clean up
                    try:
                        os.unlink(temp_filename)
                    except:
                        pass
        
        except Exception as e:
            self.error_occurred.emit(f"Error in streaming speech: {str(e)}")
        finally:
            # Clean up
            self.is_speaking = False
            self.text_buffer = []
            
            # Signal that we're done
            self.is_processing = False
            self.processing_stopped.emit()
            
            # Restart listening
            QTimer.singleShot(500, self.start_listening)
    
    def _play_audio(self, audio_file):
        """Play an audio file using system's default audio player."""
        try:
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", audio_file], check=True)
            elif system == "Windows":
                from winsound import PlaySound, SND_FILENAME
                PlaySound(audio_file, SND_FILENAME)
            elif system == "Linux":
                subprocess.run(["aplay", audio_file], check=True)
            else:
                self.error_occurred.emit(f"Unsupported operating system: {system}")
        except Exception as e:
            self.error_occurred.emit(f"Error playing audio: {str(e)}")
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_listening()
        if self.audio:
            self.audio.terminate()
    
    def set_voice_type(self, voice_type):
        """Set the voice type for TTS."""
        if voice_type in self.available_voices:
            self.voice_type = voice_type
            self.settings.setValue("jarvis/voice_type", voice_type)
            
    def set_tts_enabled(self, enabled):
        """Enable or disable text-to-speech."""
        self.tts_enabled = enabled
        self.settings.setValue("jarvis/tts_enabled", enabled) 