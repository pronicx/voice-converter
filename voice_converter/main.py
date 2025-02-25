import tkinter as tk
import sys
import os

# Add project root to path so package can be run from any directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from voice_converter.audio.audio_manager import AudioManager
from voice_converter.api.elevenlabs_client import ElevenLabsClient
from voice_converter.utils.settings_manager import SettingsManager
from voice_converter.gui.gui import VoiceConverterGUI
from voice_converter.voice_converter import VoiceConverter

def main():
    # Initialize settings manager
    settings_manager = SettingsManager()
    
    # Initialize audio manager
    audio_manager = AudioManager(settings_manager)
    
    # Initialize API client
    api_client = ElevenLabsClient(settings_manager)
    
    # Initialize voice converter
    voice_converter = VoiceConverter(audio_manager, api_client, settings_manager)
    
    # Set up GUI
    root = tk.Tk()
    app = VoiceConverterGUI(root, audio_manager, api_client, voice_converter)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main() 