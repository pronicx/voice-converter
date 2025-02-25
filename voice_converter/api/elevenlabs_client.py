from elevenlabs import ElevenLabs
from voice_converter import config

class ElevenLabsClient:
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.api_key = ""
        
        if settings_manager:
            saved_api_key = settings_manager.get("api_key")
            if saved_api_key:
                self.api_key = saved_api_key
        
        # Initialize the client
        self.client = ElevenLabs(api_key=self.api_key) if self.api_key else None
        self.available_voices = []
        
        # Try to get voices if API key is available
        if self.api_key:
            self.fetch_available_voices()
    
    def fetch_available_voices(self):
        """Fetch available voices from the ElevenLabs API"""
        try:
            if not self.client:
                if not self.api_key:
                    print("No API key available")
                    return []
                self.client = ElevenLabs(api_key=self.api_key)
                
            print("Fetching available voices...")
            voices = self.client.voices.getAll()
            self.available_voices = [(voice.name, voice.voice_id) for voice in voices]
            return self.available_voices
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return []
    
    def convert_speech(self, audio_data, voice_id=None, language_code=None):
        """Convert speech using the ElevenLabs API"""
        voice_id = voice_id or config.DEFAULT_VOICE_ID
        
        try:
            audio_stream = self.client.speech_to_speech.convert_as_stream(
                voice_id=voice_id,
                output_format="mp3_44100_128",
                audio=audio_data,
                model_id=config.DEFAULT_MODEL,
                optimize_streaming_latency=3  # Maximum latency optimization
            )
            
            # Get audio data from stream
            result_audio = b""
            for chunk in audio_stream:
                result_audio += chunk
                
            return result_audio
        except Exception as e:
            print(f"Error converting speech: {e}")
            return None

    def set_api_key(self, api_key):
        """Setzt den API-Key und aktualisiert ihn in der elevenlabs-Bibliothek"""
        self.api_key = api_key
        self.client = ElevenLabs(api_key=self.api_key)
        # Aktualisiere die Voices nach API-Key-Änderung
        self.fetch_available_voices() 