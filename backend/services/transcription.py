import json
from pathlib import Path
from threading import Lock
from typing import Any

from backend.settings import settings


class TranscriptionError(RuntimeError):
    pass


_model = None
_model_lock = Lock()


def _get_model():
    global _model
    with _model_lock:
        if _model is None:
            try:
                import whisper

                _model = whisper.load_model(settings.whisper_model)
            except Exception as exc:
                raise TranscriptionError(f"Could not load Whisper: {exc}") from exc
    return _model


def transcribe(video_path: Path, transcript_path: Path) -> dict[str, Any]:
    try:
        result = _get_model().transcribe(
            str(video_path), word_timestamps=True, verbose=False
        )
    except TranscriptionError:
        raise
    except Exception as exc:
        raise TranscriptionError(f"Transcription failed: {exc}") from exc

    segments = []
    for segment in result.get("segments", []):
        words = [
            {
                "word": str(word.get("word", "")).strip(),
                "start": float(word.get("start", segment["start"])),
                "end": float(word.get("end", segment["end"])),
            }
            for word in segment.get("words", [])
            if str(word.get("word", "")).strip()
        ]
        segments.append(
            {
                "start": float(segment["start"]),
                "end": float(segment["end"]),
                "text": str(segment.get("text", "")).strip(),
                "words": words,
            }
        )

    if not segments:
        raise TranscriptionError("The video did not contain usable speech.")

    transcript = {"segments": segments}
    transcript_path.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
    return transcript
