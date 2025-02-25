import tkinter as tk
from tkinter import ttk
import threading
import time
import config
from gui_components.main_tab import MainTabComponent
from gui_components.settings_tab import SettingsTabComponent
from gui_components.status_bar import StatusBarComponent

class VoiceConverterGUI:
    def __init__(self, root, audio_manager, api_client, voice_converter):
        self.root = root
        self.audio_manager = audio_manager
        self.api_client = api_client
        self.voice_converter = voice_converter
        
        # Configure the root window
        self.root.title("Voice Converter")
        self.root.geometry("600x500")
        self.root.minsize(500, 400)
        
        # Set up the main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create title
        title_label = ttk.Label(self.main_frame, text="Voice Converter", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)
        
        # Create tabs
        self.tab_control = ttk.Notebook(self.main_frame)
        
        # Main controls tab
        self.main_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.main_tab, text="Main Controls")
        
        # Settings tab
        self.settings_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.settings_tab, text="Settings")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Status bar component
        self.status_bar = StatusBarComponent(self.root)
        
        # Recording state
        self.is_recording = False
        self.voices_loaded = False
        
        # Initialize tab components
        self.main_tab_component = MainTabComponent(
            self.main_tab, 
            self.audio_manager, 
            self.api_client, 
            self.voice_converter,
            self.status_bar,
            self.toggle_recording_callback
        )
        
        self.settings_tab_component = SettingsTabComponent(
            self.settings_tab,
            self.audio_manager,
            self.voice_converter,
            self.status_bar
        )
        
        # Fetch voices on startup in a separate thread
        threading.Thread(target=self.load_voices, daemon=True).start()
        
    def load_voices(self):
        """Load voices in a background thread"""
        # Check if API key is available
        api_key = self.api_client.settings_manager.get("api_key")
        if not api_key:
            self.status_bar.set_status("No API key found. Please enter your API key in the Settings tab.")
            # Auto-switch to settings tab
            self.tab_control.select(self.settings_tab)
            return
        
        self.status_bar.set_status("Loading voices...")
        voices, languages = self.api_client.get_voices()
        
        if voices:
            # Update UI on main thread
            self.root.after(0, lambda: self.update_voices_ui(voices, languages))
        else:
            self.status_bar.set_status("Error loading voices. Check your API key.")
    
    def update_voices_ui(self, voices, languages):
        """Update UI with voice data"""
        self.main_tab_component.update_voices(voices)
        
        # Set the voice from saved settings
        saved_voice_id = self.voice_converter.voice_id
        if saved_voice_id:
            # Find voice name for the saved ID
            for voice_name, voice_id in voices.items():
                if voice_id == saved_voice_id:
                    # Set the combobox to this voice
                    self.main_tab_component.voice_combobox.set(voice_name)
                    break
        
        self.voices_loaded = True
        self.status_bar.set_status("Voices loaded successfully")
    
    def toggle_recording_callback(self):
        """Toggle recording state"""
        if self.is_recording:
            # Stop recording
            self.voice_converter.stop_recording()
            self.main_tab_component.set_recording_state(False)
            self.status_bar.set_status("Recording stopped")
        else:
            # Start recording
            self.voice_converter.start_recording()
            self.main_tab_component.set_recording_state(True)
            self.status_bar.set_status("Recording in progress...")
        
        self.is_recording = not self.is_recording 