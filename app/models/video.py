"""動画データモデル"""
import json
import re
import base64
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

_SAFE_ID_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


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
    # 字幕はメモリキャッシュのみ（永続化しない）
    transcript: Optional[list[TranscriptEntry]] = None

    def to_dict(self) -> dict:
        """永続化用（字幕は含めない）"""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "thumbnail": self.thumbnail,
            "added_at": self.added_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Video":
        return cls(
            id=data["id"],
            url=data["url"],
            title=data["title"],
            thumbnail=data["thumbnail"],
            added_at=data.get("added_at", datetime.now().isoformat()),
        )


class SettingsStore:
    """設定の永続化管理"""

    def __init__(self, settings_path: Path):
        self.settings_path = settings_path
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._settings: dict = {}
        self.load()

    def load(self):
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[WARN] Failed to load settings: {e}")
                self._settings = {}
        else:
            self._settings = {}

    def save(self):
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        value = self._settings.get(key, default)
        if key == "api_key" and value:
            try:
                return base64.b64decode(value.encode()).decode()
            except Exception:
                return value  # 平文のまま返す（移行対応）
        return value

    def set(self, key: str, value):
        if key == "api_key" and value:
            value = base64.b64encode(value.encode()).decode()
        self._settings[key] = value
        self.save()


class SummaryStore:
    """要約の永続化管理（1動画1ファイル）"""

    def __init__(self, summaries_dir: Path):
        self.summaries_dir = summaries_dir
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, video_id: str) -> Path:
        """動画IDから要約ファイルのパスを取得"""
        if not _SAFE_ID_RE.match(video_id):
            raise ValueError(f"Invalid video ID for file path: {video_id}")
        return self.summaries_dir / f"{video_id}.md"

    def get(self, video_id: str) -> Optional[str]:
        """要約を取得"""
        try:
            file_path = self._get_file_path(video_id)
        except ValueError as e:
            print(f"[WARN] {e}")
            return None
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                print(f"[WARN] Failed to read summary: {e}")
                return None
        return None

    def set(self, video_id: str, summary: str):
        """要約を保存"""
        file_path = self._get_file_path(video_id)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(summary)

    def remove(self, video_id: str):
        """要約を削除"""
        file_path = self._get_file_path(video_id)
        if file_path.exists():
            file_path.unlink()


class VideoStore:
    """動画リストの永続化管理"""

    MAX_VIDEOS = 50

    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.videos: list[Video] = []
        self._index: dict[str, int] = {}
        # 字幕キャッシュ（メモリのみ）
        self._transcript_cache: dict[str, list[TranscriptEntry]] = {}
        self.load()

    def _rebuild_index(self):
        """動画IDからインデックスへのマップを再構築"""
        self._index = {v.id: i for i, v in enumerate(self.videos)}

    def load(self):
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.videos = [Video.from_dict(v) for v in data]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[WARN] Failed to load videos: {e}")
                self.videos = []
        else:
            self.videos = []
        self._rebuild_index()

    def save(self):
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump([v.to_dict() for v in self.videos], f, ensure_ascii=False, indent=2)

    def add(self, video: Video):
        """動画を追加（最大50件、先頭に追加）"""
        # 既存の場合は追加しない
        if video.id in self._index:
            return

        # 先頭に追加
        self.videos.insert(0, video)

        # 50件を超えたら古いものを削除
        if len(self.videos) > self.MAX_VIDEOS:
            removed = self.videos[self.MAX_VIDEOS:]
            self.videos = self.videos[:self.MAX_VIDEOS]
            # 削除された動画の字幕キャッシュもクリア
            for v in removed:
                self._transcript_cache.pop(v.id, None)

        self._rebuild_index()
        self.save()

    def remove(self, video_id: str):
        self.videos = [v for v in self.videos if v.id != video_id]
        self._transcript_cache.pop(video_id, None)
        self._rebuild_index()
        self.save()

    def move_to_top(self, video_id: str):
        """動画をリストの最上位に移動"""
        idx = self._index.get(video_id)
        if idx is not None and idx > 0:
            video = self.videos.pop(idx)
            self.videos.insert(0, video)
            self._rebuild_index()
            self.save()

    def get(self, video_id: str) -> Optional[Video]:
        idx = self._index.get(video_id)
        if idx is not None:
            v = self.videos[idx]
            # キャッシュから字幕を復元
            v.transcript = self._transcript_cache.get(video_id)
            return v
        return None

    def set_transcript(self, video_id: str, transcript: list[TranscriptEntry]):
        """字幕をキャッシュに保存"""
        self._transcript_cache[video_id] = transcript
        # Videoオブジェクトにも設定
        for v in self.videos:
            if v.id == video_id:
                v.transcript = transcript
                break

    def get_transcript(self, video_id: str) -> Optional[list[TranscriptEntry]]:
        """キャッシュから字幕を取得"""
        return self._transcript_cache.get(video_id)
