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

    # ... rest of the AudioManager implementation ...
    # Add other methods from the original file here 