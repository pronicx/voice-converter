import json
import os

class SettingsManager:
    def __init__(self, config_path="user_settings.json"):
        self.config_path = config_path
        self.settings = {
            "input_device": None,
            "output_device": None,
            "volume": 0.8,
            "silence_threshold": 200,
            "voice_id": None,
            "language_code": "en",
            "api_key": None
        }
        self.load_settings()
    
    def load_settings(self):
        """Load settings from the config file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
                return True
        except Exception as e:
            print(f"Error loading settings: {e}")
        return False
    
    def save_settings(self):
        """Save current settings to the config file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
        return False
    
    def get(self, key, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a setting value and save"""
        self.settings[key] = value
        return self.save_settings() 