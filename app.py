import os
import json
from flask import Flask, request, jsonify, render_template, session, send_file
from werkzeug.utils import secure_filename
from functools import wraps

from config import Config
from logger import setup_logger
from script_engine import ScriptEngine
from voice_generator import VoiceGenerator
from image_generator import ImageGenerator
from pipeline import Pipeline
from video_compositor import VideoCompositor

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get("SECRET_KEY", Config.SECRET_KEY)

logger = setup_logger(__name__)

pipeline = Pipeline(
    script_engine=ScriptEngine(),
    voice_generator=VoiceGenerator(),
    image_generator=ImageGenerator(),
    video_compositor=VideoCompositor()
)

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key == Config.API_KEY:
            return f(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized"}), 401
    return decorated

@app.route("/", methods=["GET"])
def index():
    """Render the main page."""
    try:
        return render_template("index.html")
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/generate", methods=["POST"])
@require_api_key
def generate():
    """Generate video from user input."""
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        topic = data.get("topic")
        if not topic:
            return jsonify({"error": "Missing 'topic' field"}), 400

        # Optional additional parameters
        style = data.get("style", "realistic")
        duration = data.get("duration", 30)
        language = data.get("language", "en")
        custom_prompt = data.get("custom_prompt", None)

        # Validate inputs
        if not isinstance(duration, int) or duration < 10 or duration > 300:
            return jsonify({"error": "Duration must be integer between 10 and 300 seconds"}), 400

        allowed_styles = ["realistic", "cartoon", "anime", "watercolor"]
        if style not in allowed_styles:
            return jsonify({"error": f"Style must be one of {allowed_styles}"}), 400

        logger.info(f"Generating video for topic: {topic}, style: {style}, duration: {duration}s")

        # Run the pipeline
        result = pipeline.generate(
            topic=topic,
            style=style,
            duration=duration,
            language=language,
            custom_prompt=custom_prompt
        )

        # result expected to be a dict with keys: video_url, thumbnail_url, script, etc.
        return jsonify({
            "success": True,
            "video_url": result.get("video_url"),
            "thumbnail_url": result.get("thumbnail_url"),
            "script": result.get("script"),
            "audio_url": result.get("audio_url")
        })

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Pipeline generation failed: {e}", exc_info=True)
        return jsonify({"error": "Video generation failed. Please try again later."}), 500

@app.route("/status/<task_id>", methods=["GET"])
def status(task_id):
    """Check the status of an asynchronous generation task."""
    try:
        # In a real app, this would check a task queue (e.g., Celery)
        # For simplicity, we assume synchronous generation.
        return jsonify({"status": "completed", "task_id": task_id})
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return jsonify({"error": "Status check failed"}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )