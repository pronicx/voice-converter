import tkinter as tk
from tkinter import ttk
import config

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
        
        # Set language from saved settings if available
        saved_language_code = self.voice_converter.language_code
        if saved_language_code:
            # Find the language name for the saved code
            for lang_name, lang_code in config.LANGUAGES.items():
                if lang_code == saved_language_code:
                    self.language_combobox.set(lang_name)
                    break
            else:
                # Default to English if saved language not found
                for i, lang in enumerate(language_names):
                    if lang == "English":
                        self.language_combobox.current(i)
                        break
        else:
            # Default to English
            for i, lang in enumerate(language_names):
                if lang == "English":
                    self.language_combobox.current(i)
                    break
        
        # Volume control
        ttk.Label(controls_frame, text="Volume:").grid(column=0, row=2, sticky=tk.W, pady=5)
        self.volume_var = tk.DoubleVar(value=self.audio_manager.volume * 100)
        self.volume_slider = ttk.Scale(
            controls_frame, 
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL,
            variable=self.volume_var,
            command=self.on_volume_change
        )
        self.volume_slider.grid(column=1, row=2, sticky=tk.EW, padx=5, pady=5)
        
        # Volume percentage label
        self.volume_label = ttk.Label(controls_frame, text=f"{int(self.volume_var.get())}%")
        self.volume_label.grid(column=2, row=2, sticky=tk.W, padx=5, pady=5)
        
        # Status indicator (colored circle)
        indicator_frame = ttk.Frame(controls_frame)
        indicator_frame.grid(column=0, row=4, columnspan=3, pady=15)
        
        self.status_indicator = tk.Canvas(indicator_frame, width=20, height=20)
        self.status_indicator.create_oval(5, 5, 15, 15, fill="red", tags="status_light")
        self.status_indicator.pack(side=tk.LEFT, padx=5)
        
        # Recording button
        self.record_button = ttk.Button(
            indicator_frame, 
            text="Start Recording", 
            command=self.toggle_recording_callback,
            state=tk.DISABLED  # Initially disabled until voices are loaded
        )
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        # Wenn beim Start ein Gerät ausgewählt ist, setzen wir es explizit
        if self.audio_manager.input_device is not None:
            print(f"Using input device index: {self.audio_manager.input_device}")
        
        if self.audio_manager.output_device is not None:
            print(f"Using output device index: {self.audio_manager.output_device}")
        
        # Set initial volume from saved settings
        volume_percentage = int(self.audio_manager.volume * 100)
        self.volume_var.set(volume_percentage)
        self.volume_label.config(text=f"{volume_percentage}%")
    
    def update_voices(self, voices):
        """Update the voice combobox with available voices"""
        self.voice_combobox['values'] = list(voices.keys())
        if voices:
            # Voice selection will be updated in VoiceConverterGUI.update_voices_ui
            self.record_button.config(state=tk.NORMAL)
    
    def select_voice(self, event):
        """Handle voice selection"""
        if not self.voice_combobox.get():
            return
        
        voice_name = self.voice_combobox.get()
        voice_id = self.api_client.get_voice(voice_name)
        
        if voice_id:
            self.voice_converter.set_voice(voice_id)
            self.status_bar.set_status(f"Voice set to: {voice_name}")
    
    def select_language(self, event):
        """Handle language selection"""
        language_name = self.language_combobox.get()
        language_code = config.LANGUAGES.get(language_name)
        
        if language_code:
            self.voice_converter.set_language(language_code)
            self.status_bar.set_status(f"Language set to: {language_name}")
    
    def on_volume_change(self, value):
        """Handle volume slider change"""
        volume = float(value) / 100.0
        self.audio_manager.set_volume(volume)
        self.volume_label.config(text=f"{int(float(value))}%")
        
    def set_recording_state(self, is_recording):
        """Update the UI to reflect the recording state"""
        if is_recording:
            self.record_button.config(text="Stop Recording")
            self.status_indicator.itemconfig("status_light", fill="green")
        else:
            self.record_button.config(text="Start Recording")
            self.status_indicator.itemconfig("status_light", fill="red") 