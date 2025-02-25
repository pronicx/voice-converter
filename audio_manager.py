import pyaudio
import wave
import time
import io
import subprocess
import os
import numpy as np
from io import BytesIO
from elevenlabs import play
import config
import sys

class AudioManager:
    def __init__(self, settings_manager=None):
        self.p = pyaudio.PyAudio()
        self.settings_manager = settings_manager
        self.available_devices = self.get_available_devices()
        
        # Load saved settings if available
        self.volume = config.DEFAULT_VOLUME
        self.input_device = None
        self.output_device = None
        
        if settings_manager:
            self.volume = settings_manager.get("volume", config.DEFAULT_VOLUME)
            
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
        """Play audio data using the selected output device"""
        try:
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