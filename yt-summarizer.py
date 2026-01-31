"""YT Summarizer - YouTube動画要約アプリ (tkinter版)"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
import threading
import re
from pathlib import Path
from io import BytesIO
import requests
from PIL import Image, ImageTk

from app.models.video import Video, VideoStore, SummaryStore, SettingsStore
from app.services.youtube import extract_video_id, get_thumbnail_url, get_video_title, format_time
from app.services.transcript import get_transcript
from app.services.gemini import summarize_transcript, set_api_key, get_api_key
from app.i18n import I18nManager
from app.constants import (
    COLORS, WINDOW_SIZE, WINDOW_MIN_SIZE,
    FONT_SCALE_MIN, FONT_SCALE_MAX, FONT_SCALE_STEP,
    FONT_SCALE_DEFAULT, BASE_FONT_SIZE, THUMBNAIL_SIZE
)


class YTSummarizer:
    """YouTube動画要約アプリケーション"""

    # 定数をクラス変数として参照
    COLORS = COLORS

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(*WINDOW_MIN_SIZE)
        self.root.configure(bg=self.COLORS["background"])

        # データストア
        data_dir = Path(__file__).parent / "data"
        self.video_store = VideoStore(data_dir / "videos.json")
        self.summary_store = SummaryStore(data_dir / "summaries")
        self.settings = SettingsStore(data_dir / "settings.json")

        # i18n初期化
        i18n_dir = Path(__file__).parent / "app" / "i18n" / "locales"
        self.i18n = I18nManager(i18n_dir, default_language="ja")
        saved_language = self.settings.get("language", "ja")
        self.i18n.set_language(saved_language)

        # ウィンドウタイトル設定
        self.root.title(self.i18n.t("ui.app_title"))

        # 状態
        self.current_video_id: str | None = None
        self.font_scale = self.settings.get("font_scale", FONT_SCALE_DEFAULT)
        self.thumbnail_cache: dict[str, ImageTk.PhotoImage] = {}

        # APIキー復元
        saved_api_key = self.settings.get("api_key", "")
        if saved_api_key:
            set_api_key(saved_api_key)

        # UI構築
        self._setup_styles()
        self._build_ui()
        self._refresh_video_list()
        self._bind_events()

        # 言語変更時のコールバック登録
        self.i18n.add_observer(self._on_language_changed)

    def _setup_styles(self):
        """スタイル設定"""
        style = ttk.Style()
        style.theme_use("clam")

        # 全体的なスタイル
        style.configure(".", background=self.COLORS["background"])

        # エントリー
        style.configure("TEntry",
                        fieldbackground=self.COLORS["surface"],
                        bordercolor=self.COLORS["border"],
                        lightcolor=self.COLORS["border"],
                        darkcolor=self.COLORS["border"],
                        padding=8)

        # セパレータ
        style.configure("TSeparator", background=self.COLORS["border"])

        # スクロールバー（より見やすく）
        style.configure("TScrollbar",
                        background="#C0C0C0",
                        troughcolor=self.COLORS["surface_alt"],
                        bordercolor=self.COLORS["border"],
                        arrowcolor=self.COLORS["text_secondary"],
                        width=14)
        style.map("TScrollbar",
                  background=[("active", "#A0A0A0"), ("pressed", "#808080")])

        # PanedWindow
        style.configure("TPanedwindow", background=self.COLORS["border"])

    def _build_ui(self):
        """UIを構築"""
        # メインコンテナ
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # ヘッダー
        self._build_header(main_container)

        # コンテンツエリア
        content = ttk.Frame(main_container)
        content.pack(fill=tk.BOTH, expand=True)

        # 左パネル（動画リスト）
        self._build_video_list_panel(content)

        # 右エリア（要約 + 字幕）
        self._build_content_panels(content)

    def _build_header(self, parent):
        """ヘッダー構築 - Refined Editorial Style"""
        header = tk.Frame(parent, bg=self.COLORS["primary"], height=56)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # 左側コンテナ
        left_container = tk.Frame(header, bg=self.COLORS["primary"])
        left_container.pack(side=tk.LEFT, padx=20, pady=10)

        # ロゴアイコン - シンプルな再生マーク
        logo = tk.Label(left_container, text="▶", bg=self.COLORS["primary"],
                        fg=self.COLORS["accent"], font=("", 20, "bold"))
        logo.pack(side=tk.LEFT, padx=(0, 10))

        # タイトル - よりシャープなフォント
        font_family = self.i18n.get_font()
        title = tk.Label(left_container, text=self.i18n.t("ui.app_title"),
                         bg=self.COLORS["primary"], fg=self.COLORS["text_inverse"],
                         font=(font_family, 17, "bold"))
        title.pack(side=tk.LEFT)

        # サブタイトル
        subtitle = tk.Label(left_container, text=self.i18n.t("ui.header.subtitle"),
                            bg=self.COLORS["primary"], fg=self.COLORS["text_muted"],
                            font=(font_family, 9))
        subtitle.pack(side=tk.LEFT, padx=(8, 0), pady=(4, 0))

        # 設定ボタン - より洗練されたスタイル
        self.settings_btn = tk.Button(header, text=f"⚙ {self.i18n.t('ui.header.settings')}",
                                  bg=self.COLORS["primary_light"],
                                  fg=self.COLORS["text_inverse"],
                                  font=(font_family, 10),
                                  relief=tk.FLAT, cursor="hand2",
                                  padx=18, pady=6,
                                  activebackground=self.COLORS["accent"],
                                  activeforeground=self.COLORS["text_inverse"],
                                  command=self._show_settings)
        self.settings_btn.pack(side=tk.RIGHT, padx=20, pady=10)

        # ホバー効果
        def on_enter(e):
            self.settings_btn.configure(bg=self.COLORS["accent"])

        def on_leave(e):
            self.settings_btn.configure(bg=self.COLORS["primary_light"])

        self.settings_btn.bind("<Enter>", on_enter)
        self.settings_btn.bind("<Leave>", on_leave)

    def _build_video_list_panel(self, parent):
        """動画リストパネル構築 - Refined Editorial Style"""
        font_family = self.i18n.get_font()
        left_panel = tk.Frame(parent, bg=self.COLORS["surface"], width=320)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        left_panel.pack_propagate(False)

        # サイドバーヘッダー - より洗練されたスタイル
        sidebar_header = tk.Frame(left_panel, bg=self.COLORS["surface"])
        sidebar_header.pack(fill=tk.X, padx=16, pady=(20, 12))

        self.video_list_label = tk.Label(sidebar_header, text=self.i18n.t("ui.sidebar.video_list"),
                 bg=self.COLORS["surface"], fg=self.COLORS["text"],
                 font=(font_family, 14, "bold"))
        self.video_list_label.pack(side=tk.LEFT)

        # 動画数バッジ
        video_count_text = self.i18n.t("ui.sidebar.video_count", count=len(self.video_store.videos))
        self.video_count_label = tk.Label(sidebar_header, text=video_count_text,
                                           bg=self.COLORS["accent_light"],
                                           fg=self.COLORS["accent"],
                                           font=(font_family, 9, "bold"),
                                           padx=8, pady=2)
        self.video_count_label.pack(side=tk.RIGHT)

        # URL入力エリア
        input_frame = tk.Frame(left_panel, bg=self.COLORS["surface"])
        input_frame.pack(fill=tk.X, padx=16, pady=(0, 16))

        # 入力フィールドコンテナ - より目立つボーダー
        self.url_entry_container = tk.Frame(input_frame, bg=self.COLORS["border"])
        self.url_entry_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry_inner = tk.Frame(self.url_entry_container, bg=self.COLORS["surface_alt"])
        entry_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.url_entry = tk.Entry(entry_inner, font=(font_family, 10),
                                   relief=tk.FLAT, bg=self.COLORS["surface_alt"],
                                   fg=self.COLORS["text"],
                                   insertbackground=self.COLORS["accent"])
        self.url_entry.pack(fill=tk.X, padx=12, pady=10)
        self.url_entry.bind("<Return>", lambda e: self._add_video())

        # プレースホルダー
        self.url_placeholder = self.i18n.t("ui.sidebar.url_placeholder")
        self.url_entry.insert(0, self.url_placeholder)
        self.url_entry.configure(fg=self.COLORS["text_muted"])

        def on_focus_in(e):
            if self.url_entry.get() == self.url_placeholder:
                self.url_entry.delete(0, tk.END)
                self.url_entry.configure(fg=self.COLORS["text"])
            self.url_entry_container.configure(bg=self.COLORS["accent"])

        def on_focus_out(e):
            if not self.url_entry.get():
                self.url_entry.insert(0, self.url_placeholder)
                self.url_entry.configure(fg=self.COLORS["text_muted"])
            self.url_entry_container.configure(bg=self.COLORS["border"])

        self.url_entry.bind("<FocusIn>", on_focus_in)
        self.url_entry.bind("<FocusOut>", on_focus_out)

        # 追加ボタン - より目立つスタイル
        add_btn = tk.Button(input_frame, text="+", font=("Segoe UI", 16, "bold"),
                            bg=self.COLORS["accent"], fg=self.COLORS["text_inverse"],
                            relief=tk.FLAT, cursor="hand2", width=3,
                            activebackground=self.COLORS["accent_hover"],
                            activeforeground=self.COLORS["text_inverse"],
                            command=self._add_video)
        add_btn.pack(side=tk.RIGHT, padx=(12, 0))

        # ホバー効果
        def on_btn_enter(e):
            add_btn.configure(bg=self.COLORS["accent_hover"])

        def on_btn_leave(e):
            add_btn.configure(bg=self.COLORS["accent"])

        add_btn.bind("<Enter>", on_btn_enter)
        add_btn.bind("<Leave>", on_btn_leave)

        # 区切り線
        separator = tk.Frame(left_panel, bg=self.COLORS["border"], height=1)
        separator.pack(fill=tk.X, padx=16)

        # 動画リスト（スクロール可能）
        list_container = tk.Frame(left_panel, bg=self.COLORS["surface"])
        list_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=10)

        canvas = tk.Canvas(list_container, bg=self.COLORS["surface"],
                           highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=canvas.yview)

        self.video_list_frame = tk.Frame(canvas, bg=self.COLORS["surface"])
        self.video_list_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=self.video_list_frame, anchor=tk.NW, width=290)
        canvas.configure(yscrollcommand=scrollbar.set)

        # スクロールバーを先にpackして確実にスペースを確保
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.video_list_canvas = canvas

        # マウスホイールスクロール（動画リスト専用）
        def _on_video_list_scroll(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")
            return "break"

        def _bind_video_list_scroll(event):
            canvas.bind("<MouseWheel>", _on_video_list_scroll)

        def _unbind_video_list_scroll(event):
            canvas.unbind("<MouseWheel>")

        canvas.bind("<Enter>", _bind_video_list_scroll)
        canvas.bind("<Leave>", _unbind_video_list_scroll)
        self.video_list_frame.bind("<Enter>", _bind_video_list_scroll)
        self.video_list_frame.bind("<Leave>", _unbind_video_list_scroll)

        # 右側との区切り - より繊細
        right_separator = tk.Frame(parent, bg=self.COLORS["border"], width=1)
        right_separator.pack(side=tk.LEFT, fill=tk.Y)

    def _build_content_panels(self, parent):
        """コンテンツパネル（要約 + 字幕）構築 - Refined Editorial Style"""
        font_family = self.i18n.get_font()
        right_area = tk.Frame(parent, bg=self.COLORS["background"])
        right_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # タイトルバー - より存在感のあるデザイン
        title_frame = tk.Frame(right_area, bg=self.COLORS["surface"])
        title_frame.pack(fill=tk.X, padx=0, pady=0)

        title_inner = tk.Frame(title_frame, bg=self.COLORS["surface"])
        title_inner.pack(fill=tk.X, padx=24, pady=18)

        self.video_title_label = tk.Label(title_inner, text=self.i18n.t("ui.content.select_video"),
                                           font=(font_family, 16, "bold"),
                                           bg=self.COLORS["surface"],
                                           fg=self.COLORS["text"],
                                           anchor=tk.W, wraplength=850)
        self.video_title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # YouTubeリンクボタン - より目立つスタイル
        self.youtube_link = tk.Label(title_inner, text=f"▶ {self.i18n.t('ui.content.watch_on_youtube')}",
                                      fg=self.COLORS["accent"],
                                      bg=self.COLORS["surface"],
                                      cursor="hand2",
                                      font=(font_family, 10, "bold"))
        self.youtube_link.pack(side=tk.RIGHT, padx=(20, 0))
        self.youtube_link.bind("<Button-1>", lambda e: self._open_youtube())

        # ホバー効果
        def on_link_enter(e):
            self.youtube_link.configure(fg=self.COLORS["accent_hover"])

        def on_link_leave(e):
            self.youtube_link.configure(fg=self.COLORS["accent"])

        self.youtube_link.bind("<Enter>", on_link_enter)
        self.youtube_link.bind("<Leave>", on_link_leave)

        # 区切り線
        separator = tk.Frame(right_area, bg=self.COLORS["border"], height=1)
        separator.pack(fill=tk.X)

        # 要約 + 字幕パネル
        panels = tk.Frame(right_area, bg=self.COLORS["background"])
        panels.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # PanedWindowで分割
        paned = ttk.PanedWindow(panels, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # 要約パネル
        summary_panel = self._build_summary_panel(paned)
        paned.add(summary_panel, weight=1)

        # 字幕パネル
        transcript_panel = self._build_transcript_panel(paned)
        paned.add(transcript_panel, weight=1)

        # フッター
        footer = tk.Frame(right_area, bg=self.COLORS["background"])
        footer.pack(fill=tk.X, padx=24, pady=(0, 16))

        self.font_scale_label = tk.Label(footer,
                                          text=self.i18n.t("ui.content.font_size", scale=self.font_scale),
                                          bg=self.COLORS["background"],
                                          fg=self.COLORS["text_muted"],
                                          font=(font_family, 9))
        self.font_scale_label.pack(side=tk.RIGHT)

    def _build_summary_panel(self, parent) -> ttk.Frame:
        """要約パネル構築 - Refined Editorial Style"""
        font_family = self.i18n.get_font()

        # 外枠（カード風デザイン） - シャドウ効果を模倣
        outer = tk.Frame(parent, bg=self.COLORS["border"])
        outer_inner = tk.Frame(outer, bg=self.COLORS["surface"])
        outer_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        frame = tk.Frame(outer_inner, bg=self.COLORS["surface"])
        frame.pack(fill=tk.BOTH, expand=True)

        # ヘッダー - より洗練されたデザイン
        header = tk.Frame(frame, bg=self.COLORS["surface"])
        header.pack(fill=tk.X, padx=20, pady=14)

        # ラベルとアイコン
        label_frame = tk.Frame(header, bg=self.COLORS["surface"])
        label_frame.pack(side=tk.LEFT)

        # アクセントバー（左側のカラーインジケーター）
        accent_bar = tk.Frame(label_frame, bg=self.COLORS["accent"], width=4)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        self.summary_title_label = tk.Label(label_frame, text=self.i18n.t("ui.summary_panel.title"),
                 font=(font_family, 14, "bold"),
                 bg=self.COLORS["surface"],
                 fg=self.COLORS["text"])
        self.summary_title_label.pack(side=tk.LEFT)

        # 生成ボタン - より目立つスタイル
        self.generate_btn = tk.Button(header, text=f"✨ {self.i18n.t('ui.summary_panel.generate')}",
                                       bg=self.COLORS["accent"],
                                       fg=self.COLORS["text_inverse"],
                                       font=(font_family, 10, "bold"),
                                       relief=tk.FLAT,
                                       cursor="hand2",
                                       padx=16, pady=6,
                                       activebackground=self.COLORS["accent_hover"],
                                       activeforeground=self.COLORS["text_inverse"],
                                       command=self._generate_summary)
        self.generate_btn.pack(side=tk.RIGHT)

        # ホバー効果
        def on_gen_enter(e):
            if self.generate_btn["state"] != tk.DISABLED:
                self.generate_btn.configure(bg=self.COLORS["accent_hover"])

        def on_gen_leave(e):
            if self.generate_btn["state"] != tk.DISABLED:
                self.generate_btn.configure(bg=self.COLORS["accent"])

        self.generate_btn.bind("<Enter>", on_gen_enter)
        self.generate_btn.bind("<Leave>", on_gen_leave)

        # 区切り線
        separator = tk.Frame(frame, bg=self.COLORS["border"], height=1)
        separator.pack(fill=tk.X, padx=20)

        # テキストエリア
        text_frame = tk.Frame(frame, bg=self.COLORS["surface"])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        self.summary_text = tk.Text(text_frame, wrap=tk.WORD,
                                     font=(font_family, self._get_font_size()),
                                     relief=tk.FLAT,
                                     bg=self.COLORS["surface_alt"],
                                     fg=self.COLORS["text"],
                                     padx=18, pady=14,
                                     borderwidth=0,
                                     highlightthickness=1,
                                     highlightbackground=self.COLORS["border"],
                                     highlightcolor=self.COLORS["accent"],
                                     spacing1=6,
                                     spacing2=8,
                                     spacing3=10,
                                     height=1)
        summary_scroll = ttk.Scrollbar(text_frame, command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scroll.set)

        # スクロールバーを先にpackして確実にスペースを確保
        summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.summary_text.insert("1.0", self.i18n.t("ui.content.select_video"))
        self.summary_text.configure(state=tk.DISABLED)

        # Ctrl+ホイールでフォントサイズ変更
        self.summary_text.bind("<Control-MouseWheel>", self._on_font_scale)

        # マウスホイールスクロール（要約エリア専用）
        def _on_summary_scroll(event):
            self.summary_text.yview_scroll(-1 * (event.delta // 120), "units")
            return "break"

        self.summary_text.bind("<MouseWheel>", _on_summary_scroll)

        return outer

    def _build_transcript_panel(self, parent) -> ttk.Frame:
        """字幕パネル構築 - Refined Editorial Style"""
        font_family = self.i18n.get_font()

        # 外枠（カード風デザイン）
        outer = tk.Frame(parent, bg=self.COLORS["border"])
        outer_inner = tk.Frame(outer, bg=self.COLORS["surface"])
        outer_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        frame = tk.Frame(outer_inner, bg=self.COLORS["surface"])
        frame.pack(fill=tk.BOTH, expand=True)

        # ヘッダー - より洗練されたデザイン
        header = tk.Frame(frame, bg=self.COLORS["surface"])
        header.pack(fill=tk.X, padx=20, pady=14)

        # ラベルとアイコン
        label_frame = tk.Frame(header, bg=self.COLORS["surface"])
        label_frame.pack(side=tk.LEFT)

        # アクセントバー（左側のカラーインジケーター）- 字幕用は別色
        accent_bar = tk.Frame(label_frame, bg=self.COLORS["text_secondary"], width=4)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        self.transcript_title_label = tk.Label(label_frame, text=self.i18n.t("ui.transcript_panel.title"),
                 font=(font_family, 14, "bold"),
                 bg=self.COLORS["surface"],
                 fg=self.COLORS["text"])
        self.transcript_title_label.pack(side=tk.LEFT)

        # 区切り線
        separator = tk.Frame(frame, bg=self.COLORS["border"], height=1)
        separator.pack(fill=tk.X, padx=20)

        # テキストエリア
        text_frame = tk.Frame(frame, bg=self.COLORS["surface"])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        self.transcript_text = tk.Text(text_frame, wrap=tk.WORD,
                                        font=(font_family, self._get_font_size()),
                                        relief=tk.FLAT,
                                        bg=self.COLORS["surface_alt"],
                                        fg=self.COLORS["text"],
                                        padx=18, pady=14,
                                        borderwidth=0,
                                        highlightthickness=1,
                                        highlightbackground=self.COLORS["border"],
                                        highlightcolor=self.COLORS["accent"],
                                        spacing1=6,
                                        spacing2=8,
                                        spacing3=10,
                                        height=1)
        transcript_scroll = ttk.Scrollbar(text_frame, command=self.transcript_text.yview)
        self.transcript_text.configure(yscrollcommand=transcript_scroll.set)

        # スクロールバーを先にpackして確実にスペースを確保
        transcript_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.transcript_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.transcript_text.insert("1.0", self.i18n.t("ui.content.select_video"))
        self.transcript_text.configure(state=tk.DISABLED)

        # タグ設定（タイムスタンプ用） - より目立つスタイル
        self.transcript_text.tag_configure("timestamp",
                                            foreground=self.COLORS["accent"],
                                            font=(font_family, self._get_font_size(), "bold"))

        # Ctrl+ホイールでフォントサイズ変更
        self.transcript_text.bind("<Control-MouseWheel>", self._on_font_scale)

        # マウスホイールスクロール（字幕エリア専用）
        def _on_transcript_scroll(event):
            self.transcript_text.yview_scroll(-1 * (event.delta // 120), "units")
            return "break"

        self.transcript_text.bind("<MouseWheel>", _on_transcript_scroll)

        return outer

    def _bind_events(self):
        """イベントバインド"""
        # ウィンドウ閉じる時
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _get_font_size(self) -> int:
        """現在のフォントサイズを計算"""
        return max(8, int(BASE_FONT_SIZE * self.font_scale / 100))

    def _configure_markdown_tags(self, text_widget: tk.Text):
        """マークダウン用タグを設定 - Refined Editorial Style"""
        size = self._get_font_size()
        font_family = self.i18n.get_font()

        # 見出しタグ - より洗練されたスタイル
        text_widget.tag_configure("h1", font=(font_family, size + 8, "bold"),
                                   foreground=self.COLORS["text"],
                                   spacing1=20, spacing2=6, spacing3=14)
        text_widget.tag_configure("h2", font=(font_family, size + 5, "bold"),
                                   foreground=self.COLORS["text"],
                                   spacing1=16, spacing2=6, spacing3=12)
        text_widget.tag_configure("h3", font=(font_family, size + 2, "bold"),
                                   foreground=self.COLORS["text_secondary"],
                                   spacing1=14, spacing2=4, spacing3=10)

        # 太字・斜体 - 太字は読みやすいフォントと色で強調
        text_widget.tag_configure("bold", font=(font_family, size, "bold"),
                                   foreground=self.COLORS["primary"])
        text_widget.tag_configure("italic", font=(font_family, size, "italic"),
                                   foreground=self.COLORS["text_secondary"])

        # 箇条書き - より余白を設定
        text_widget.tag_configure("bullet", lmargin1=24, lmargin2=40,
                                   spacing1=4, spacing2=4, spacing3=6)

        # コード - アクセントカラーを使用
        text_widget.tag_configure("code", font=("Consolas", size - 1),
                                   background=self.COLORS["surface_alt"],
                                   foreground=self.COLORS["accent"])

        # 区切り線
        text_widget.tag_configure("hr", foreground=self.COLORS["border"], justify=tk.CENTER,
                                   spacing1=12, spacing3=12)

    def _render_markdown(self, text_widget: tk.Text, markdown_text: str):
        """マークダウンテキストをレンダリング"""
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)

        self._configure_markdown_tags(text_widget)

        lines = markdown_text.split("\n")
        for i, line in enumerate(lines):
            # 見出し
            if line.startswith("### "):
                text_widget.insert(tk.END, line[4:] + "\n", "h3")
            elif line.startswith("## "):
                text_widget.insert(tk.END, line[3:] + "\n", "h2")
            elif line.startswith("# "):
                text_widget.insert(tk.END, line[2:] + "\n", "h1")
            # 区切り線
            elif line.strip() in ["---", "***", "___"]:
                text_widget.insert(tk.END, "─" * 50 + "\n", "hr")
            # 箇条書き
            elif line.strip().startswith("- ") or line.strip().startswith("* "):
                content = line.strip()[2:]
                self._insert_inline_markdown(text_widget, "• " + content, "bullet")
                text_widget.insert(tk.END, "\n")
            # 番号付きリスト
            elif re.match(r'^\d+\.\s', line.strip()):
                content = re.sub(r'^\d+\.\s', '', line.strip())
                num = re.match(r'^(\d+)\.\s', line.strip()).group(1)
                self._insert_inline_markdown(text_widget, f"{num}. " + content, "bullet")
                text_widget.insert(tk.END, "\n")
            # 通常テキスト
            else:
                self._insert_inline_markdown(text_widget, line)
                text_widget.insert(tk.END, "\n")

        text_widget.configure(state=tk.DISABLED)

    def _insert_inline_markdown(self, text_widget: tk.Text, text: str, base_tag: str = None):
        """インラインマークダウン（太字、斜体、コード）を処理"""
        # パターン: **太字**, *斜体*, `コード`
        patterns = [
            (r'\*\*(.+?)\*\*', 'bold'),
            (r'\*(.+?)\*', 'italic'),
            (r'`(.+?)`', 'code'),
        ]

        # 全パターンを統合して処理
        combined_pattern = r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)'
        parts = re.split(combined_pattern, text)

        for part in parts:
            if not part:
                continue

            tag = base_tag
            display_text = part

            if part.startswith("**") and part.endswith("**"):
                display_text = part[2:-2]
                tag = "bold" if not base_tag else (base_tag, "bold")
            elif part.startswith("*") and part.endswith("*") and not part.startswith("**"):
                display_text = part[1:-1]
                tag = "italic" if not base_tag else (base_tag, "italic")
            elif part.startswith("`") and part.endswith("`"):
                display_text = part[1:-1]
                tag = "code" if not base_tag else (base_tag, "code")

            if tag:
                text_widget.insert(tk.END, display_text, tag)
            else:
                text_widget.insert(tk.END, display_text)

    def _on_font_scale(self, event):
        """フォントサイズ変更"""
        if event.delta > 0:
            self.font_scale = min(FONT_SCALE_MAX, self.font_scale + FONT_SCALE_STEP)
        else:
            self.font_scale = max(FONT_SCALE_MIN, self.font_scale - FONT_SCALE_STEP)

        self.settings.set("font_scale", self.font_scale)
        self._update_font_size()
        return "break"

    def _update_font_size(self):
        """フォントサイズを適用"""
        size = self._get_font_size()
        font_family = self.i18n.get_font()

        self.summary_text.configure(font=(font_family, size))
        self.transcript_text.configure(font=(font_family, size))
        self.transcript_text.tag_configure("timestamp",
                                            font=(font_family, size, "bold"),
                                            foreground=self.COLORS["accent"])

        # マークダウンタグも更新
        self._configure_markdown_tags(self.summary_text)

        self.font_scale_label.configure(text=self.i18n.t("ui.content.font_size", scale=self.font_scale))

    def _refresh_video_list(self):
        """動画リストを更新"""
        # 既存のウィジェットを削除
        for widget in self.video_list_frame.winfo_children():
            widget.destroy()

        # 動画数バッジを更新
        if hasattr(self, 'video_count_label'):
            count = len(self.video_store.videos)
            self.video_count_label.configure(text=self.i18n.t("ui.sidebar.video_count", count=count))

        # 動画リストを表示
        for video in self.video_store.videos:
            self._create_video_item(video)

    def _create_video_item(self, video: Video):
        """動画リストアイテムを作成 - Refined Editorial Style"""
        font_family = self.i18n.get_font()
        is_selected = video.id == self.current_video_id
        bg_color = self.COLORS["selected"] if is_selected else self.COLORS["surface"]

        # 外枠 - 選択時は左ボーダーにアクセントカラー
        outer_frame = tk.Frame(self.video_list_frame, bg=self.COLORS["surface"])
        outer_frame.pack(fill=tk.X, padx=6, pady=3)

        # 左アクセントバー（選択インジケーター）
        accent_indicator = tk.Frame(outer_frame,
                                     bg=self.COLORS["accent"] if is_selected else self.COLORS["surface"],
                                     width=4)
        accent_indicator.pack(side=tk.LEFT, fill=tk.Y)

        item_frame = tk.Frame(outer_frame, bg=bg_color, cursor="hand2")
        item_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 削除ボタン（先にpackしてスペースを確保）
        delete_btn = tk.Button(item_frame, text="×",
                                font=(font_family, 11),
                                bg=bg_color, fg=self.COLORS["text_muted"],
                                relief=tk.FLAT, cursor="hand2",
                                activebackground=bg_color,
                                activeforeground=self.COLORS["error"],
                                command=lambda v=video: self._delete_video(v))
        delete_btn.pack(side=tk.RIGHT, padx=(0, 6), pady=8)

        # サムネイルコンテナ - より大きく
        thumb_container = tk.Frame(item_frame, bg=bg_color)
        thumb_container.pack(side=tk.LEFT, padx=10, pady=10)

        thumb_label = tk.Label(thumb_container, bg=self.COLORS["border"])
        thumb_label.pack()
        self._load_thumbnail(video.id, video.thumbnail, thumb_label)

        # 情報エリア
        info_frame = tk.Frame(item_frame, bg=bg_color)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10, padx=(0, 4))

        # タイトル（省略）
        title = video.title[:26] + "..." if len(video.title) > 26 else video.title
        title_label = tk.Label(info_frame, text=title,
                                font=(font_family, 10),
                                bg=bg_color, fg=self.COLORS["text"],
                                anchor=tk.W, wraplength=130, justify=tk.LEFT)
        title_label.pack(fill=tk.X, anchor=tk.W)

        # 要約済みマーク - より洗練されたバッジスタイル
        if self.summary_store.get(video.id):
            status_frame = tk.Frame(info_frame, bg=bg_color)
            status_frame.pack(fill=tk.X, pady=(6, 0))

            badge = tk.Label(status_frame, text=f"✓ {self.i18n.t('ui.summary_panel.summarized')}",
                              fg=self.COLORS["success"],
                              bg=self.COLORS["success_light"],
                              font=(self.i18n.get_font(), 8, "bold"),
                              padx=6, pady=1)
            badge.pack(side=tk.LEFT)

        # ホバー効果 - 左アクセントバーを含む
        def on_enter(e):
            if not is_selected:
                accent_indicator.configure(bg=self.COLORS["accent"])
                item_frame.configure(bg=self.COLORS["hover"])
                for widget in [info_frame, title_label, thumb_container, delete_btn]:
                    widget.configure(bg=self.COLORS["hover"])
                if self.summary_store.get(video.id):
                    status_frame.configure(bg=self.COLORS["hover"])

        def on_leave(e):
            if not is_selected:
                accent_indicator.configure(bg=self.COLORS["surface"])
                item_frame.configure(bg=self.COLORS["surface"])
                for widget in [info_frame, title_label, thumb_container, delete_btn]:
                    widget.configure(bg=self.COLORS["surface"])
                if self.summary_store.get(video.id):
                    status_frame.configure(bg=self.COLORS["surface"])

        # クリックイベント
        clickable_widgets = [item_frame, info_frame, title_label, thumb_label, thumb_container, accent_indicator]
        if self.summary_store.get(video.id):
            clickable_widgets.append(status_frame)

        for widget in clickable_widgets:
            widget.bind("<Button-1>", lambda e, v=video: self._select_video(v))
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def _load_thumbnail(self, video_id: str, url: str, label: tk.Label):
        """サムネイルを非同期で読み込み - より大きいサイズ"""
        def load():
            try:
                if video_id in self.thumbnail_cache:
                    img = self.thumbnail_cache[video_id]
                else:
                    response = requests.get(url, timeout=5)
                    image = Image.open(BytesIO(response.content))
                    # 16:9比率を維持しつつ大きく
                    image = image.resize(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                    img = ImageTk.PhotoImage(image)
                    self.thumbnail_cache[video_id] = img

                label.configure(image=img)
                label.image = img
            except Exception:
                pass

        threading.Thread(target=load, daemon=True).start()

    def _add_video(self):
        """動画を追加"""
        url = self.url_entry.get().strip()
        if not url or url == self.url_placeholder:
            return

        video_id = extract_video_id(url)
        if not video_id:
            messagebox.showerror(self.i18n.t("messages.error"), self.i18n.t("messages.invalid_url"))
            return

        if self.video_store.get(video_id):
            messagebox.showinfo(self.i18n.t("messages.info"), self.i18n.t("messages.already_added"))
            return

        # タイトル取得（非同期）
        def add():
            try:
                title = get_video_title(video_id)
                video = Video(
                    id=video_id,
                    url=url,
                    title=title,
                    thumbnail=get_thumbnail_url(video_id),
                )
                self.video_store.add(video)

                self.root.after(0, lambda: self._on_video_added(video))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(self.i18n.t("messages.error"), str(e)))

        self.url_entry.delete(0, tk.END)
        threading.Thread(target=add, daemon=True).start()

    def _on_video_added(self, video: Video):
        """動画追加完了"""
        self._refresh_video_list()
        self._select_video(video)

    def _delete_video(self, video: Video):
        """動画を削除"""
        title_short = video.title[:30] + "..." if len(video.title) > 30 else video.title
        confirm_msg = self.i18n.t("ui.video_item.delete_confirm", title=title_short)
        if messagebox.askyesno(self.i18n.t("messages.confirm"), confirm_msg):
            self.video_store.remove(video.id)
            self.summary_store.remove(video.id)

            if self.current_video_id == video.id:
                self.current_video_id = None
                self._clear_panels()

            self._refresh_video_list()

    def _select_video(self, video: Video):
        """動画を選択"""
        self.current_video_id = video.id
        self.video_store.move_to_top(video.id)
        self._refresh_video_list()
        self._update_panels(video)

        # 字幕がなければ取得
        if not video.transcript:
            self._fetch_transcript(video)

    def _clear_panels(self):
        """パネルをクリア"""
        self.video_title_label.configure(text="")

        self.summary_text.configure(state=tk.NORMAL)
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert("1.0", self.i18n.t("ui.content.select_video"))
        self.summary_text.configure(state=tk.DISABLED)

        self.transcript_text.configure(state=tk.NORMAL)
        self.transcript_text.delete("1.0", tk.END)
        self.transcript_text.insert("1.0", self.i18n.t("ui.content.select_video"))
        self.transcript_text.configure(state=tk.DISABLED)

    def _update_panels(self, video: Video):
        """パネルを更新"""
        self.video_title_label.configure(text=video.title)

        # 要約
        summary = self.summary_store.get(video.id)
        if summary:
            self._render_markdown(self.summary_text, summary)
        elif video.transcript:
            self.summary_text.configure(state=tk.NORMAL)
            self.summary_text.delete("1.0", tk.END)
            self.summary_text.insert("1.0", self.i18n.t("ui.summary_panel.prompt_generate"))
            self.summary_text.configure(state=tk.DISABLED)
        else:
            self.summary_text.configure(state=tk.NORMAL)
            self.summary_text.delete("1.0", tk.END)
            self.summary_text.insert("1.0", self.i18n.t("ui.transcript_panel.fetching"))
            self.summary_text.configure(state=tk.DISABLED)

        # 字幕
        self._update_transcript_display(video)

    def _update_transcript_display(self, video: Video):
        """字幕表示を更新"""
        self.transcript_text.configure(state=tk.NORMAL)
        self.transcript_text.delete("1.0", tk.END)

        if video.transcript:
            for entry in video.transcript:
                time_str = format_time(entry.start)
                # 字幕テキスト内の改行を削除して1行にする
                clean_text = entry.text.replace("\n", " ").strip()
                self.transcript_text.insert(tk.END, f"{time_str} ", "timestamp")
                self.transcript_text.insert(tk.END, f"{clean_text}\n")
        else:
            self.transcript_text.insert("1.0", self.i18n.t("ui.transcript_panel.fetching"))

        self.transcript_text.configure(state=tk.DISABLED)

    def _fetch_transcript(self, video: Video):
        """字幕を取得"""
        def fetch():
            try:
                transcript = get_transcript(video.id)
                self.video_store.set_transcript(video.id, transcript)

                self.root.after(0, lambda: self._on_transcript_fetched(video))
            except Exception as e:
                self.root.after(0, lambda: self._on_transcript_error(str(e)))

        threading.Thread(target=fetch, daemon=True).start()

    def _on_transcript_fetched(self, video: Video):
        """字幕取得完了"""
        video = self.video_store.get(video.id)
        if video and video.id == self.current_video_id:
            self._update_panels(video)

    def _on_transcript_error(self, error: str):
        """字幕取得エラー"""
        # エラーメッセージを翻訳
        if error.startswith("TRANSCRIPT_FAILED:"):
            detail = error.replace("TRANSCRIPT_FAILED:", "").strip()
            display_error = f"{self.i18n.t('messages.transcript_failed')}\n{detail}"
        else:
            display_error = error

        self.transcript_text.configure(state=tk.NORMAL)
        self.transcript_text.delete("1.0", tk.END)
        self.transcript_text.insert("1.0", display_error)
        self.transcript_text.configure(state=tk.DISABLED)

    def _generate_summary(self):
        """要約を生成"""
        if not self.current_video_id:
            messagebox.showwarning(self.i18n.t("messages.warning"), self.i18n.t("messages.select_video_first"))
            return

        video = self.video_store.get(self.current_video_id)
        if not video or not video.transcript:
            messagebox.showwarning(self.i18n.t("messages.warning"), self.i18n.t("messages.get_transcript_first"))
            return

        if not get_api_key():
            messagebox.showwarning(self.i18n.t("messages.warning"), self.i18n.t("messages.set_api_key_first"))
            return

        # 生成中表示
        self.generate_btn.configure(state=tk.DISABLED, text=f"⏳ {self.i18n.t('ui.summary_panel.generating')}",
                                     bg=self.COLORS["text_muted"])
        self.summary_text.configure(state=tk.NORMAL)
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert("1.0", self.i18n.t("ui.summary_panel.generating_summary"))
        self.summary_text.configure(state=tk.DISABLED)

        def generate():
            try:
                transcript_text = " ".join([t.text for t in video.transcript])
                prompt_template = self.i18n.t("prompts.summarize")
                summary = summarize_transcript(transcript_text, prompt_template)
                self.summary_store.set(video.id, summary)

                self.root.after(0, lambda: self._on_summary_generated(video))
            except Exception as e:
                self.root.after(0, lambda: self._on_summary_error(str(e)))

        threading.Thread(target=generate, daemon=True).start()

    def _on_summary_generated(self, video: Video):
        """要約生成完了"""
        self.generate_btn.configure(state=tk.NORMAL, text=f"✨ {self.i18n.t('ui.summary_panel.generate')}",
                                     bg=self.COLORS["accent"])
        self._update_panels(video)
        self._refresh_video_list()

    def _on_summary_error(self, error: str):
        """要約生成エラー"""
        self.generate_btn.configure(state=tk.NORMAL, text=f"✨ {self.i18n.t('ui.summary_panel.generate')}",
                                     bg=self.COLORS["accent"])

        # エラーメッセージを翻訳
        if error == "API_KEY_NOT_SET":
            display_error = self.i18n.t("messages.api_key_not_set")
        else:
            display_error = f"{self.i18n.t('messages.summary_failed')}: {error}"

        self.summary_text.configure(state=tk.NORMAL)
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert("1.0", display_error)
        self.summary_text.configure(state=tk.DISABLED)

    def _open_youtube(self):
        """YouTubeを開く"""
        if self.current_video_id:
            webbrowser.open(f"https://www.youtube.com/watch?v={self.current_video_id}")

    def _show_settings(self):
        """設定ダイアログ - Refined Editorial Style with i18n"""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.i18n.t("ui.settings_dialog.title"))
        dialog.geometry("480x400")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=self.COLORS["surface"])

        # ヘッダー - より洗練されたスタイル
        header = tk.Frame(dialog, bg=self.COLORS["primary"], height=48)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text=f"⚙ {self.i18n.t('ui.settings_dialog.title')}",
                 bg=self.COLORS["primary"], fg=self.COLORS["text_inverse"],
                 font=(self.i18n.get_font(), 13, "bold")).pack(side=tk.LEFT, padx=20, pady=10)

        # コンテンツ
        content = tk.Frame(dialog, bg=self.COLORS["surface"])
        content.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        # 言語選択
        tk.Label(content, text=self.i18n.t("ui.settings_dialog.language"),
                 bg=self.COLORS["surface"],
                 fg=self.COLORS["text"],
                 font=(self.i18n.get_font(), 11, "bold")).pack(anchor=tk.W)

        lang_container = tk.Frame(content, bg=self.COLORS["border"])
        lang_container.pack(fill=tk.X, pady=(10, 16))

        lang_inner = tk.Frame(lang_container, bg=self.COLORS["surface_alt"])
        lang_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # 言語オプションを構築
        lang_options = []
        lang_codes = []
        for code, info in self.i18n.SUPPORTED_LANGUAGES.items():
            lang_options.append(info["native_name"])
            lang_codes.append(code)

        current_lang = self.i18n.current_language
        current_idx = lang_codes.index(current_lang) if current_lang in lang_codes else 0

        lang_var = tk.StringVar(value=lang_options[current_idx])
        lang_menu = tk.OptionMenu(lang_inner, lang_var, *lang_options)
        lang_menu.configure(font=(self.i18n.get_font(), 11),
                           bg=self.COLORS["surface_alt"],
                           fg=self.COLORS["text"],
                           relief=tk.FLAT,
                           highlightthickness=0,
                           activebackground=self.COLORS["accent"],
                           activeforeground=self.COLORS["text_inverse"])
        lang_menu["menu"].configure(font=(self.i18n.get_font(), 10),
                                    bg=self.COLORS["surface_alt"],
                                    fg=self.COLORS["text"])
        lang_menu.pack(fill=tk.X, padx=10, pady=8)

        # APIキー入力
        tk.Label(content, text=self.i18n.t("ui.settings_dialog.api_key_label"),
                 bg=self.COLORS["surface"],
                 fg=self.COLORS["text"],
                 font=(self.i18n.get_font(), 11, "bold")).pack(anchor=tk.W)

        # 入力フィールドコンテナ - フォーカス時にハイライト
        entry_container = tk.Frame(content, bg=self.COLORS["border"])
        entry_container.pack(fill=tk.X, pady=(10, 0))

        entry_inner = tk.Frame(entry_container, bg=self.COLORS["surface_alt"])
        entry_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        api_entry = tk.Entry(entry_inner, font=(self.i18n.get_font(), 11),
                              relief=tk.FLAT, bg=self.COLORS["surface_alt"],
                              fg=self.COLORS["text"], show="•",
                              insertbackground=self.COLORS["accent"])
        api_entry.pack(fill=tk.X, padx=14, pady=12)
        api_entry.insert(0, get_api_key() or "")

        def on_entry_focus_in(e):
            entry_container.configure(bg=self.COLORS["accent"])

        def on_entry_focus_out(e):
            entry_container.configure(bg=self.COLORS["border"])

        api_entry.bind("<FocusIn>", on_entry_focus_in)
        api_entry.bind("<FocusOut>", on_entry_focus_out)

        # リンク
        link = tk.Label(content, text=f"→ {self.i18n.t('ui.settings_dialog.api_key_link')}",
                        fg=self.COLORS["accent"], bg=self.COLORS["surface"],
                        cursor="hand2", font=(self.i18n.get_font(), 10))
        link.pack(anchor=tk.W, pady=(10, 0))
        link.bind("<Button-1>", lambda e: webbrowser.open("https://aistudio.google.com/app/apikey"))

        # ホバー効果
        def on_link_enter(e):
            link.configure(fg=self.COLORS["accent_hover"])

        def on_link_leave(e):
            link.configure(fg=self.COLORS["accent"])

        link.bind("<Enter>", on_link_enter)
        link.bind("<Leave>", on_link_leave)

        # ボタン
        btn_frame = tk.Frame(dialog, bg=self.COLORS["surface"])
        btn_frame.pack(pady=(0, 20))

        def save():
            # APIキーを保存
            api_key = api_entry.get().strip()
            current_api_key = get_api_key() or ""
            api_changed = api_key != current_api_key
            if api_changed:
                set_api_key(api_key)
                self.settings.set("api_key", api_key)

            # 言語を取得
            selected_lang_name = lang_var.get()
            selected_lang_code = lang_codes[lang_options.index(selected_lang_name)]
            language_changed = selected_lang_code != self.i18n.current_language

            # 言語を保存（変更があれば）
            if language_changed:
                self.settings.set("language", selected_lang_code)

            # ダイアログを閉じる
            dialog.destroy()

            # 言語変更を適用
            if language_changed:
                self.i18n.current_language = selected_lang_code
                self._on_language_changed()

        cancel_btn = tk.Button(btn_frame, text=self.i18n.t("ui.settings_dialog.cancel"),
                                font=(self.i18n.get_font(), 10),
                                bg=self.COLORS["surface_alt"],
                                fg=self.COLORS["text"],
                                relief=tk.FLAT,
                                padx=20, pady=8,
                                cursor="hand2",
                                command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=8)

        save_btn = tk.Button(btn_frame, text=self.i18n.t("ui.settings_dialog.save_and_close"),
                              font=(self.i18n.get_font(), 10, "bold"),
                              bg=self.COLORS["accent"],
                              fg=self.COLORS["text_inverse"],
                              relief=tk.FLAT,
                              padx=28, pady=8,
                              cursor="hand2",
                              activebackground=self.COLORS["accent_hover"],
                              activeforeground=self.COLORS["text_inverse"],
                              command=save)
        save_btn.pack(side=tk.LEFT, padx=8)

        # ホバー効果
        def on_save_enter(e):
            save_btn.configure(bg=self.COLORS["accent_hover"])

        def on_save_leave(e):
            save_btn.configure(bg=self.COLORS["accent"])

        def on_cancel_enter(e):
            cancel_btn.configure(bg=self.COLORS["border"])

        def on_cancel_leave(e):
            cancel_btn.configure(bg=self.COLORS["surface_alt"])

        save_btn.bind("<Enter>", on_save_enter)
        save_btn.bind("<Leave>", on_save_leave)
        cancel_btn.bind("<Enter>", on_cancel_enter)
        cancel_btn.bind("<Leave>", on_cancel_leave)

    def _on_language_changed(self):
        """言語変更時にUI全体を更新"""
        font_family = self.i18n.get_font()

        # ウィンドウタイトル
        self.root.title(self.i18n.t("ui.app_title"))

        # ヘッダー
        self.settings_btn.configure(
            text=f"⚙ {self.i18n.t('ui.header.settings')}",
            font=(font_family, 10)
        )

        # サイドバー
        self.video_list_label.configure(
            text=self.i18n.t("ui.sidebar.video_list"),
            font=(font_family, 14, "bold")
        )
        video_count = len(self.video_store.videos)
        self.video_count_label.configure(
            text=self.i18n.t("ui.sidebar.video_count", count=video_count),
            font=(font_family, 9, "bold")
        )

        # URL入力
        self.url_placeholder = self.i18n.t("ui.sidebar.url_placeholder")
        self.url_entry.configure(font=(font_family, 10))
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, self.url_placeholder)
        self.url_entry.configure(fg=self.COLORS["text_muted"])

        # パネルタイトル
        self.summary_title_label.configure(
            text=self.i18n.t("ui.summary_panel.title"),
            font=(font_family, 13, "bold")
        )
        self.transcript_title_label.configure(
            text=self.i18n.t("ui.transcript_panel.title"),
            font=(font_family, 13, "bold")
        )

        # 生成ボタン
        self.generate_btn.configure(
            text=f"✨ {self.i18n.t('ui.summary_panel.generate')}",
            font=(font_family, 10, "bold")
        )

        # YouTubeリンク
        self.youtube_link.configure(
            text=f"▶ {self.i18n.t('ui.content.watch_on_youtube')}",
            font=(font_family, 10)
        )

        # フォントサイズ表示
        self.font_scale_label.configure(
            text=self.i18n.t("ui.content.font_size", scale=self.font_scale),
            font=(font_family, 9)
        )

        # テキストエリアのフォント更新
        size = self._get_font_size()
        self.summary_text.configure(font=(font_family, size))
        self.transcript_text.configure(font=(font_family, size))
        self.transcript_text.tag_configure("timestamp",
                                            font=(font_family, size, "bold"),
                                            foreground=self.COLORS["accent"])

        # マークダウンタグを再設定
        self._configure_markdown_tags(self.summary_text)

        # 動画リストを再描画（フォント更新含む）
        self._refresh_video_list()

        # パネルコンテンツを更新
        if self.current_video_id:
            video = self.video_store.get(self.current_video_id)
            if video:
                self._update_panels(video)
        else:
            self._clear_panels()

        # UIの強制更新
        self.root.update_idletasks()

    def _on_close(self):
        """アプリ終了"""
        self.root.destroy()


def main():
    root = tk.Tk()
    app = YTSummarizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
