import tkinter as tk
from tkinter import ttk
import numpy as np

class SettingsTabComponent:
    def __init__(self, parent, audio_manager, voice_converter, status_bar):
        self.parent = parent
        self.audio_manager = audio_manager
        self.voice_converter = voice_converter
        self.status_bar = status_bar
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the settings tab elements"""
        # Audio settings section
        audio_frame = ttk.LabelFrame(self.parent, text="Audio Settings", padding=10)
        audio_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input device selection
        ttk.Label(audio_frame, text="Input Device:").grid(column=0, row=0, sticky=tk.W, pady=5)
        self.input_device_combobox = ttk.Combobox(audio_frame, state="readonly", width=30)
        self.input_device_combobox.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5)
        self.input_device_combobox.bind("<<ComboboxSelected>>", self.select_input_device)
        
        # Output device selection
        ttk.Label(audio_frame, text="Output Device:").grid(column=0, row=1, sticky=tk.W, pady=5)
        self.output_device_combobox = ttk.Combobox(audio_frame, state="readonly", width=30)
        self.output_device_combobox.grid(column=1, row=1, sticky=tk.W, padx=5, pady=5)
        self.output_device_combobox.bind("<<ComboboxSelected>>", self.select_output_device)
        
        # Silence threshold slider
        ttk.Label(audio_frame, text="Silence Threshold:").grid(column=0, row=2, sticky=tk.W, pady=5)
        self.threshold_frame = ttk.Frame(audio_frame)
        self.threshold_frame.grid(column=1, row=2, sticky=tk.W, padx=5, pady=5)
        
        self.threshold_slider = ttk.Scale(
            self.threshold_frame, 
            from_=0, 
            to=1000, 
            orient=tk.HORIZONTAL, 
            length=200,
            command=self.on_threshold_change
        )
        self.threshold_slider.pack(side=tk.LEFT)
        
        # Current threshold value
        self.threshold_label = ttk.Label(self.threshold_frame, text="367")
        self.threshold_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Set initial threshold from settings
        initial_threshold = self.voice_converter.silence_threshold
        self.threshold_slider.set(initial_threshold)
        self.threshold_label.config(text=str(int(initial_threshold)))
        
        # Calibrate microphone button
        self.calibrate_button = ttk.Button(
            audio_frame,
            text="Calibrate Microphone",
            command=self.calibrate_threshold
        )
        self.calibrate_button.grid(column=1, row=3, sticky=tk.W, padx=5, pady=10)
        
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
        
        # Populate the device combos
        self.populate_audio_devices()

    def on_threshold_change(self, value):
        """Handle threshold slider changes"""
        threshold = int(float(value))
        self.threshold_label.config(text=str(threshold))
        self.voice_converter.on_threshold_change(threshold)
        
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.show_key.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")

    def populate_audio_devices(self):
        """Populate the audio device comboboxes"""
        # Get input devices
        input_devices = self.audio_manager.available_devices['input']
        self.input_device_combobox['values'] = list(input_devices.values())
        
        # Get output devices
        output_devices = self.audio_manager.available_devices['output']
        self.output_device_combobox['values'] = list(output_devices.values())
        
        # Set current selections
        if self.audio_manager.input_device is not None:
            input_name = input_devices.get(self.audio_manager.input_device)
            if input_name:
                self.input_device_combobox.set(input_name)
                
        if self.audio_manager.output_device is not None:
            output_name = output_devices.get(self.audio_manager.output_device)
            if output_name:
                self.output_device_combobox.set(output_name)

    def select_input_device(self, event):
        """Handle input device selection"""
        selected_device_name = self.input_device_combobox.get()
        
        # Find the device index for the selected name
        device_idx = None
        for idx, name in self.audio_manager.available_devices['input'].items():
            if name == selected_device_name:
                device_idx = idx
                break
        
        if device_idx is not None:
            success = self.audio_manager.set_input_device(device_idx)
            if success:
                self.status_bar.set_status(f"Input device set to: {selected_device_name}")
            else:
                self.status_bar.set_status("Failed to set input device")
        else:
            self.status_bar.set_status("Invalid input device selected")

    def select_output_device(self, event):
        """Handle output device selection"""
        selected_device_name = self.output_device_combobox.get()
        
        # Find the device index for the selected name
        device_idx = None
        for idx, name in self.audio_manager.available_devices['output'].items():
            if name == selected_device_name:
                device_idx = idx
                break
        
        if device_idx is not None:
            success = self.audio_manager.set_output_device(device_idx)
            if success:
                self.status_bar.set_status(f"Output device set to: {selected_device_name}")
            else:
                self.status_bar.set_status("Failed to set output device")
        else:
            self.status_bar.set_status("Invalid output device selected")

    def calibrate_threshold(self):
        """Automatically calibrate the silence threshold"""
        self.status_bar.set_status("Calibrating threshold, please remain quiet for a moment...")
        
        # Start a short recording to analyze background noise
        try:
            # Create a short recording stream
            stream = self.audio_manager.p.open(
                format=self.audio_manager.p.get_format_from_width(2),
                channels=1,
                rate=44100,
                input=True,
                input_device_index=self.audio_manager.input_device,
                frames_per_buffer=1024
            )
            
            # Collect 2 seconds of ambient audio
            frames = []
            samples = int(44100 / 1024 * 2)  # 2 seconds of audio
            
            # Visual feedback during calibration
            for i in range(samples):
                data = stream.read(1024)
                frames.append(data)
                if i % 5 == 0:  # Update status every few frames
                    progress = int((i / samples) * 100)
                    self.status_bar.set_status(f"Calibration in progress: {progress}% (please remain quiet)")
                    self.parent.update()  # Update UI
            
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            
            # Analyze audio to determine threshold
            if frames:
                # Convert all frames to numpy arrays
                audio_arrays = [np.frombuffer(frame, dtype=np.int16) for frame in frames]
                all_audio = np.concatenate(audio_arrays)
                
                # Calculate RMS
                rms = np.sqrt(np.mean(np.square(all_audio.astype(float))))
                
                # Set threshold to 2.5x the ambient noise (minimum 150)
                new_threshold = max(int(rms * 2.5), 150)
                
                # Update threshold in the UI and system
                self.threshold_slider.set(new_threshold)
                self.threshold_label.config(text=str(new_threshold))
                self.voice_converter.on_threshold_change(new_threshold)
                
                self.status_bar.set_status(f"Microphone calibrated to threshold {new_threshold}")
            else:
                self.status_bar.set_status("Calibration failed: No audio data recorded")
        except Exception as e:
            print(f"Error during calibration: {e}")
            self.status_bar.set_status("Calibration error - See console for details")

    def save_api_key(self):
        """Save the API key and update the client"""
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            self.status_bar.set_status("API key cannot be empty")
            return
        
        # Update the API client
        self.voice_converter.api_client.set_api_key(api_key)
        
        # Save to settings
        if self.voice_converter.settings_manager:
            self.voice_converter.settings_manager.set("api_key", api_key)
        
        self.status_bar.set_status("API key saved successfully")
        
        # Refresh voice list with new API key
        self.parent.after(500, lambda: self.parent.master.after(500, self.parent.master.load_voices)) 