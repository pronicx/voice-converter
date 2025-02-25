from elevenlabs import ElevenLabs
import config

class ElevenLabsClient:
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.voices = {}
        
        # API-Key aus Settings oder Config verwenden
        self.api_key = None
        if settings_manager and settings_manager.get("api_key"):
            self.api_key = settings_manager.get("api_key")
        else:
            self.api_key = config.API_KEY
        
        # Elevenlabs client initialisieren mit dem API-Key
        self.client = ElevenLabs(api_key=self.api_key)
        self.languages = {}
        
    def get_voices(self):
        """Fetch available voices from ElevenLabs API"""
        try:
            voices_data = self.client.voices.get_all()
            self.voices = {voice.name: voice.voice_id for voice in voices_data.voices}
            
            # Also group voices by language
            self.languages = {}
            for voice in voices_data.voices:
                for language in voice.labels.get('language', []):
                    if language not in self.languages:
                        self.languages[language] = []
                    self.languages[language].append((voice.name, voice.voice_id))
            
            return self.voices, self.languages
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return {}, {}
    
    def get_voice(self, voice_name):
        """Get voice ID by name"""
        return self.voices.get(voice_name)
    
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