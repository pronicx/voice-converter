import tkinter as tk
from tkinter import ttk
from voice_converter import config

class MainTabComponent:
    def __init__(self, parent, audio_manager, api_client, voice_converter, status_bar, toggle_recording_callback):
        self.parent = parent
        self.audio_manager = audio_manager
        self.api_client = api_client
        self.voice_converter = voice_converter
        self.status_bar = status_bar
        self.toggle_recording_callback = toggle_recording_callback
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the main control elements"""
        # Main controls frame
        controls_frame = ttk.LabelFrame(self.parent, text="Controls", padding=10)
        controls_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Voice selection
        ttk.Label(controls_frame, text="Voice:").grid(column=0, row=0, sticky=tk.W, pady=5)
        self.voice_combobox = ttk.Combobox(controls_frame, state="readonly", width=30)
        self.voice_combobox.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5)
        self.voice_combobox.bind("<<ComboboxSelected>>", self.select_voice)
        
        # Language selection
        ttk.Label(controls_frame, text="Language:").grid(column=0, row=1, sticky=tk.W, pady=5)
        self.language_combobox = ttk.Combobox(controls_frame, state="readonly", width=30)
        self.language_combobox.grid(column=1, row=1, sticky=tk.W, padx=5, pady=5)
        self.language_combobox.bind("<<ComboboxSelected>>", self.select_language)
        
        # Set initial language options
        language_names = sorted(config.LANGUAGES.keys())
        self.language_combobox['values'] = language_names
        
        # Set the language from settings if available
        if self.voice_converter and self.voice_converter.language_code:
            # Find language name for the saved code
            for lang_name, lang_code in config.LANGUAGES.items():
                if lang_code == self.voice_converter.language_code:
                    self.language_combobox.set(lang_name)
                    break
            else:
                # Default to first language if no match
                if language_names:
                    self.language_combobox.current(0)
        elif language_names:
            # Default to first language if no saved setting
            self.language_combobox.current(0)
        
        # Volume slider
        ttk.Label(controls_frame, text="Volume:").grid(column=0, row=2, sticky=tk.W, pady=5)
        self.volume_frame = ttk.Frame(controls_frame)
        self.volume_frame.grid(column=1, row=2, sticky=tk.W, padx=5, pady=5)
        
        self.volume_slider = ttk.Scale(
            self.volume_frame, 
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL, 
            length=200,
            command=self.on_volume_change
        )
        self.volume_slider.pack(side=tk.LEFT)
        
        # Current volume percentage
        self.volume_label = ttk.Label(self.volume_frame, text="50%")
        self.volume_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Set initial volume
        initial_volume = self.audio_manager.volume * 100
        self.volume_slider.set(initial_volume)
        self.update_volume_label(initial_volume)
        
        # Recording indicator and button frame
        record_frame = ttk.Frame(controls_frame)
        record_frame.grid(column=1, row=3, sticky=tk.W, padx=5, pady=15)
        
        # Recording indicator (red circle)
        self.canvas = tk.Canvas(record_frame, width=20, height=20)
        self.canvas.pack(side=tk.LEFT, padx=(0, 10))
        self.recording_indicator = self.canvas.create_oval(5, 5, 15, 15, fill="red")
        
        # Recording button
        self.record_button = ttk.Button(
            record_frame, 
            text="Start Recording", 
            command=self.toggle_recording
        )
        self.record_button.pack(side=tk.LEFT)
        
        # Initially hide the red indicator
        self.set_recording_state(False)

    def update_volume_label(self, value):
        """Update the volume percentage label"""
        try:
            # Handle float values that might be passed as strings
            if isinstance(value, str):
                value = float(value)
            self.volume_label.config(text=f"{int(value)}%")
        except ValueError:
            # If conversion fails, just display the raw value
            self.volume_label.config(text=f"{value}%")

    def on_volume_change(self, value):
        """Handle volume slider changes"""
        volume = float(value) / 100
        self.audio_manager.set_volume(volume)
        self.update_volume_label(value)

    def set_recording_state(self, is_recording):
        """Update UI elements based on recording state"""
        if is_recording:
            self.record_button.config(text="Stop Recording")
            self.canvas.itemconfig(self.recording_indicator, state="normal")
        else:
            self.record_button.config(text="Start Recording")
            self.canvas.itemconfig(self.recording_indicator, state="hidden")

    def select_voice(self, event=None):
        """Handle voice selection from dropdown"""
        selected_voice = self.voice_combobox.get()
        if selected_voice and hasattr(self, 'voices') and selected_voice in self.voices:
            voice_id = self.voices[selected_voice]
            
            # Update the voice converter with the selected voice
            if self.voice_converter:
                self.voice_converter.set_voice(voice_id)
                print(f"Selected voice: {selected_voice} (ID: {voice_id})")
            else:
                print("Warning: Voice converter not available")
        else:
            print(f"Warning: Voice '{selected_voice}' not found in available voices")

    def select_language(self, event=None):
        """Handle language selection from dropdown"""
        selected_language_name = self.language_combobox.get()
        if selected_language_name in config.LANGUAGES:
            language_code = config.LANGUAGES[selected_language_name]
            
            # Update voice converter with selected language
            if self.voice_converter:
                self.voice_converter.language_code = language_code
                # Save to settings if available through the voice converter
                if self.voice_converter.settings_manager:
                    self.voice_converter.settings_manager.set("language_code", language_code)
                    
                print(f"Selected language: {selected_language_name} (Code: {language_code})")
                self.status_bar.set_status(f"Language set to {selected_language_name}")
            else:
                print("Warning: Voice converter not available for language selection")
        else:
            print(f"Warning: Language '{selected_language_name}' not found in available languages")

    def toggle_recording(self):
        """Toggle recording state by calling the parent callback"""
        self.toggle_recording_callback()

    def update_voices(self, voices):
        """Update the voice combobox with available voices
        
        Args:
            voices (dict): Dictionary of voice names to voice IDs
        """
        if not voices:
            print("Warning: No voices available to display in dropdown")
            return
        
        # Clear existing values
        self.voice_combobox['values'] = []
        
        # Set new values from the voices dictionary
        voice_names = sorted(voices.keys())
        self.voice_combobox['values'] = voice_names
        
        # Store the voice dictionary for later reference
        self.voices = voices
        
        # If there are voices, select the first one by default
        if voice_names:
            self.voice_combobox.current(0)
            # Update the voice in the voice converter
            selected_voice = voice_names[0]
            voice_id = voices[selected_voice]
            self.voice_converter.set_voice(voice_id)
        
        print(f"Updated voice dropdown with {len(voice_names)} options") 