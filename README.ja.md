# YT Summarizer

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **[English](README.md)** | **[한국어](README.ko.md)** | **[简体中文](README.zh-CN.md)** | **[Español](README.es.md)** | **[Português](README.pt.md)**

YouTube動画の字幕を取得し、Gemini APIを使用してAI要約を生成するデスクトップアプリケーションです。

## 機能

- **字幕自動取得**: YouTube動画の字幕を自動で取得（多言語対応）
- **AI要約生成**: Google Gemini 2.5 Flashを使用した簡潔な要約
- **多言語対応**: 6言語のインターフェース（日本語、英語、韓国語、中国語、スペイン語、ポルトガル語）
- **動画管理**: サムネイル付きで複数の動画を保存・管理
- **マークダウン表示**: 要約はフォーマットされたマークダウンで表示
- **文字サイズ調整**: Ctrl+マウスホイールで拡大縮小（50%〜200%）

## 動作要件

- Python 3.10以上
- Gemini APIキー（[Google AI Studioで取得](https://aistudio.google.com/app/apikey)）

## インストール

1. リポジトリをクローン:
```bash
git clone https://github.com/QuatrexEX/yt-summarizer.git
cd yt-summarizer
```

2. 依存関係をインストール:
```bash
pip install -r requirements.txt
```

3. アプリケーションを起動:
```bash
python yt-summarizer.py
```

Windowsの場合は `yt-summarizer.bat` をダブルクリックでも起動できます。

## 使い方

1. 右上の**設定**ボタンをクリックし、Gemini APIキーを入力
2. 入力欄にYouTube URLを貼り付けて**+**ボタンで動画を追加
3. リストから動画を選択（字幕が自動で取得されます）
4. **生成**ボタンをクリックしてAI要約を作成
5. **YouTubeで見る**をクリックして動画を視聴

## プロジェクト構成

```
yt-summarizer/
├── yt-summarizer.py       # メインアプリケーション
├── yt-summarizer.bat      # Windows起動用
├── app/
│   ├── constants.py       # アプリケーション定数
│   ├── models/            # データモデル
│   │   └── video.py       # Video, Storeクラス
│   ├── services/          # ビジネスロジック
│   │   ├── youtube.py     # YouTubeユーティリティ
│   │   ├── transcript.py  # 字幕取得
│   │   └── gemini.py      # Gemini API連携
│   └── i18n/              # 国際化
│       ├── __init__.py    # I18nManager
│       └── locales/       # 翻訳ファイル
├── data/                  # ローカルデータ（gitignore）
│   ├── videos.json        # 動画リスト
│   ├── settings.json      # ユーザー設定
│   └── summaries/         # 生成された要約
└── requirements.txt
```

## 対応言語

| 言語 | コード |
|------|--------|
| 日本語 | ja |
| 英語 | en |
| 韓国語 | ko |
| 中国語（簡体字） | zh-CN |
| スペイン語 | es |
| ポルトガル語 | pt |

## 依存ライブラリ

- `youtube-transcript-api` - YouTube字幕取得
- `google-generativeai` - Google Gemini APIクライアント
- `Pillow` - サムネイル画像処理
- `requests` - HTTPリクエスト

## ライセンス

MITライセンス - 詳細は [LICENSE](LICENSE) を参照してください。

## コントリビューション

プルリクエストは大歓迎です！お気軽にご参加ください。
