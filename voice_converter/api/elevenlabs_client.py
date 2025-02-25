from elevenlabs import ElevenLabs
from voice_converter import config

class ElevenLabsClient:
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.api_key = ""
        self.available_voices = []
        self.client = None
        
        if settings_manager:
            saved_api_key = settings_manager.get("api_key")
            if saved_api_key:
                self.api_key = saved_api_key
        
        # Initialize the client if we have an API key
        if self.api_key:
            self.client = ElevenLabs(api_key=self.api_key)
        
        # We'll no longer fetch voices automatically during initialization
        # This will be done explicitly when needed via get_voices()
    
    def fetch_available_voices(self):
        """Fetch available voices from the ElevenLabs API"""
        try:
            if not self.client:
                if not self.api_key:
                    print("No API key available")
                    return {}, []
                self.client = ElevenLabs(api_key=self.api_key)
                
            print("Fetching available voices...")
            response = self.client.voices.get_all()
            voice_dict = {}
            
            # Check response structure based on ElevenLabs API docs
            if hasattr(response, 'voices'):
                # Handle response in format: {"voices": [...]}
                voices = response.voices
            else:
                # Assume response is already the voices list
                voices = response
            
            # Process voice objects
            try:
                # Check if we have objects with name and voice_id attributes
                if voices and hasattr(voices[0], 'name') and hasattr(voices[0], 'voice_id'):
                    self.available_voices = [(voice.name, voice.voice_id) for voice in voices]
                    voice_dict = {voice.name: voice.voice_id for voice in voices}
                elif voices and isinstance(voices[0], dict):
                    # Handle dict format
                    self.available_voices = [(voice.get('name', ''), voice.get('voice_id', '')) for voice in voices]
                    voice_dict = {voice.get('name', ''): voice.get('voice_id', '') for voice in voices}
                else:
                    print(f"Warning: Unexpected voice format: {type(voices[0]) if voices else 'Empty list'}")
                    # Try to extract whatever data we can
                    self.available_voices = []
                    for voice in voices:
                        if hasattr(voice, '__dict__'):
                            # Try to access as object with attributes
                            name = getattr(voice, 'name', str(voice))
                            voice_id = getattr(voice, 'voice_id', '')
                        elif isinstance(voice, tuple) and len(voice) >= 2:
                            # Already in (name, id) format
                            name, voice_id = voice[0], voice[1]
                        else:
                            # Last resort, stringify the object
                            name = str(voice)
                            voice_id = ''
                            
                        self.available_voices.append((name, voice_id))
                        voice_dict[name] = voice_id
            except (IndexError, AttributeError, TypeError) as e:
                print(f"Error processing voices: {e}")
                print(f"Voice data format: {type(voices)}")
            
            return voice_dict, self.available_voices
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return {}, []
    
    def convert_speech(self, audio_data, voice_id=None, language_code=None):
        """Convert speech using the ElevenLabs API"""
        voice_id = voice_id or config.DEFAULT_VOICE_ID
        
        try:
            # Die ElevenLabs API erwartet den Parameter "model_id" anstatt "model"
            # Oder ggf. überhaupt keinen Sprachparameter, wenn das Modell fest ist
            audio_stream = self.client.speech_to_speech.convert_as_stream(
                voice_id=voice_id,
                # Verwende das Modell aus der Konfiguration, falls eine Sprache angegeben wurde
                model_id=config.DEFAULT_MODEL,
                audio=audio_data,
                optimize_streaming_latency=3
            )
            
            result_audio = bytes()
            for chunk in audio_stream:
                result_audio += chunk
                
            return result_audio
        except Exception as e:
            print(f"Error converting speech: {e}")
            
            # Spezifische Fehlerbehandlung für überschrittenes Kontingent
            error_str = str(e)
            if "quota_exceeded" in error_str or "exceeds your quota" in error_str:
                # Kontingentfehler extrahieren
                import re
                
                # Versuche verbleibende und benötigte Credits zu extrahieren
                remaining_credits = re.search(r'You have (\d+) credits remaining', error_str)
                required_credits = re.search(r'while (\d+) credits are required', error_str)
                
                remaining = remaining_credits.group(1) if remaining_credits else "unknown"
                required = required_credits.group(1) if required_credits else "unknown"
                
                error_message = {
                    "type": "quota_exceeded",
                    "message": f"Quota exceeded: {remaining} credits available, {required} credits required.",
                    "details": str(e)
                }
                return None, error_message
            
            # Allgemeiner Fehler
            return None, {"type": "general_error", "message": "API error during speech conversion", "details": str(e)}

    def set_api_key(self, api_key):
        """Set the API key and update the client
        
        Note: This doesn't automatically fetch voices as that will be
        done by the UI refresh after setting the key.
        """
        self.api_key = api_key
        self.client = ElevenLabs(api_key=self.api_key)
        
        # Clear the voice cache so the next get_voices() call will refresh
        # Instead of fetching here, which causes duplication
        self.available_voices = []

    def get_voices(self, force_refresh=False):
        """Return the available voices and languages
        
        Args:
            force_refresh: Whether to force a refresh from the API
            
        Returns:
            tuple: (voices_dict, language_list)
        """
        # Only fetch from API if we don't have voices yet or a refresh is requested
        if not self.available_voices or force_refresh:
            voices_dict, voice_list = self.fetch_available_voices()
        else:
            # Use cached voices
            voice_list = self.available_voices
            voices_dict = {name: voice_id for name, voice_id in voice_list}
            print("Using cached voices (skip fetching)")
        
        # Debug output
        if voice_list:
            print(f"Voice list sample: {voice_list[0:2]}")
            print(f"Voice dict sample: {list(voices_dict.items())[0:2] if voices_dict else 'Empty'}")
        else:
            print("No voices retrieved")
        
        # For languages, we use the static config
        from voice_converter import config
        languages = config.LANGUAGES
        
        return voices_dict, languages 