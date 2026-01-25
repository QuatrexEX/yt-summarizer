"""Gemini API サービス"""
import google.generativeai as genai
from typing import Optional


_api_key: Optional[str] = None


def set_api_key(api_key: str):
    """APIキーを設定"""
    global _api_key
    _api_key = api_key
    genai.configure(api_key=api_key)


def get_api_key() -> Optional[str]:
    """現在のAPIキーを取得"""
    return _api_key


def summarize_transcript(transcript_text: str) -> str:
    """字幕テキストを要約"""
    if not _api_key:
        raise Exception("Gemini APIキーが設定されていません")

    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""以下はYouTube動画の字幕テキストです。この動画の内容を日本語で分かりやすく要約してください。

要約のフォーマット:
- まず動画の主題を1-2文で説明
- 次に主要なポイントを箇条書きで3-5個
- 最後に結論や重要なポイントを1-2文で

字幕テキスト:
{transcript_text}"""

    response = model.generate_content(prompt)
    return response.text
