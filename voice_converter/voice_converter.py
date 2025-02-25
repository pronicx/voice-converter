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
        self.status_callback = None  # Callback für Statusmeldungen an die GUI
    
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
        """Add audio frames to the processing queue
        
        Args:
            frames: Either a single audio frame or a list of frames
        """
        if not self.running:
            return
        
        # Limit queue size to maximum 3 elements
        # If queue becomes too large, discard oldest elements
        MAX_QUEUE_SIZE = 3
        
        if len(self.audio_queue) >= MAX_QUEUE_SIZE:
            # Remove oldest element
            old_frames = self.audio_queue.pop(0)
            print(f"Queue overloaded - discarded oldest audio ({len(old_frames)} frames)")
        
        if isinstance(frames, list):
            # If we got a list of frames, process them as a single speech segment
            self.audio_queue.append(frames)
        else:
            # If we got a single frame, add it directly
            self.audio_queue.append([frames])
        
        print(f"Audio data added to queue (size: {len(self.audio_queue)})")
    
    def process_audio_queue(self):
        while self.running:
            if len(self.audio_queue) > 0:
                try:
                    # Get the oldest audio in the queue
                    frames = self.audio_queue.pop(0)
                    
                    # Convert the raw audio frames to a wav file in memory
                    audio_data = self.audio_manager.record_to_file(frames)
                    
                    print(f"Processing audio segment ({len(frames)} frames)")
                    
                    # Send to API for conversion
                    result = self.api_client.convert_speech(
                        audio_data=audio_data,
                        voice_id=self.voice_id,
                        language_code=self.language_code
                    )
                    
                    # Überprüfen, ob ein Fehler zurückgegeben wurde
                    if isinstance(result, tuple) and len(result) == 2:
                        audio_data, error_info = result
                        
                        if error_info and "type" in error_info:
                            # Fehlermeldung an UI senden
                            if hasattr(self, 'status_callback') and self.status_callback:
                                self.status_callback(error_info["message"])
                            
                            # Je nach Fehlertyp unterschiedlich reagieren
                            if error_info["type"] == "quota_exceeded":
                                print(f"QUOTA EXCEEDED: {error_info['message']}")
                                # Optional: Pause recording until user responds
                            else:
                                print(f"API ERROR: {error_info['message']}")
                                
                            # Output details to console
                            print(f"Error details: {error_info['details']}")
                            continue
                    else:
                        # Frühere API-Antwort ohne Fehlerinfos
                        audio_data = result
                    
                    if audio_data:
                        print("Received converted audio, playing...")
                        # Play the converted audio through the audio manager
                        self.audio_manager.play_audio(audio_data)
                    else:
                        print("Warning: Received empty audio data from API")
                        
                except Exception as e:
                    print(f"Error in speech conversion: {e}")
            else:
                # Sleep briefly when queue is empty to reduce CPU usage
                time.sleep(0.1)
    
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
        # Update in settings manager
        if self.settings_manager:
            self.settings_manager.set("silence_threshold", self.silence_threshold)
        # Update in audio manager
        if self.audio_manager:
            self.audio_manager.set_silence_threshold(threshold)
    
    def __del__(self):
        self.running = False  # Signal threads to stop
        if hasattr(self, 'p'):
            self.p.terminate()
    
    def set_voice(self, voice_id):
        """Set the voice to use for conversion"""
        if voice_id:
            self.voice_id = voice_id
            # Save to settings if available
            if self.settings_manager:
                self.settings_manager.set("voice_id", self.voice_id)
            print(f"Voice set to: {voice_id}")
        else:
            print("Warning: Attempted to set empty voice ID")

    def start_recording(self):
        """Start recording and processing"""
        # First start the processing thread
        self.start_processing()
        
        # Then start the audio capture, with a callback to add frames to our queue
        result = self.audio_manager.start_recording(callback=self.add_audio_to_queue)
        
        if not result:
            # If audio capture failed, stop processing too
            self.stop_processing()
            print("Failed to start recording")
            return False
        
        print("Recording and processing started")
        return True

    def stop_recording(self):
        """Stop recording and processing"""
        # Stop audio capture
        self.audio_manager.stop_recording()
        
        # Stop processing
        self.stop_processing()
        
        print("Recording and processing stopped")
        return True

    def set_status_callback(self, callback):
        """Set a callback function that will be called with status messages"""
        self.status_callback = callback 