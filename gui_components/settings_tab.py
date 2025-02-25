import tkinter as tk
from tkinter import ttk

class SettingsTabComponent:
    def __init__(self, parent, audio_manager, voice_converter, status_bar):
        self.parent = parent
        self.audio_manager = audio_manager
        self.voice_converter = voice_converter
        self.status_bar = status_bar
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the settings tab elements"""
        settings_frame = ttk.LabelFrame(self.parent, text="Audio Settings", padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Audio input device selection
        ttk.Label(settings_frame, text="Input Device:").grid(column=0, row=0, sticky=tk.W, pady=5)
        
        self.input_devices = []
        input_device_map = {}  # To map display string to device index
        
        for idx, name in self.audio_manager.available_devices['input'].items():
            device_string = f"{idx}: {name}"
            self.input_devices.append(device_string)
            input_device_map[idx] = device_string
        
        self.input_combobox = ttk.Combobox(settings_frame, values=self.input_devices, state="readonly", width=40)
        if self.input_devices:
            # Select current device if set
            if self.audio_manager.input_device is not None and self.audio_manager.input_device in input_device_map:
                self.input_combobox.set(input_device_map[self.audio_manager.input_device])
            else:
                self.input_combobox.current(0)
        
        self.input_combobox.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5)
        self.input_combobox.bind("<<ComboboxSelected>>", self.select_input_device)
        
        # Audio output device selection
        ttk.Label(settings_frame, text="Output Device:").grid(column=0, row=1, sticky=tk.W, pady=5)
        
        self.output_devices = []
        output_device_map = {}  # To map display string to device index
        
        for idx, name in self.audio_manager.available_devices['output'].items():
            device_string = f"{idx}: {name}"
            self.output_devices.append(device_string)
            output_device_map[idx] = device_string
            
        self.output_combobox = ttk.Combobox(settings_frame, values=self.output_devices, state="readonly", width=40)
        if self.output_devices:
            # Select current device if set
            if self.audio_manager.output_device is not None and self.audio_manager.output_device in output_device_map:
                self.output_combobox.set(output_device_map[self.audio_manager.output_device])
            else:
                self.output_combobox.current(0)
        
        self.output_combobox.grid(column=1, row=1, sticky=tk.W, padx=5, pady=5)
        self.output_combobox.bind("<<ComboboxSelected>>", self.select_output_device)
        
        # Silence threshold
        ttk.Label(settings_frame, text="Silence Threshold:").grid(column=0, row=2, sticky=tk.W, pady=5)
        self.threshold_var = tk.IntVar(value=self.voice_converter.silence_threshold)
        self.threshold_slider = ttk.Scale(
            settings_frame, 
            from_=50, 
            to=2000, 
            orient=tk.HORIZONTAL,
            variable=self.threshold_var,
            command=self.on_threshold_change
        )
        self.threshold_slider.grid(column=1, row=2, sticky=tk.EW, padx=5, pady=5)
        
        # Threshold value label
        self.threshold_label = ttk.Label(settings_frame, text=str(self.threshold_var.get()))
        self.threshold_label.grid(column=2, row=2, sticky=tk.W, padx=5, pady=5)
        
        # Calibration button
        calibrate_frame = ttk.Frame(settings_frame)
        calibrate_frame.grid(column=0, row=3, columnspan=3, pady=15)
        
        self.calibrate_button = ttk.Button(
            calibrate_frame,
            text="Calibrate Microphone",
            command=self.calibrate_threshold
        )
        self.calibrate_button.pack(pady=10)
        
        # API settings section
        api_frame = ttk.LabelFrame(self.parent, text="API Settings", padding=10)
        api_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # API Key input
        ttk.Label(api_frame, text="ElevenLabs API Key:").grid(column=0, row=0, sticky=tk.W, pady=5)
        
        # Current API key or empty
        current_api_key = ""
        if hasattr(self.voice_converter, 'api_client') and hasattr(self.voice_converter.api_client, 'settings_manager'):
            current_api_key = self.voice_converter.api_client.settings_manager.get("api_key", "")
        
        self.api_key_var = tk.StringVar(value=current_api_key)
        self.api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=40, show="*")
        self.api_key_entry.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5)
        
        # Show/hide API key
        self.show_key = tk.BooleanVar(value=False)
        self.show_key_check = ttk.Checkbutton(
            api_frame, 
            text="Show API Key", 
            variable=self.show_key,
            command=self.toggle_api_key_visibility
        )
        self.show_key_check.grid(column=2, row=0, padx=5)
        
        # Save API key button
        self.save_api_button = ttk.Button(
            api_frame,
            text="Save API Key",
            command=self.save_api_key
        )
        self.save_api_button.grid(column=1, row=1, sticky=tk.W, padx=5, pady=10)
        
        # About section
        about_frame = ttk.LabelFrame(self.parent, text="About", padding=10)
        about_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        about_text = """Voice Converter is a real-time speech-to-speech converter 
        using ElevenLabs API for voice synthesis. 
        
        Speak into your microphone and hear your voice converted 
        to another voice in real-time."""
        
        about_label = ttk.Label(about_frame, text=about_text, wraplength=400, justify="left")
        about_label.pack(pady=5)
    
    def select_input_device(self, event):
        """Handle input device selection"""
        selection = self.input_combobox.get()
        if ":" in selection:
            try:
                device_idx = int(selection.split(":")[0])
                if self.audio_manager.set_input_device(device_idx):
                    self.status_bar.set_status(f"Input device set to: {selection}")
                    # Wenn wir bereits aufnehmen, neu starten
                    if hasattr(self.voice_converter, 'recording') and self.voice_converter.recording:
                        self.voice_converter.stop_recording()
                        self.voice_converter.start_recording()
                        self.status_bar.set_status(f"Recording restarted with new input device: {selection}")
                else:
                    self.status_bar.set_status(f"Failed to set input device: {selection}")
            except ValueError:
                self.status_bar.set_status(f"Invalid device selection: {selection}")
    
    def select_output_device(self, event):
        """Handle output device selection"""
        selection = self.output_combobox.get()
        if ":" in selection:
            try:
                device_idx = int(selection.split(":")[0])
                if self.audio_manager.set_output_device(device_idx):
                    # Testen, ob das Gerät funktioniert - kurzen Ton abspielen
                    self.status_bar.set_status(f"Setting output device to: {selection}...")
                    # Kurze Verzögerung für die Statusbar-Aktualisierung
                    self.parent.after(100, lambda: self.status_bar.set_status(f"Output device set to: {selection}"))
                else:
                    self.status_bar.set_status(f"Failed to set output device: {selection}")
            except ValueError:
                self.status_bar.set_status(f"Invalid device selection: {selection}")
    
    def on_threshold_change(self, value):
        """Handle threshold slider change"""
        threshold = int(float(value))
        self.voice_converter.on_threshold_change(threshold)
        self.threshold_label.config(text=str(threshold))
    
    def calibrate_threshold(self):
        """Recalibrate the silence threshold"""
        self.status_bar.set_status("Calibrating silence threshold...")
        self.voice_converter.calibrate_silence_threshold()
        # Update the slider to match the new threshold
        self.threshold_var.set(self.voice_converter.silence_threshold)
        self.threshold_label.config(text=str(self.voice_converter.silence_threshold))
        self.status_bar.set_status("Silence threshold calibrated successfully")
    
    def toggle_api_key_visibility(self):
        """Toggle zwischen Anzeigen und Verstecken des API-Keys"""
        if self.show_key.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
    
    def save_api_key(self):
        """Speichert den eingegebenen API-Key"""
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            self.status_bar.set_status("API Key cannot be empty!")
            return
        
        # Key in den Einstellungen speichern
        self.voice_converter.api_client.settings_manager.set("api_key", api_key)
        
        # API-Client aktualisieren
        self.voice_converter.api_client.set_api_key(api_key)
        
        self.status_bar.set_status("API Key saved successfully!") 