import pyaudio
import time
import threading
import config

class VoiceConverter:
    def __init__(self, audio_manager, api_client, settings_manager=None):
        self.audio_manager = audio_manager
        self.api_client = api_client
        self.settings_manager = settings_manager
        self.p = pyaudio.PyAudio()
        self.recording = False
        self.stream = None
        self.frames = []
        self.last_audio_time = time.time()
        self.audio_queue = []
        self.processing_thread = None
        self.running = True
        
        # Load settings if available
        if settings_manager:
            self.silence_threshold = settings_manager.get("silence_threshold", config.DEFAULT_SILENCE_THRESHOLD)
            self.voice_id = settings_manager.get("voice_id", config.DEFAULT_VOICE_ID)
            self.language_code = settings_manager.get("language_code")
        else:
            self.silence_threshold = config.DEFAULT_SILENCE_THRESHOLD
            self.voice_id = config.DEFAULT_VOICE_ID
            self.language_code = None
        
        self.silence_buffer = []
        
    def set_voice(self, voice_id):
        """Set the voice ID to use for conversion"""
        self.voice_id = voice_id
        self.settings_manager.set("voice_id", voice_id)
        
    def set_language(self, language_code):
        """Set the language code to use for conversion"""
        self.language_code = language_code
        self.settings_manager.set("language_code", language_code)
        
    def calibrate_silence_threshold(self):
        """Automatically calibrate the silence threshold based on ambient noise"""
        print("Calibrating silence threshold... (please stay quiet)")
        
        input_device = None
        if self.audio_manager.input_device is not None:
            input_device = self.audio_manager.input_device
            
        calibration_stream = self.p.open(
            format=pyaudio.paInt16,
            channels=config.CHANNELS,
            rate=config.RATE,
            input=True,
            input_device_index=input_device,
            frames_per_buffer=config.CHUNK
        )
        
        # Collect 2 seconds of ambient noise
        noise_frames = []
        for _ in range(0, int(config.RATE / config.CHUNK * 2)):
            data = calibration_stream.read(config.CHUNK)
            noise_frames.append(data)
        
        calibration_stream.stop_stream()
        calibration_stream.close()
        
        # Calculate the maximum amplitude from ambient noise
        max_amplitudes = []
        for frame in noise_frames:
            audio_data = [abs(int.from_bytes(frame[i:i+2], byteorder='little', signed=True)) 
                         for i in range(0, len(frame), 2)]
            if audio_data:
                max_amplitudes.append(max(audio_data))
        
        # Set the threshold to be 2.5x the max ambient noise
        if max_amplitudes:
            ambient_max = max(max_amplitudes)
            self.silence_threshold = int(ambient_max * 2.5)
            print(f"Silence threshold calibrated to: {self.silence_threshold}")
            self.settings_manager.set("silence_threshold", self.silence_threshold)
        else:
            print("Calibration failed, using default threshold")
        
    def callback(self, in_data, frame_count, time_info, status):
        if self.recording:
            # Check if there's audio or silence
            audio_data = [abs(int.from_bytes(in_data[i:i+2], byteorder='little', signed=True)) 
                        for i in range(0, len(in_data), 2)]
            
            # Keep a buffer of recent frames
            self.silence_buffer.append(in_data)
            if len(self.silence_buffer) > config.BUFFER_FRAMES:
                self.silence_buffer.pop(0)
                
            if max(audio_data) > self.silence_threshold:
                # Speech detected
                if self.silence_buffer:
                    # Add buffered frames first if we're just starting to speak
                    if len(self.frames) == 0:
                        self.frames.extend(self.silence_buffer)
                # Then add the current frame
                self.frames.append(in_data)
                self.last_audio_time = time.time()
            elif time.time() - self.last_audio_time > config.SILENCE_DURATION and len(self.frames) >= config.MIN_SPEECH_FRAMES:
                # If silence detected and we have enough frames, process the audio
                if len(self.frames) > 0:
                    # Add a few extra frames to capture trailing sounds
                    self.frames.append(in_data)
                    
                    temp_frames = self.frames.copy()
                    self.frames = []
                    # Use a maximum queue size
                    if len(self.audio_queue) < 3:  # Strict limit on queue size
                        self.audio_queue.append(temp_frames)
                    else:
                        print("Queue full, skipping audio segment")
                
        return (in_data, pyaudio.paContinue)
    
    def start_recording(self):
        # Calibrate silence threshold first
        self.calibrate_silence_threshold()
        
        # Start the worker thread
        self.running = True
        self.processing_thread = threading.Thread(target=self.process_audio_queue)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        # Then start audio recording with the selected input device
        input_device_index = self.audio_manager.input_device
        
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=config.CHANNELS,
            rate=config.RATE,
            input=True,
            input_device_index=input_device_index,
            frames_per_buffer=config.CHUNK,
            stream_callback=self.callback
        )
        self.recording = True
        self.frames = []
        self.silence_buffer = []
        self.stream.start_stream()
        
        print(f"Recording started with threshold {self.silence_threshold}...")
        if input_device_index is not None:
            device_info = self.p.get_device_info_by_index(input_device_index)
            print(f"Using input device: {device_info['name']}")
        
    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.stream.stop_stream()
            self.stream.close()
            # Signal the worker thread to stop
            self.running = False
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2.0)  # Wait up to 2 seconds
            print("Recording stopped.")
            
    def process_audio_queue(self):
        while self.running:
            if len(self.audio_queue) > 0:
                frames = self.audio_queue.pop(0)
                self.convert_speech(frames)
            else:
                # Sleep briefly when no audio to process (reduces CPU usage)
                time.sleep(0.05)
    
    def convert_speech(self, frames):
        try:
            # Convert frames to WAV format in memory
            wav_data = self.audio_manager.record_to_file(frames)
            
            print("Converting speech...")
            # Use the API client to convert speech
            audio_data = self.api_client.convert_speech(
                audio_data=wav_data, 
                voice_id=self.voice_id,
                language_code=self.language_code
            )
            
            if audio_data:
                # Play the converted audio through the audio manager
                self.audio_manager.play_audio(audio_data)
            else:
                print("Warning: Received empty audio data from API")
                
        except Exception as e:
            print(f"Error in speech conversion: {e}")
    
    def on_threshold_change(self, threshold):
        """Set the silence threshold"""
        self.silence_threshold = threshold
        self.settings_manager.set("silence_threshold", self.silence_threshold)
    
    def __del__(self):
        self.running = False  # Signal threads to stop
        if hasattr(self, 'p'):
            self.p.terminate() 