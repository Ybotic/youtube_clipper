from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-5.6-luna")
    whisper_model: str = os.getenv("WHISPER_MODEL", "base")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "auto")
    max_video_seconds: int = int(os.getenv("MAX_VIDEO_SECONDS", "7200"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    ffmpeg_binary: str = os.getenv(
        "FFMPEG_BINARY",
        str(ROOT_DIR / ".tools" / "bin" / "ffmpeg")
        if (ROOT_DIR / ".tools" / "bin" / "ffmpeg").is_file()
        else "ffmpeg",
    )
    temp_dir: Path = ROOT_DIR / "temp"
    output_dir: Path = ROOT_DIR / "output"


settings = Settings()
settings.temp_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)

if settings.ffmpeg_binary != "ffmpeg":
    ffmpeg_dir = str(Path(settings.ffmpeg_binary).resolve().parent)
    os.environ["PATH"] = os.pathsep.join(
        part for part in (ffmpeg_dir, os.environ.get("PATH", "")) if part
    )
