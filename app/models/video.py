"""動画データモデル"""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class TranscriptEntry:
    text: str
    start: float
    duration: float


@dataclass
class Video:
    id: str
    url: str
    title: str
    thumbnail: str
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())
    summary: Optional[str] = None
    transcript: Optional[list[TranscriptEntry]] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        if self.transcript:
            data["transcript"] = [asdict(t) for t in self.transcript]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Video":
        transcript = None
        if data.get("transcript"):
            transcript = [TranscriptEntry(**t) for t in data["transcript"]]
        return cls(
            id=data["id"],
            url=data["url"],
            title=data["title"],
            thumbnail=data["thumbnail"],
            added_at=data.get("added_at", datetime.now().isoformat()),
            summary=data.get("summary"),
            transcript=transcript,
        )


class VideoStore:
    """動画リストの永続化管理"""

    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.videos: list[Video] = []
        self.load()

    def load(self):
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.videos = [Video.from_dict(v) for v in data]
            except (json.JSONDecodeError, KeyError):
                self.videos = []
        else:
            self.videos = []

    def save(self):
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump([v.to_dict() for v in self.videos], f, ensure_ascii=False, indent=2)

    def add(self, video: Video):
        if not any(v.id == video.id for v in self.videos):
            self.videos.append(video)
            self.save()

    def remove(self, video_id: str):
        self.videos = [v for v in self.videos if v.id != video_id]
        self.save()

    def update(self, video_id: str, **kwargs):
        for v in self.videos:
            if v.id == video_id:
                for key, value in kwargs.items():
                    if hasattr(v, key):
                        setattr(v, key, value)
                self.save()
                break

    def get(self, video_id: str) -> Optional[Video]:
        for v in self.videos:
            if v.id == video_id:
                return v
        return None
