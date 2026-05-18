from typing import Dict, Optional
import os

# Other project modules
from config import Config
from logger import setup_logger
from script_engine import generate_script
from voice_generator import generate_voice
from image_generator import generate_image
from video_compositor import create_video

# -------------------------------------------------------------------
# Global logger (configured once in app.py, reused here via logger name)
# -------------------------------------------------------------------
logger = setup_logger(__name__)


def run_pipeline(
    topic: str,
    voice_id: Optional[str] = None,
    style: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """
    Orchestrate the full AI video generation pipeline.

    Steps:
        1. Generate a script from the given topic.
        2. Generate voiceover audio from the script.
        3. Generate a background image from the script.
        4. Assemble the final video (audio + image + optional text overlays).

    Args:
        topic:        User-provided topic for the video.
        voice_id:     ElevenLabs voice ID (falls back to config default).
        style:        Optional style hint for script generation.
        output_dir:   Directory to store all generated files (default from config).

    Returns:
        Dictionary with keys:
            - "status":        "success" or "error"
            - "video_path":    Path to the final video (or None on failure)
            - "script":        The generated script (or None)
            - "error":         Error message (if any)

    Example:
        result = run_pipeline("Quantum Computing", voice_id="21m00Tcm4TlvDq8ikWAM")
        if result["status"] == "success":
            print(f"Video saved at {result['video_path']}")
    """
    # Use defaults from config if not provided
    voice_id = voice_id or Config.DEFAULT_VOICE_ID
    output_dir = output_dir or Config.OUTPUT_DIR

    # -------------------------------------------------------------------
    # 1. Generate script
    # -------------------------------------------------------------------
    script = None
    try:
        logger.info("Starting script generation for topic: %s", topic)
        script = generate_script(topic, style=style)
        logger.info("Script generated successfully (length=%d)", len(script))
    except Exception as e:
        logger.error("Script generation failed: %s", e, exc_info=True)
        return _error_result("Script generation failed", e)

    # -------------------------------------------------------------------
    # 2. Generate voiceover
    # -------------------------------------------------------------------
    audio_path = None
    try:
        logger.info("Starting voice generation")
        audio_path = generate_voice(script, voice_id=voice_id)
        logger.info("Voice generated successfully: %s", audio_path)
    except Exception as e:
        logger.error("Voice generation failed: %s", e, exc_info=True)
        return _error_result("Voice generation failed", e, script=script)

    # -------------------------------------------------------------------
    # 3. Generate background image(s)
    # -------------------------------------------------------------------
    image_path = None
    try:
        # Use the first sentence of the script as the image prompt
        prompt = script.split(".")[0] + "." if "." in script else script
        logger.info("Starting image generation from prompt: %s", prompt[:80])
        image_path = generate_image(prompt)
        logger.info("Image generated successfully: %s", image_path)
    except Exception as e:
        logger.error("Image generation failed: %s", e, exc_info=True)
        return _error_result("Image generation failed", e, script=script, audio_path=audio_path)

    # -------------------------------------------------------------------
    # 4. Compose final video
    # -------------------------------------------------------------------
    video_path = None
    try:
        logger.info("Starting video composition")
        # For simplicity, we pass the image as a single-element list.
        # Extend with additional images if needed (e.g., scenes per paragraph).
        video_path = create_video(
            audio_path=audio_path,
            image_paths=[image_path],
            output_dir=output_dir,
            script_text=script,           # Optional text overlay
        )
        logger.info("Video created successfully: %s", video_path)
    except Exception as e:
        logger.error("Video composition failed: %s", e, exc_info=True)
        return _error_result("Video composition failed", e, script=script, audio_path=audio_path, image_path=image_path)

    # -------------------------------------------------------------------
    # Success
    # -------------------------------------------------------------------
    return {
        "status": "success",
        "video_path": video_path,
        "script": script,
        "audio_path": audio_path,
        "image_path": image_path,
        "error": None,
    }


def _error_result(
    message: str,
    exception: Exception,
    script: Optional[str] = None,
    audio_path: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Build a standard error result dictionary."""
    return {
        "status": "error",
        "video_path": None,
        "script": script,
        "audio_path": audio_path,
        "image_path": image_path,
        "error": f"{message}: {str(exception)}",
    }