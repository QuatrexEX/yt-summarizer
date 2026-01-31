# YT Summarizer

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **[日本語](README.ja.md)** | **[한국어](README.ko.md)** | **[简体中文](README.zh-CN.md)** | **[Español](README.es.md)** | **[Português](README.pt.md)**

A desktop application that fetches YouTube video transcripts and generates AI-powered summaries using Gemini API.

## Features

- **YouTube Transcript Fetching**: Automatically retrieves video transcripts (supports multiple languages)
- **AI-Powered Summaries**: Generates concise summaries using Google's Gemini 2.5 Flash
- **Multi-language Support**: Interface available in 6 languages (Japanese, English, Korean, Chinese, Spanish, Portuguese)
- **Video Management**: Save and manage multiple videos with thumbnails
- **Markdown Rendering**: Summaries are displayed with formatted markdown
- **Adjustable Font Size**: Ctrl+Mouse wheel to zoom in/out (50%-200%)

## Requirements

- Python 3.10 or higher
- Gemini API Key ([Get it from Google AI Studio](https://aistudio.google.com/app/apikey))

## Installation

1. Clone the repository:
```bash
git clone https://github.com/QuatrexEX/yt-summarizer.git
cd yt-summarizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python yt-summarizer.py
```

Or on Windows, double-click `yt-summarizer.bat`

## Usage

1. Click the **Settings** button (top-right) and enter your Gemini API key
2. Paste a YouTube URL in the input field and click **+** to add a video
3. Select a video from the list (transcript will be fetched automatically)
4. Click **Generate** to create an AI summary
5. Click **Watch on YouTube** to open the video

## Project Structure

```
yt-summarizer/
├── yt-summarizer.py       # Main application
├── yt-summarizer.bat      # Windows launcher
├── app/
│   ├── constants.py       # Application constants
│   ├── models/            # Data models
│   │   └── video.py       # Video, Store classes
│   ├── services/          # Business logic
│   │   ├── youtube.py     # YouTube utilities
│   │   ├── transcript.py  # Transcript fetching
│   │   └── gemini.py      # Gemini API integration
│   └── i18n/              # Internationalization
│       ├── __init__.py    # I18nManager
│       └── locales/       # Translation files
├── data/                  # Local data (gitignored)
│   ├── videos.json        # Video list
│   ├── settings.json      # User settings
│   └── summaries/         # Generated summaries
└── requirements.txt
```

## Supported Languages

| Language | Code |
|----------|------|
| Japanese | ja |
| English | en |
| Korean | ko |
| Chinese (Simplified) | zh-CN |
| Spanish | es |
| Portuguese | pt |

## Dependencies

- `youtube-transcript-api` - Fetches YouTube transcripts
- `google-generativeai` - Google Gemini API client
- `Pillow` - Image processing for thumbnails
- `requests` - HTTP requests

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
