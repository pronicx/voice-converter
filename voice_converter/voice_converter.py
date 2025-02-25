import time
import threading

class VoiceConverter:
    def __init__(self, audio_manager, api_client, settings_manager=None):
        self.audio_manager = audio_manager
        self.api_client = api_client
        self.settings_manager = settings_manager
        
        # Initialize with settings from the settings manager if available
        self.voice_id = None
        self.language_code = "en"
        self.silence_threshold = 200
        
        if settings_manager:
            self.voice_id = settings_manager.get("voice_id")
            self.language_code = settings_manager.get("language_code", "en")
            self.silence_threshold = settings_manager.get("silence_threshold", 200)
        
        # Audio processing state
        self.running = False
        self.audio_queue = []
        self.processing_thread = None
    
    def start_processing(self):
        """Start the speech processing thread"""
        if not self.running:
            self.running = True
            self.audio_queue = []  # Clear any pending audio
            self.processing_thread = threading.Thread(target=self.process_audio_queue)
            self.processing_thread.daemon = True
            self.processing_thread.start()
    
    def stop_processing(self):
        """Stop the speech processing thread"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
            self.processing_thread = None
    
    def add_audio_to_queue(self, frames):
        """Add audio frames to the processing queue"""
        if self.running:
            self.audio_queue.append(frames)
            
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