# YT Summarizer

YouTube動画の視聴とAI要約を組み合わせたデスクトップアプリケーション

## 機能

- YouTube動画の埋め込み再生
- 動画の字幕取得
- Gemini AIによる動画要約生成
- 動画リストの管理・保存

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/yt-summarizer.git
cd yt-summarizer

# 依存関係をインストール
pip install -r requirements.txt
```

## 使い方

```bash
# アプリを起動
python main.py
```

1. 右上の設定アイコンからGemini APIキーを設定
2. 左側のURL入力欄にYouTube動画のURLを貼り付けて追加
3. 動画を選択
4. 「字幕」タブで字幕を取得
5. 「要約」タブで要約を生成

## APIキーの取得

Gemini APIキーは [Google AI Studio](https://aistudio.google.com/app/apikey) で無料で取得できます。

## 技術スタック

- **言語**: Python 3.10+
- **GUI**: Flet
- **AI**: Gemini 2.5 Flash API
- **字幕取得**: youtube-transcript-api

## ライセンス

MIT License
