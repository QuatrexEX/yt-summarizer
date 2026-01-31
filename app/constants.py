"""アプリケーション定数"""

# アプリ設定
APP_NAME = "YT Summarizer"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "1400x800"
WINDOW_MIN_SIZE = (1000, 650)

# 動画リスト
MAX_VIDEOS = 50
THUMBNAIL_SIZE = (88, 50)

# フォント設定
FONT_SCALE_MIN = 50
FONT_SCALE_MAX = 200
FONT_SCALE_STEP = 10
FONT_SCALE_DEFAULT = 100
BASE_FONT_SIZE = 12

# カラーパレット - Refined Editorial Style
COLORS = {
    # Primary - Deep Indigo
    "primary": "#0D1B2A",       # 深いインディゴ（ヘッダー）
    "primary_light": "#1B263B", # ライトインディゴ（ボタンホバー）

    # Accent - Vibrant Coral/Orange
    "accent": "#E85D04",        # コーラルオレンジ（アクセント）
    "accent_hover": "#DC2F02",  # ディープオレンジ（ホバー）
    "accent_light": "#FFF1E6",  # ライトコーラル（選択背景）

    # Surface - Warm Neutrals
    "background": "#F8F9FA",    # オフホワイト背景
    "surface": "#FFFFFF",       # ピュアホワイト
    "surface_alt": "#F1F3F4",   # グレイッシュホワイト
    "surface_elevated": "#FFFFFF",  # カード背景

    # Text - Sharp Contrast
    "text": "#1A1A2E",          # ディープネイビー（メイン）
    "text_secondary": "#4A4E69",# スレートグレー（サブ）
    "text_muted": "#9A8C98",    # モーブグレー（ミュート）
    "text_inverse": "#FFFFFF",  # 白テキスト

    # Borders & States
    "border": "#E5E5E5",        # ソフトグレーボーダー
    "border_focus": "#E85D04",  # フォーカスボーダー
    "selected": "#FFF4ED",      # 選択背景（ウォームティント）
    "hover": "#FDF6F0",         # ホバー背景（ウォームティント）

    # Semantic
    "success": "#2D6A4F",       # フォレストグリーン
    "success_light": "#D8F3DC", # ライトグリーン
    "warning": "#E85D04",       # オレンジ
    "error": "#9D0208",         # ディープレッド
}

# パネルサイズ
SIDEBAR_WIDTH = 320
SUMMARY_PANEL_MIN_WIDTH = 400
TRANSCRIPT_PANEL_MIN_WIDTH = 350
