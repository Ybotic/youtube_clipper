from pathlib import Path
from typing import Any


def _ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remainder = seconds % 60
    return f"{hours}:{minutes:02d}:{remainder:05.2f}"


def _escape_ass(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def _words_in_range(transcript: dict[str, Any], start: float, end: float) -> list[dict[str, Any]]:
    words = []
    for segment in transcript["segments"]:
        for word in segment.get("words", []):
            if float(word["end"]) > start and float(word["start"]) < end:
                words.append(word)
    return words


def write_ass_file(
    transcript: dict[str, Any], clip_start: float, clip_end: float, path: Path
) -> None:
    words = _words_in_range(transcript, clip_start, clip_end)
    events = []
    chunk: list[dict[str, Any]] = []
    chunk_start = None

    for word in words:
        if chunk_start is None:
            chunk_start = max(0.0, float(word["start"]) - clip_start)
        chunk.append(word)
        relative_end = min(clip_end, float(word["end"])) - clip_start
        should_flush = len(chunk) >= 4 or relative_end - chunk_start >= 2.0
        if should_flush:
            events.append((chunk_start, max(chunk_start + 0.25, relative_end), chunk))
            chunk = []
            chunk_start = None
    if chunk and chunk_start is not None:
        relative_end = min(clip_end, float(chunk[-1]["end"])) - clip_start
        events.append((chunk_start, max(chunk_start + 0.25, relative_end), chunk))

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,76,&H00FFFFFF,&H00FFFFFF,&H90000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,2,80,80,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for start, end, group in events:
        text = " ".join(str(word["word"]).strip().upper() for word in group)
        lines.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Caption,,0,0,0,,{_escape_ass(text)}\n"
        )
    path.write_text("".join(lines), encoding="utf-8")
