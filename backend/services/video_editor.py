import subprocess
from pathlib import Path

from backend.services.captions import write_ass_file


class VideoEditorError(RuntimeError):
    pass


def _run_ffmpeg(args: list[str]) -> None:
    try:
        process = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise VideoEditorError("FFmpeg is not installed or is not on PATH.") from exc
    if process.returncode != 0:
        detail = process.stderr.strip().splitlines()[-1:] or ["unknown FFmpeg error"]
        raise VideoEditorError(f"FFmpeg failed: {detail[0]}")


def render_clip(
    source: Path,
    transcript: dict,
    start: float,
    end: float,
    output_path: Path,
    subtitle_path: Path,
) -> None:
    write_ass_file(transcript, start, end, subtitle_path)
    duration = max(1.0, end - start)
    subtitle_filter = f"subtitles={subtitle_path.as_posix().replace(':', '\\:')}"
    video_filter = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        f"{subtitle_filter}"
    )
    _run_ffmpeg(
        [
            "-ss",
            f"{start:.3f}",
            "-i",
            str(source),
            "-t",
            f"{duration:.3f}",
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "21",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
