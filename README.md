# 🎬 AI Video Engine

AI Video Engine is a full-stack web platform for generating short, narrative-driven videos using artificial intelligence. It leverages advanced LLMs, text-to-speech, image generation, and video compositing to transform a simple prompt into a complete video with voiceover and visuals.

## 🚀 Features

- **AI Script Generation** – Uses DeepSeek (via OpenRouter) to generate a creative, scene-based script from a user prompt.
- **Text-to-Speech Voiceover** – Converts each script line into natural-sounding audio using ElevenLabs.
- **AI Image Generation** – Creates scene images using Google GenAI (Imagen or similar).
- **Automated Video Compositing** – Combines images, voiceover, and subtitles into a final video with MoviePy.
- **Web Interface** – Simple, modern UI (HTML/CSS/JS) to submit prompts and download the result.
- **Configurable** – Easily switch API keys and settings via `config.py`.

## 🧰 Tech Stack

| Component          | Technology                                   |
|--------------------|----------------------------------------------|
| Backend Framework  | Flask (Python)                               |
| Script Generation  | DeepSeek via OpenRouter API (LLM)            |
| Text-to-Speech     | ElevenLabs API                               |
| Image Generation   | Google GenAI (Gemini / Imagen)               |
| Video Assembly     | MoviePy + FFmpeg                             |
| Frontend           | HTML, CSS, JavaScript (vanilla)              |
| Logging            | Python `logging` module                      |

## 📦 Installation

### Prerequisites
- Python 3.10+
- FFmpeg installed and available in PATH (required by MoviePy)
- API keys for: OpenRouter (DeepSeek), ElevenLabs, Google GenAI

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-video-engine.git
   cd ai-video-engine
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**  
   Copy `config.py` to set your API keys. You can also use a `.env` file (adjust `config.py` accordingly):
   ```python
   # config.py example
   OPENROUTER_API_KEY = "your-openrouter-key"
   ELEVENLABS_API_KEY = "your-elevenlabs-key"
   GOOGLE_GENAI_API_KEY = "your-google-genai-key"
   ```

5. **Run the application**
   ```bash
   python app.py
   ```
   The server will start at `http://127.0.0.1:5000`.

## 🖥️ Usage

1. Open the web interface in your browser.
2. Enter a prompt (e.g., “A short story about a robot learning to paint”).
3. Click **Generate Video**.
4. Wait for the pipeline to complete (this may take a few minutes depending on API response times and video length).
5. Download the final `.mp4` video.

The generated video will include:
- A narrative voiceover (ElevenLabs)
- Corresponding AI-generated images per scene
- Subtitles (optional, can be configured in `video_compositor.py`)

## 📁 Project Structure

```
ai-video-engine/
├── app.py                  # Flask web server & routes
├── config.py               # API keys and configuration
├── logger.py               # Custom logging setup
├── script_engine.py        # Script generation (DeepSeek)
├── voice_generator.py      # Text-to-speech (ElevenLabs)
├── image_generator.py      # Image generation (Google GenAI)
├── video_compositor.py     # Audio + images → video (MoviePy)
├── pipeline.py             # Orchestrates the entire generation flow
├── templates/
│   └── index.html          # Frontend HTML
├── static/
│   ├── style.css           # Styling
│   └── script.js           # Client-side JavaScript
└── requirements.txt        # Python dependencies
```

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

**Note**: This application requires active API subscriptions. Video generation speed depends on the responsiveness of the third-party services used.