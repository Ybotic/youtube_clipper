import shutil
from collections.abc import Callable
from pathlib import Path

from backend.services.clip_detector import find_best_clips
from backend.services.downloader import download_video
from backend.services.transcription import transcribe
from backend.services.video_editor import render_clip
from backend.settings import settings


def run_pipeline(
    job_id: str,
    youtube_url: str,
    job_dir: Path,
    output_dir: Path,
    update: Callable[[str, str], None],
    attention_gameplay: str = "none",
) -> list[dict]:
    gameplay_asset = _gameplay_asset(attention_gameplay)
    update("downloading", "Downloading video")
    source = download_video(youtube_url, job_dir)

    update("transcribing", "Transcribing audio")
    transcript = transcribe(source, job_dir / "transcript.json")

    update("finding_moments", "Finding best moments")
    selected = find_best_clips(transcript)

    update("creating_clips", "Creating vertical clips")
    job_output = output_dir / job_id
    job_output.mkdir(parents=True, exist_ok=True)
    results = []
    for index, clip in enumerate(selected, start=1):
        update("adding_captions", f"Adding captions to clip {index} of {len(selected)}")
        output_path = job_output / f"clip_{index}.mp4"
        subtitle_path = job_dir / f"clip_{index}.ass"
        render_clip(
            source,
            transcript,
            clip.start,
            clip.end,
            output_path,
            subtitle_path,
            gameplay_asset=gameplay_asset,
        )
        results.append(
            {
                "id": index,
                "title": clip.title,
                "reason": clip.reason,
                "score": clip.score,
                "start": clip.start,
                "end": clip.end,
                "url": f"/api/clips/{job_id}/clip_{index}.mp4",
            }
        )

    shutil.rmtree(job_dir, ignore_errors=True)
    return results


def _gameplay_asset(selection: str) -> Path | None:
    if selection == "none":
        return None
    filenames = {
        "subway_surfer": "subway_surfer.mp4",
        "minecraft_parkour": "minecraft_parkour.mp4",
    }
    filename = filenames.get(selection)
    if filename is None:
        raise ValueError("Unsupported attention gameplay selection.")
    asset = settings.gameplay_dir / filename
    if not asset.is_file():
        raise FileNotFoundError(
            f"Gameplay asset is missing: assets/gameplay/{filename}. Add the video locally and try again."
        )
    return asset
