import os
import base64
import hashlib
from typing import List, Optional
from config import GOOGLE_API_KEY
from logger import setup_logger
import google.generativeai as genai

logger = setup_logger(__name__)

class ImageGenerator:
    """
    Generates images using Google Gemini API.

    This class leverages the Gemini model's ability to generate images
    from text prompts. It handles API configuration, prompt generation,
    and image saving.
    """

    def __init__(self, model_name: str = "gemini-2.0-flash-exp-image-generation"):
        """
        Initialize the ImageGenerator.

        Args:
            model_name: The Gemini model name with image generation capability.
        """
        if not GOOGLE_API_KEY:
            raise ValueError("Google API key not found in config.")
        
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(model_name)
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.4,
            top_p=0.9,
            top_k=32,
            max_output_tokens=8192,
        )
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        logger.info("ImageGenerator initialized with model %s", model_name)

    def generate_image(self, prompt: str, output_dir: str = "generated_images", filename: Optional[str] = None) -> str:
        """
        Generate an image from text prompt and save to file.

        Args:
            prompt: The text description for the image.
            output_dir: Directory to save the image.
            filename: Optional filename (without extension). If None, uses prompt hash.

        Returns:
            str: Absolute path to saved image file.

        Raises:
            ValueError: If prompt is empty or generation fails.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt must not be empty.")

        try:
            # Prepare request with image generation instruction
            full_prompt = f"Generate a detailed image based on this description: {prompt}"
            response = self.model.generate_content(
                contents=full_prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
            )

            # Parse response for image data (assuming inline format)
            image_data = None
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    image_data = part.inline_data.data
                    break

            if not image_data:
                # If no image returned, try to use text description as fallback
                raise RuntimeError("No image data returned from Gemini API.")

            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Generate filename
            if filename is None:
                # Simple deterministic name from prompt
                hash_obj = hashlib.md5(prompt.encode())
                filename = hash_obj.hexdigest()[:12]

            # Determine extension from MIME type
            mime_type = part.inline_data.mime_type
            ext = mime_type.split("/")[-1] if mime_type else "png"
            if ext == "jpeg":
                ext = "jpg"

            filepath = os.path.join(output_dir, f"{filename}.{ext}")

            # Decode base64 and save
            image_bytes = base64.b64decode(image_data)
            with open(filepath, "wb") as f:
                f.write(image_bytes)

            logger.info("Image saved to %s", filepath)
            return os.path.abspath(filepath)

        except Exception as e:
            logger.error("Failed to generate image for prompt '%s': %s", prompt, str(e))
            raise

    def generate_images_from_scenes(self, scenes: List[dict], output_dir: str = "generated_images") -> List[str]:
        """
        Generate images for a list of scenes.

        Args:
            scenes: List of dicts containing 'visual_description' key.
            output_dir: Directory to save images.

        Returns:
            List of file paths to generated images.
        """
        if not scenes:
            logger.warning("No scenes provided for image generation.")
            return []

        image_paths = []
        for i, scene in enumerate(scenes):
            prompt = scene.get("visual_description", scene.get("description", ""))
            if not prompt:
                logger.warning("Scene %d has no visual description, skipping.", i)
                continue
            try:
                path = self.generate_image(prompt, output_dir, filename=f"scene_{i:04d}")
                image_paths.append(path)
            except Exception as e:
                logger.error("Failed to generate image for scene %d: %s", i, str(e))
                # Continue with other scenes
                continue

        return image_paths