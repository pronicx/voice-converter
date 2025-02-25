import tkinter as tk
import threading
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from audio_manager import AudioManager
from api_client import ElevenLabsClient
from voice_converter import VoiceConverter
from gui import VoiceConverterGUI
from settings_manager import SettingsManager

def main():
    # Initialize settings manager first
    settings_manager = SettingsManager()
    
    # Initialize components with settings
    audio_manager = AudioManager(settings_manager)
    api_client = ElevenLabsClient(settings_manager)
    voice_converter = VoiceConverter(audio_manager, api_client, settings_manager)
    
    # Create and start the GUI
    root = tk.Tk()
    root.title("Voice Converter")
    
    # Set application icon if available
    try:
        if os.path.exists("icon.ico"):
            root.iconbitmap("icon.ico")
    except:
        pass  # Ignore icon errors
    
    # Initialize GUI
    app = VoiceConverterGUI(root, audio_manager, api_client, voice_converter)
    
    # Set up clean shutdown
    def on_closing():
        if hasattr(app, 'is_recording') and app.is_recording:
            voice_converter.stop_recording()
        # Save settings before closing
        settings_manager.save_settings()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    main() 