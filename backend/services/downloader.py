from pathlib import Path
from urllib.parse import urlparse

from backend.settings import settings


class DownloadError(RuntimeError):
    pass


def validate_youtube_url(url: str) -> None:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().removeprefix("www.")
    if parsed.scheme not in {"http", "https"} or hostname not in {
        "youtube.com",
        "m.youtube.com",
        "youtu.be",
    }:
        raise DownloadError("Please enter a valid YouTube URL.")


def download_video(url: str, job_dir: Path) -> Path:
    validate_youtube_url(url)

    try:
        import yt_dlp
    except ImportError as exc:
        raise DownloadError("yt-dlp is not installed on the backend.") from exc

    output_template = str(job_dir / "source.%(ext)s")
    options = {
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "max_filesize": 2 * 1024 * 1024 * 1024,
    }
    if Path(settings.ffmpeg_binary).is_file():
        options["ffmpeg_location"] = str(Path(settings.ffmpeg_binary).parent)

    try:
        with yt_dlp.YoutubeDL(options) as client:
            info = client.extract_info(url, download=True)
            duration = info.get("duration")
            if duration and duration > settings.max_video_seconds:
                raise DownloadError(
                    f"This video is longer than the {settings.max_video_seconds // 3600}-hour limit."
                )
    except DownloadError:
        raise
    except Exception as exc:
        raise DownloadError(f"Could not download the video: {exc}") from exc

    videos = sorted(job_dir.glob("source.*"))
    if not videos:
        raise DownloadError("The download completed without producing a video file.")
    return videos[0]
