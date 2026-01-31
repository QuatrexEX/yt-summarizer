"""YouTube関連ユーティリティ"""
import re
import urllib.request
import json
from typing import Optional


def get_video_title(video_id: str) -> str:
    """YouTube oEmbed APIから動画タイトルを取得"""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("title", f"Video {video_id}")
    except Exception:
        return f"Video {video_id}"


def extract_video_id(url: str) -> Optional[str]:
    """YouTube URLから動画IDを抽出"""
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_thumbnail_url(video_id: str) -> str:
    """動画IDからサムネイルURLを生成"""
    return f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"


def get_embed_url(video_id: str) -> str:
    """動画IDから埋め込みURLを生成"""
    return f"https://www.youtube.com/embed/{video_id}"


def format_time(seconds: float) -> str:
    """秒数を mm:ss 形式にフォーマット"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"
