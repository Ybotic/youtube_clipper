import json
from dataclasses import dataclass
from typing import Any

from backend.settings import settings


class ClipDetectionError(RuntimeError):
    pass


@dataclass
class CandidateClip:
    start: float
    end: float
    title: str
    reason: str
    score: int


def _transcript_for_prompt(transcript: dict[str, Any]) -> str:
    return "\n".join(
        f"[{segment['start']:.2f}-{segment['end']:.2f}] {segment['text']}"
        for segment in transcript["segments"]
    )


def find_best_clips(transcript: dict[str, Any]) -> list[CandidateClip]:
    if not settings.openrouter_api_key:
        raise ClipDetectionError("OPENROUTER_API_KEY is not configured.")

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "AI Clipper",
            },
        )
        response = client.chat.completions.create(
            model=settings.openrouter_model,
            temperature=0.3,
            response_format={"type": "json_object"},
            extra_body={"reasoning": {"enabled": True}},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You select high-potential short-form video moments. "
                        "Return only valid JSON with a clips array. Find exactly 5 "
                        "non-overlapping candidates when possible. Each should be "
                        "20 to 60 seconds, include enough setup and payoff, and use "
                        "timestamps from the transcript. Rank score from 0 to 100."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Choose moments with hooks, surprising statements, jokes, "
                        "emotion, useful insights, conflict, stories, reactions, "
                        "or satisfying answers. Avoid contextless fragments. You may "
                        "start a few seconds before the key line.\n\n"
                        "Required shape: {\"clips\":[{\"start\": number, "
                        "\"end\": number, \"title\": string, \"reason\": string, "
                        "\"score\": number}]}\n\n"
                        f"Transcript:\n{_transcript_for_prompt(transcript)}"
                    ),
                },
            ],
        )
        payload = json.loads(response.choices[0].message.content or "{}")
    except ClipDetectionError:
        raise
    except Exception as exc:
        raise ClipDetectionError(f"The AI clip analysis failed: {exc}") from exc

    max_time = max(float(segment["end"]) for segment in transcript["segments"])
    candidates = []
    for item in payload.get("clips", []):
        try:
            start = max(0.0, float(item["start"]))
            end = min(max_time, float(item["end"]))
            if end <= start or end - start < 10 or end - start > 75:
                continue
            candidates.append(
                CandidateClip(
                    start=start,
                    end=end,
                    title=str(item.get("title", "Untitled moment"))[:120],
                    reason=str(item.get("reason", "Strong short-form moment."))[:300],
                    score=max(0, min(100, int(item.get("score", 0)))),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue

    candidates.sort(key=lambda clip: clip.score, reverse=True)
    selected = []
    for candidate in candidates:
        if any(
            candidate.start < chosen.end and candidate.end > chosen.start
            for chosen in selected
        ):
            continue
        selected.append(candidate)
        if len(selected) == 3:
            break

    if len(selected) < 3:
        raise ClipDetectionError(
            "The AI returned fewer than 3 usable moments. Try a video with more spoken content."
        )
    return selected
