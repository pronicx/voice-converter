# Configuration and constants for Voice Converter application

# ElevenLabs API settings
API_KEY = ""  # API key removed - should be entered in Settings tab
DEFAULT_VOICE_ID = "nPczCjzI2devNBz1zQrb"  # Brian voice ID
DEFAULT_MODEL = "eleven_multilingual_sts_v2"

# Audio recording parameters
FORMAT = 'int16'
CHANNELS = 1
RATE = 44100
CHUNK = 1024 * 5  # Larger chunk size for better speech recognition
SILENCE_DURATION = 0.7  # Reduced silence duration to detect shorter pauses
BUFFER_FRAMES = 3  # Number of frames to keep before speech to avoid choppy starts
MIN_SPEECH_FRAMES = 4  # Minimum number of frames to consider as valid speech
DEFAULT_SILENCE_THRESHOLD = 200  # Default value, will be calibrated

# Audio playback
DEFAULT_VOLUME = 0.8  # Default volume level (0.0 to 1.0)

# Supported languages
LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Polish": "pl",
    "Hindi": "hi",
    "Chinese": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "Arabic": "ar",
    "Dutch": "nl",
    "Turkish": "tr",
    "Russian": "ru",
} 