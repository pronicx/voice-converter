import tkinter as tk
from tkinter import ttk
import threading
import time

from voice_converter.gui.components.main_tab import MainTabComponent
from voice_converter.gui.components.settings_tab import SettingsTabComponent
from voice_converter.gui.components.status_bar import StatusBarComponent

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

        # ... rest of the implementation ...
        # Add remaining methods here

    def toggle_recording_callback(self):
        # Implementation
        pass 