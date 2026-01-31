# YT Summarizer

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **[English](README.md)** | **[日本語](README.ja.md)** | **[한국어](README.ko.md)** | **[Español](README.es.md)** | **[Português](README.pt.md)**

一款桌面应用程序，可获取YouTube视频字幕并使用Gemini API生成AI摘要。

## 功能

- **自动获取字幕**: 自动获取YouTube视频字幕（支持多语言）
- **AI摘要生成**: 使用Google Gemini 2.5 Flash生成简洁摘要
- **多语言支持**: 支持6种语言界面（日语、英语、韩语、中文、西班牙语、葡萄牙语）
- **视频管理**: 保存和管理带缩略图的多个视频
- **Markdown渲染**: 摘要以格式化的Markdown显示
- **字体大小调整**: Ctrl+鼠标滚轮缩放（50%-200%）

## 系统要求

- Python 3.10或更高版本
- Gemini API密钥（[从Google AI Studio获取](https://aistudio.google.com/app/apikey)）

## 安装

1. 克隆仓库:
```bash
git clone https://github.com/QuatrexEX/yt-summarizer.git
cd yt-summarizer
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 运行应用:
```bash
python yt-summarizer.py
```

在Windows上，也可以双击 `yt-summarizer.bat`

## 使用方法

1. 点击右上角的**设置**按钮，输入Gemini API密钥
2. 在输入框中粘贴YouTube网址，点击**+**添加视频
3. 从列表中选择视频（字幕将自动获取）
4. 点击**生成**按钮创建AI摘要
5. 点击**在YouTube观看**查看视频

## 项目结构

```
yt-summarizer/
├── yt-summarizer.py       # 主应用程序
├── yt-summarizer.bat      # Windows启动器
├── app/
│   ├── constants.py       # 应用程序常量
│   ├── models/            # 数据模型
│   │   └── video.py       # Video, Store类
│   ├── services/          # 业务逻辑
│   │   ├── youtube.py     # YouTube工具
│   │   ├── transcript.py  # 字幕获取
│   │   └── gemini.py      # Gemini API集成
│   └── i18n/              # 国际化
│       ├── __init__.py    # I18nManager
│       └── locales/       # 翻译文件
├── data/                  # 本地数据（gitignore）
│   ├── videos.json        # 视频列表
│   ├── settings.json      # 用户设置
│   └── summaries/         # 生成的摘要
└── requirements.txt
```

## 支持的语言

| 语言 | 代码 |
|------|------|
| 日语 | ja |
| 英语 | en |
| 韩语 | ko |
| 中文（简体） | zh-CN |
| 西班牙语 | es |
| 葡萄牙语 | pt |

## 依赖项

- `youtube-transcript-api` - 获取YouTube字幕
- `google-generativeai` - Google Gemini API客户端
- `Pillow` - 缩略图处理
- `requests` - HTTP请求

## 许可证

MIT许可证 - 详情请参阅 [LICENSE](LICENSE)。

## 贡献

欢迎提交Pull Request！
