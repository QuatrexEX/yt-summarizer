# YT Summarizer

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **[English](README.md)** | **[日本語](README.ja.md)** | **[简体中文](README.zh-CN.md)** | **[Español](README.es.md)** | **[Português](README.pt.md)**

YouTube 동영상 자막을 가져와 Gemini API를 사용하여 AI 요약을 생성하는 데스크톱 애플리케이션입니다.

## 기능

- **자막 자동 가져오기**: YouTube 동영상 자막 자동 추출 (다국어 지원)
- **AI 요약 생성**: Google Gemini 2.5 Flash를 사용한 간결한 요약
- **다국어 지원**: 6개 언어 인터페이스 (일본어, 영어, 한국어, 중국어, 스페인어, 포르투갈어)
- **동영상 관리**: 썸네일과 함께 여러 동영상 저장 및 관리
- **마크다운 렌더링**: 요약이 포맷된 마크다운으로 표시
- **글꼴 크기 조절**: Ctrl+마우스 휠로 확대/축소 (50%-200%)

## 요구 사항

- Python 3.10 이상
- Gemini API 키 ([Google AI Studio에서 받기](https://aistudio.google.com/app/apikey))

## 설치

1. 저장소 복제:
```bash
git clone https://github.com/QuatrexEX/yt-summarizer.git
cd yt-summarizer
```

2. 종속성 설치:
```bash
pip install -r requirements.txt
```

3. 애플리케이션 실행:
```bash
python yt-summarizer.py
```

Windows에서는 `yt-summarizer.bat`을 더블 클릭해도 됩니다.

## 사용법

1. 오른쪽 상단의 **설정** 버튼을 클릭하여 Gemini API 키 입력
2. 입력 필드에 YouTube URL을 붙여넣고 **+**를 클릭하여 동영상 추가
3. 목록에서 동영상 선택 (자막이 자동으로 가져와집니다)
4. **생성** 버튼을 클릭하여 AI 요약 생성
5. **YouTube에서 보기**를 클릭하여 동영상 시청

## 프로젝트 구조

```
yt-summarizer/
├── yt-summarizer.py       # 메인 애플리케이션
├── yt-summarizer.bat      # Windows 실행기
├── app/
│   ├── constants.py       # 애플리케이션 상수
│   ├── models/            # 데이터 모델
│   │   └── video.py       # Video, Store 클래스
│   ├── services/          # 비즈니스 로직
│   │   ├── youtube.py     # YouTube 유틸리티
│   │   ├── transcript.py  # 자막 가져오기
│   │   └── gemini.py      # Gemini API 통합
│   └── i18n/              # 국제화
│       ├── __init__.py    # I18nManager
│       └── locales/       # 번역 파일
├── data/                  # 로컬 데이터 (gitignore)
│   ├── videos.json        # 동영상 목록
│   ├── settings.json      # 사용자 설정
│   └── summaries/         # 생성된 요약
└── requirements.txt
```

## 지원 언어

| 언어 | 코드 |
|------|------|
| 일본어 | ja |
| 영어 | en |
| 한국어 | ko |
| 중국어 (간체) | zh-CN |
| 스페인어 | es |
| 포르투갈어 | pt |

## 종속성

- `youtube-transcript-api` - YouTube 자막 가져오기
- `google-generativeai` - Google Gemini API 클라이언트
- `Pillow` - 썸네일 이미지 처리
- `requests` - HTTP 요청

## 라이선스

MIT 라이선스 - 자세한 내용은 [LICENSE](LICENSE)를 참조하세요.

## 기여

풀 리퀘스트를 환영합니다! 자유롭게 참여해 주세요.
