import os
import requests
import tempfile
from pathlib import Path
from typing import List, Dict, Optional

from config import ELEVENLABS_API_KEY, DEFAULT_VOICE_ID, DEFAULT_MODEL
from logger import get_logger

logger = get_logger(__name__)

class VoiceGenerator:
    """Generates speech audio per scene using ElevenLabs TTS API."""
    
    def __init__(self, api_key: Optional[str] = None, voice_id: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the VoiceGenerator with ElevenLabs credentials.
        
        Args:
            api_key: ElevenLabs API key (default from config)
            voice_id: Voice ID to use (default from config)
            model: TTS model ID (default from config)
        """
        self.api_key = api_key or ELEVENLABS_API_KEY
        self.voice_id = voice_id or DEFAULT_VOICE_ID
        self.model = model or DEFAULT_MODEL
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required.")
    
    def generate_scene_audio(self, text: str, output_path: str, voice_id: Optional[str] = None,
                             model: Optional[str] = None) -> str:
        """
        Generate speech audio for a single scene.
        
        Args:
            text: Text to convert to speech
            output_path: File path to save the audio (e.g., .mp3)
            voice_id: Override default voice ID
            model: Override default model
            
        Returns:
            Path to the generated audio file
            
        Raises:
            ValueError: If text is empty
            Exception: If API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")
        
        voice = voice_id or self.voice_id
        model_id = model or self.model
        
        url = f"{self.base_url}/text-to-speech/{voice}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Audio generated for scene: {output_path}")
            return output_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ElevenLabs API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            raise
    
    def generate_scenes_audio(self, scenes: List[Dict[str, str]], output_dir: str,
                              filename_template: str = "scene_{index}.mp3") -> List[str]:
        """
        Generate audio for multiple scenes.
        
        Args:
            scenes: List of scene dictionaries, each expected to have 'text' key
            output_dir: Directory to save audio files
            filename_template: Template for filenames, {index} is replaced with scene index
            
        Returns:
            List of paths to generated audio files
        """
        audio_paths = []
        os.makedirs(output_dir, exist_ok=True)
        
        for i, scene in enumerate(scenes):
            text = scene.get('text', '')
            if not text:
                logger.warning(f"Scene {i} has no text, skipping audio generation.")
                continue
            
            filename = filename_template.format(index=i)
            output_path = os.path.join(output_dir, filename)
            
            try:
                generated_path = self.generate_scene_audio(text, output_path)
                audio_paths.append(generated_path)
            except Exception as e:
                logger.error(f"Failed to generate audio for scene {i}: {e}")
                # Optionally continue with next scene or raise
                continue
        
        return audio_paths
    
    def list_voices(self) -> List[Dict]:
        """
        List available voices from ElevenLabs.
        
        Returns:
            List of voice dictionaries
            
        Raises:
            Exception: If API call fails
        """
        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("voices", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list voices: {e}")
            raise

# Convenience function to get an audio file extension (e.g., .mp3)
def get_audio_extension() -> str:
    """Return the default audio file extension for TTS output."""
    return ".mp3"