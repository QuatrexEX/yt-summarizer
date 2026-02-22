"""字幕取得サービス"""
from youtube_transcript_api import YouTubeTranscriptApi
from app.models.video import TranscriptEntry


def get_transcript(video_id: str, languages: list[str] = None) -> list[TranscriptEntry]:
    """YouTube動画の字幕を取得"""
    if languages is None:
        languages = ["ja", "en"]

    try:
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id, languages=languages)

        entries = [
            TranscriptEntry(
                text=entry.text,
                start=entry.start,
                duration=entry.duration,
            )
            for entry in transcript_data
        ]

        if not entries:
            raise Exception("TRANSCRIPT_FAILED: Empty transcript returned")

        return entries
    except Exception as e:
        raise Exception(f"TRANSCRIPT_FAILED: {e}")
