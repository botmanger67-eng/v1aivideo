import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


class Config:
    """Central configuration for the AI video generation platform.

    All secret keys and configurable parameters are sourced from environment
    variables with sensible defaults for development.
    """

    # Flask settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))

    # API Keys
    ELEVENLABS_API_KEY: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    GOOGLE_GENAI_API_KEY: Optional[str] = os.getenv("GOOGLE_GENAI_API_KEY")
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")

    # Paths (relative to project root)
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", str(PROJECT_ROOT / "output"))
    TEMP_DIR: str = os.getenv("TEMP_DIR", str(PROJECT_ROOT / "temp"))
    STATIC_DIR: str = os.getenv("STATIC_DIR", str(PROJECT_ROOT / "static"))
    TEMPLATES_DIR: str = os.getenv("TEMPLATES_DIR", str(PROJECT_ROOT / "templates"))

    # Video composition settings
    VIDEO_WIDTH: int = int(os.getenv("VIDEO_WIDTH", "1920"))
    VIDEO_HEIGHT: int = int(os.getenv("VIDEO_HEIGHT", "1080"))
    VIDEO_FPS: int = int(os.getenv("VIDEO_FPS", "24"))
    MAX_VIDEO_DURATION_SECONDS: int = int(os.getenv("MAX_VIDEO_DURATION_SECONDS", "300"))
    MIN_IMAGE_DURATION: float = float(os.getenv("MIN_IMAGE_DURATION", "2.0"))

    # Voice generation
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel
    ELEVENLABS_MODEL: str = os.getenv("ELEVENLABS_MODEL", "eleven_monolingual_v1")
    TTS_SPEED_RATE: float = float(os.getenv("TTS_SPEED_RATE", "1.0"))

    # Image generation
    IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "imagen-3.0-generate-001")
    IMAGE_COUNT_PER_PROMPT: int = int(os.getenv("IMAGE_COUNT_PER_PROMPT", "1"))
    IMAGE_ASPECT_RATIO: str = os.getenv("IMAGE_ASPECT_RATIO", "16:9")

    # Script engine
    SCRIPT_TEMPERATURE: float = float(os.getenv("SCRIPT_TEMPERATURE", "0.7"))
    SCRIPT_MAX_TOKENS: int = int(os.getenv("SCRIPT_MAX_TOKENS", "1024"))
    DEFAULT_SCRIPT_LANGUAGE: str = os.getenv("DEFAULT_SCRIPT_LANGUAGE", "en")

    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate essential configuration settings.

        Returns a dict of missing/empty keys that are required for production.
        """
        errors: Dict[str, Any] = {}
        required_keys = ["SECRET_KEY", "ELEVENLABS_API_KEY", "GOOGLE_GENAI_API_KEY"]
        for key in required_keys:
            value = getattr(cls, key, None)
            if not value or (isinstance(value, str) and value.strip() == ""):
                errors[key] = f"{key} is missing or empty"
        # Ensure output directories exist
        for dir_attr in ["OUTPUT_DIR", "TEMP_DIR"]:
            dir_path = Path(getattr(cls, dir_attr, ""))
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    errors[dir_attr] = f"Cannot create directory {dir_attr}: {e}"
        return errors


# Convenience alias
config = Config