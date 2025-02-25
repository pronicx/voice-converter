import pyaudio
import wave
import time
import io
import subprocess
import os
import numpy as np
from io import BytesIO
from elevenlabs import play
from voice_converter import config
import sys

class AudioManager:
    def __init__(self, settings_manager=None):
        self.p = pyaudio.PyAudio()
        self.settings_manager = settings_manager
        self.available_devices = self.get_available_devices()
        
        # Initialize stream attribute
        self.stream = None
        self.recording_callback = None
        
        # Load saved settings if available
        self.volume = config.DEFAULT_VOLUME
        self.input_device = None
        self.output_device = None
        self.silence_threshold = config.DEFAULT_SILENCE_THRESHOLD
        
        if settings_manager:
            self.volume = settings_manager.get("volume", config.DEFAULT_VOLUME)
            self.silence_threshold = settings_manager.get("silence_threshold", config.DEFAULT_SILENCE_THRESHOLD)
            
            # Try to set input device
            input_device = settings_manager.get("input_device")
            if input_device is not None and input_device in self.available_devices['input'].keys():
                self.input_device = input_device
            
            # Try to set output device
            output_device = settings_manager.get("output_device")
            if output_device is not None and output_device in self.available_devices['output'].keys():
                self.output_device = output_device
    
    def get_available_devices(self):
        """Get all available audio devices"""
        devices = {
            'input': {},
            'output': {}
        }
        
        info = self.p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = self.p.get_device_info_by_index(i)
            device_name = device_info.get('name')
            
            if device_info.get('maxInputChannels') > 0:
                devices['input'][i] = device_name
                
            if device_info.get('maxOutputChannels') > 0:
                devices['output'][i] = device_name
                
        return devices

    def set_input_device(self, device_idx):
        """Set the input device to use"""
        try:
            device_idx = int(device_idx)  # Ensure it's an integer
            if device_idx in self.available_devices['input']:
                # Get device info to verify it's valid
                device_info = self.p.get_device_info_by_index(device_idx)
                if device_info and device_info.get('maxInputChannels') > 0:
                    self.input_device = device_idx
                    print(f"Input device set to: {device_info['name']}")
                    if self.settings_manager:
                        self.settings_manager.set("input_device", device_idx)
                    return True
            return False
        except Exception as e:
            print(f"Error setting input device: {e}")
            return False
    
    def set_output_device(self, device_idx):
        """Set the output device to use"""
        try:
            device_idx = int(device_idx)  # Ensure it's an integer
            if device_idx in self.available_devices['output']:
                # Get device info to verify it's valid
                device_info = self.p.get_device_info_by_index(device_idx)
                if device_info and device_info.get('maxOutputChannels') > 0:
                    self.output_device = device_idx
                    print(f"Output device set to: {device_info['name']}")
                    if self.settings_manager:
                        self.settings_manager.set("output_device", device_idx)
                    return True
            return False
        except Exception as e:
            print(f"Error setting output device: {e}")
            return False
    
    def set_volume(self, volume):
        """Set the output volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        # Einstellung speichern
        if self.settings_manager:
            self.settings_manager.set("volume", self.volume)
    
    def record_to_file(self, frames):
        """Convert frames to an in-memory audio file"""
        in_memory_wav = BytesIO()
        
        wf = wave.open(in_memory_wav, 'wb')
        wf.setnchannels(config.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(config.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        # Reset buffer position to the beginning
        in_memory_wav.seek(0)
        return in_memory_wav
    
    def play_audio(self, audio_data):
        """Play audio data through the system
        
        Args:
            audio_data: Audio data in MP3 format
        """
        try:
            # Cleanup old temp files periodically
            self.cleanup_temp_files()
            
            # Fehlendes Volumen-Adjustment hinzufügen
            ffmpeg_cmd = ["ffmpeg", "-y", "-i", "-"]
            
            # Apply volume adjustment
            ffmpeg_cmd.extend(["-af", f"volume={self.volume}"])
            
            # Output device selection (vereinfacht)
            if self.output_device is not None:
                try:
                    # Direktes Abspielen über PyAudio ohne FFmpeg
                    return self.play_audio_with_pyaudio(audio_data)
                except Exception as e:
                    print(f"Error with PyAudio playback: {e}")
                    # Fallback to FFmpeg
            
            # Fallback: Use elevenlabs play function
            print("Using elevenlabs play function as fallback")
            play(audio_data)
            
        except Exception as e:
            print(f"Error playing audio: {e}")
            # Final fallback
            play(audio_data)

    def play_audio_with_pyaudio(self, audio_data):
        """Play audio using PyAudio directly with selected output device"""
        # Speichere Audio in temporäre Datei
        temp_dir = os.path.join(os.path.expanduser("~"), "elevenlabs_temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_file = os.path.join(temp_dir, f"output_{time.time()}.mp3")
        
        with open(temp_file, "wb") as f:
            f.write(audio_data)
        
        # Konvertiere MP3 zu WAV mit FFmpeg für einfacheres Abspielen
        wav_file = os.path.join(temp_dir, f"output_{time.time()}.wav")
        
        # Einfaches Konvertieren ohne Gerätespezifikation
        subprocess.run([
            "ffmpeg", "-y", "-i", temp_file, 
            "-af", f"volume={self.volume}", 
            "-hide_banner", "-loglevel", "error",
            wav_file
        ], check=True)
        
        # WAV-Datei mit PyAudio abspielen
        wf = wave.open(wav_file, 'rb')
        
        # Öffne Stream mit dem ausgewählten Ausgabegerät
        stream = self.p.open(
            format=self.p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
            output_device_index=self.output_device
        )
        
        # Lese und spiele Daten
        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)
        
        # Aufräumen
        stream.stop_stream()
        stream.close()
        
        # Temporäre Dateien löschen
        try:
            os.remove(temp_file)
            os.remove(wav_file)
        except:
            pass
        
        return True
    
    def __del__(self):
        if hasattr(self, 'p'):
            self.p.terminate()

    def start_recording(self, callback=None):
        """Start recording audio from the microphone
        
        Args:
            callback: function to call with audio frames when speech ends
            
        Returns:
            bool: True if recording started successfully
        """
        if self.stream:
            print("Already recording")
            return False
        
        try:
            # Store the callback for use in the audio thread
            self.recording_callback = callback
            
            # Set up a new stream for recording
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                input_device_index=self.input_device,
                frames_per_buffer=1024,
                stream_callback=self._audio_callback
            )
            
            # Initialize speech detection variables
            self.frames_buffer = []
            self.is_speech_active = False
            self.silence_frames = 0
            self.speech_start_time = time.time()
            self.last_process_time = time.time()
            
            print("Recording started")
            return True
        except Exception as e:
            print(f"Error starting recording: {e}")
            return False

    def stop_recording(self):
        """Stop recording audio"""
        if not hasattr(self, 'stream') or self.stream is None:
            print("Not recording")
            return False
        
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.recording_callback = None
            print("Recording stopped")
            return True
        except Exception as e:
            print(f"Error stopping recording: {e}")
            # Still set stream to None to clean up
            self.stream = None
            return False

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for processing audio data from the microphone"""
        try:
            # Process the incoming audio data
            audio_data = in_data
            
            # Add to buffer
            self.frames_buffer.append(audio_data)
            
            # Simple speech detection based on amplitude
            is_silence = self._is_silence(audio_data)
            current_time = time.time()
            
            if not is_silence:
                # Reset silence counter when speech is detected
                self.silence_frames = 0
                
                if not self.is_speech_active:
                    # Speech just started
                    self.is_speech_active = True
                    self.speech_start_time = current_time
                    print("Speech detected")
            else:
                # Count consecutive silence frames
                self.silence_frames += 1
                
                # If we've had enough silence, consider speech ended
                if self.is_speech_active:
                    # Längere Stille (15 frames, ~300ms) für bessere Sprachsegmentierung
                    if self.silence_frames >= 15:  
                        print("Speech segment ended")
                        # Send the buffered frames to the callback
                        if self.recording_callback and self.frames_buffer:
                            self.recording_callback(self.frames_buffer)
                        
                        # Reset buffer and state
                        self.frames_buffer = []
                        self.is_speech_active = False
                    # Erhöhe die maximale Sprechdauer auf 5 Sekunden für natürlichere Pausen
                    elif current_time - self.speech_start_time >= 5.0:
                        print("Maximum speech segment duration reached")
                        if self.recording_callback and self.frames_buffer:
                            self.recording_callback(self.frames_buffer)
                        self.frames_buffer = []
                        self.is_speech_active = False
            
            # Continue processing
            return (None, pyaudio.paContinue)
        except Exception as e:
            print(f"Error in audio callback: {e}")
            return (None, pyaudio.paContinue)

    def _is_silence(self, audio_data):
        """Check if audio data is silence based on amplitude threshold"""
        if not audio_data:
            return True
        
        try:
            # Convert to numpy array for easier processing
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Check if array is empty or contains only zeros
            if len(audio_array) == 0 or np.all(audio_array == 0):
                return True
            
            # Calculate RMS amplitude
            amplitude = np.sqrt(np.mean(np.square(audio_array.astype(float))))
            
            # Check against threshold (default to 200 if not set)
            threshold = getattr(self, 'silence_threshold', 200)
            return amplitude < threshold
        except Exception as e:
            print(f"Error analyzing audio: {e}")
            return True  # Treat as silence in case of error

    def set_silence_threshold(self, threshold):
        """Set the silence threshold value"""
        self.silence_threshold = threshold
        if self.settings_manager:
            self.settings_manager.set("silence_threshold", threshold)

    def cleanup_temp_files(self):
        """Clean up old temporary audio files"""
        try:
            temp_dir = os.path.join(os.path.expanduser("~"), "elevenlabs_temp")
            if not os.path.exists(temp_dir):
                return
            
            # Delete temporary files older than 10 minutes
            current_time = time.time()
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                # Check if it's a file (not a subdirectory)
                if os.path.isfile(file_path):
                    # Check if the file is older than 10 minutes
                    if current_time - os.path.getctime(file_path) > 600:  # 600 seconds = 10 minutes
                        os.remove(file_path)
                        print(f"Old temporary file deleted: {filename}")
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}") 