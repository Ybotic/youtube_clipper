from typing import Literal

from pydantic import BaseModel, Field


Stage = Literal[
    "queued",
    "downloading",
    "transcribing",
    "finding_moments",
    "creating_clips",
    "adding_captions",
    "finished",
    "failed",
]


class GenerateRequest(BaseModel):
    youtube_url: str = Field(min_length=1)
    attention_gameplay: Literal["none", "subway_surfer", "minecraft_parkour"] = "none"


class ClipResult(BaseModel):
    id: int
    title: str
    reason: str
    score: int
    start: float
    end: float
    url: str


class JobStatus(BaseModel):
    job_id: str
    status: Stage
    message: str
    clips: list[ClipResult] = []
    error: str | None = None
