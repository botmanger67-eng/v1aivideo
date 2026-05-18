import os
from typing import List, Tuple, Optional
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
)
from moviepy.audio.AudioClip import CompositeAudioClip
from config import Config
from logger import get_logger
from script_engine import ScriptEngine
from voice_generator import VoiceGenerator

logger = get_logger(__name__)


class VideoCompositor:
    """Assembles video from audio, image, and text assets using MoviePy."""

    def __init__(
        self,
        script_engine: Optional[ScriptEngine] = None,
        voice_generator: Optional[VoiceGenerator] = None,
        output_dir: str = None,
    ):
        """
        Initialize compositor with dependencies.

        Args:
            script_engine: Engine to generate script prompts.
            voice_generator: Engine to generate voice over audio.
            output_dir: Directory to save assembled video (default from config).
        """
        self.script_engine = script_engine or ScriptEngine()
        self.voice_generator = voice_generator or VoiceGenerator()
        self.output_dir = output_dir or Config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def assemble_video(
        self,
        image_paths: List[str],
        audio_path: str,
        subtitles: Optional[List[Tuple[float, float, str]]] = None,
        output_filename: str = "final_video.mp4",
        fps: int = 24,
    ) -> str:
        """
        Combine background music (or silent), voice over, images, and subtitles.

        Args:
            image_paths: Ordered list of image file paths.
            audio_path: Path to the voice over audio file.
            subtitles: List of (start_seconds, end_seconds, text) tuples.
            output_filename: Name of output video file.
            fps: Frames per second for the output video.

        Returns:
            Path to the generated video file.

        Raises:
            FileNotFoundError: If any required file is missing.
            ValueError: If input parameters are invalid.
        """
        if not image_paths:
            raise ValueError("At least one image path is required.")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        for img_path in image_paths:
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Image file not found: {img_path}")

        try:
            # Load voice over audio
            voice_audio = AudioFileClip(audio_path)

            # Create image clip sequence with durations based on audio length
            num_images = len(image_paths)
            if num_images == 0:
                raise ValueError("No images provided.")

            # Distribute audio duration evenly among images
            audio_duration = voice_audio.duration
            per_image_duration = audio_duration / num_images

            # Ensure crossfade duration does not exceed clip duration
            crossfade = min(0.5, per_image_duration / 2)

            image_clips = []
            for i, img_path in enumerate(image_paths):
                clip = (
                    ImageClip(img_path)
                    .set_duration(per_image_duration)
                    .set_audio(None)
                    .crossfadein(crossfade)
                    .crossfadeout(crossfade)
                )
                image_clips.append(clip)

            # Concatenate image clips
            video = concatenate_videoclips(image_clips, method="compose")

            # Attach voice over audio
            video = video.set_audio(voice_audio)

            # Add subtitles if provided
            if subtitles:
                subtitle_clip = self._create_subtitle_clip(subtitles, video.size)
                if subtitle_clip is not None:
                    video = CompositeVideoClip([video, subtitle_clip])

            # Write output video
            output_path = os.path.join(self.output_dir, output_filename)
            video.write_videofile(
                output_path,
                fps=fps,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=os.path.join(self.output_dir, "temp_audio.m4a"),
                remove_temp=True,
                logger=logger,
            )

            # Cleanup
            video.close()
            voice_audio.close()

            logger.info(f"Video assembled successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Video assembly failed: {e}")
            raise

    def _create_subtitle_clip(
        self, subtitles: List[Tuple[float, float, str]], video_size: Tuple[int, int]
    ) -> Optional[CompositeVideoClip]:
        """
        Create a subtitles clip from a list of subtitle tuples.

        Args:
            subtitles: List of (start, end, text) tuples.
            video_size: (width, height) of the video.

        Returns:
            CompositeVideoClip overlay, or None if no valid subtitles.
        """
        try:
            clips = []
            for start, end, text in subtitles:
                duration = end - start
                if duration <= 0:
                    continue
                clip = (
                    TextClip(
                        text,
                        fontsize=24,
                        color="white",
                        stroke_color="black",
                        stroke_width=1,
                        font="Arial",
                        size=video_size,
                        method="caption",
                    )
                    .set_position(("center", "bottom"))
                    .set_start(start)
                    .set_duration(duration)
                )
                clips.append(clip)

            if not clips:
                return None
            return CompositeVideoClip(clips, size=video_size)

        except Exception as e:
            logger.error(f"Subtitle creation failed: {e}")
            return None

    def generate_and_assemble(
        self,
        topic: str,
        audio_path: str = None,
        image_paths: List[str] = None,
        output_filename: str = "generated_video.mp4",
        fps: int = 24,
    ) -> str:
        """
        High-level method using script engine and voice generator.

        Args:
            topic: Topic for script generation.
            audio_path: Pre-generated audio path (if None, will generate).
            image_paths: List of image paths (if None, will generate placeholders).
            output_filename: Output video name.
            fps: Frames per second.

        Returns:
            Path to final video.
        """
        try:
            # Generate script
            script_data = self.script_engine.generate_script(topic)
            lines = script_data.get("sentences", [topic])

            # Generate voice over if not provided
            if audio_path is None:
                audio_path = self.voice_generator.generate_speech(
                    " ".join(lines),
                    output_path=os.path.join(self.output_dir, "voice_over.mp3"),
                )

            # Generate placeholder images if not provided
            if not image_paths:
                image_paths = self._generate_placeholder_images(
                    len(lines), output_dir=self.output_dir
                )

            # Generate subtitles from script lines
            subtitles = self._create_subtitles_from_lines(lines)

            return self.assemble_video(
                image_paths=image_paths,
                audio_path=audio_path,
                subtitles=subtitles,
                output_filename=output_filename,
                fps=fps,
            )

        except Exception as e:
            logger.error(f"Full generation and assembly failed: {e}")
            raise

    def _generate_placeholder_images(self, count: int, output_dir: str) -> List[str]:
        """
        Generate solid color placeholder images.

        Args:
            count: Number of images needed.
            output_dir: Directory to save images.

        Returns:
            List of file paths.
        """
        paths = []
        colors = ["blue", "green", "red", "yellow", "purple", "orange", "cyan", "magenta"]
        for i in range(count):
            color = colors[i % len(colors)]
            img_path = os.path.join(output_dir, f"placeholder_{i}.png")
            clip = ColorClip(size=(1920, 1080), color=color, duration=0)
            clip.save_frame(img_path, t=0)
            paths.append(img_path)
            clip.close()
        logger.info(f"Generated {count} placeholder images in {output_dir}")
        return paths

    def _create_subtitles_from_lines(
        self,
        lines: List[str],
        word_per_second: float = 2.5,
    ) -> List[Tuple[float, float, str]]:
        """
        Convert script lines into subtitle timing based on reading speed.

        Args:
            lines: List of text lines.
            word_per_second: Estimated words per second spoken.

        Returns:
            List of (start_time, end_time, text) subtitle tuples.
        """
        subtitles = []
        current_time = 0.0
        for line in lines:
            if not line.strip():
                current_time += 0.5
                continue
            words = len(line.split())
            duration = words / word_per_second
            if duration < 1.0:
                duration = 1.0
            subtitles.append((current_time, current_time + duration, line))
            current_time += duration
        return subtitles

    @staticmethod
    def add_background_music(
        video_path: str,
        music_path: str,
        output_path: str,
        volume_reduction_db: float = 10.0,
    ) -> str:
        """
        Overlay background music onto an existing video file.

        Args:
            video_path: Path to input video.
            music_path: Path to background music audio file.
            output_path: Path for output video.
            volume_reduction_db: Reduce music volume by this many dB.

        Returns:
            Path to output video.
        """
        try:
            video = VideoFileClip(video_path)
            music = AudioFileClip(music_path)

            # Reduce music volume
            music = music.volumex(10 ** (-volume_reduction_db / 20))

            # Set music duration to match video; loop if needed
            if music.duration < video.duration:
                music = music.loop(d