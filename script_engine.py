import requests
import json
from typing import Optional
from logger import get_logger
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL

logger = get_logger(__name__)


class ScriptEngine:
    """Generates video scripts using DeepSeek AI."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize script engine with API key."""
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL or "https://api.deepseek.com/v1/chat/completions"
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")

    def generate_script(self, topic: str, max_length: int = 500) -> str:
        """Generate a script for a given topic.

        Args:
            topic: Topic for the video script.
            max_length: Maximum character length for the script.

        Returns:
            Generated script text.

        Raises:
            RuntimeError: On API request failure.
            ValueError: On invalid response parsing.
        """
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a scriptwriter for an AI video generation platform. "
                            "Create engaging, concise video scripts."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Write a short video script about {topic}. "
                                   f"Keep it under {max_length} characters.",
                    },
                ],
                "max_tokens": max_length // 4,
                "temperature": 0.7,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            response = requests.post(
                self.api_url, json=payload, headers=headers, timeout=30
            )
            response.raise_for_status()
            data = response.json()
            script = data["choices"][0]["message"]["content"].strip()
            logger.info(f"Generated script for topic: {topic}")
            return script
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}")
            raise RuntimeError(f"DeepSeek API request failed: {e}") from e
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse DeepSeek response: {e}")
            raise ValueError(f"Invalid response from DeepSeek API: {e}") from e

    def generate_script_from_prompt(self, prompt: str) -> str:
        """Generate script from a custom prompt.

        Args:
            prompt: Custom prompt for script generation.

        Returns:
            Generated script text.

        Raises:
            RuntimeError: On API request failure.
            ValueError: On invalid response parsing.
        """
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.7,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            response = requests.post(
                self.api_url, json=payload, headers=headers, timeout=30
            )
            response.raise_for_status()
            data = response.json()
            script = data["choices"][0]["message"]["content"].strip()
            logger.info("Generated script from custom prompt")
            return script
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}")
            raise RuntimeError(f"DeepSeek API request failed: {e}") from e
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse DeepSeek response: {e}")
            raise ValueError(f"Invalid response from DeepSeek API: {e}") from e