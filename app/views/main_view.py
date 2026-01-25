"""メインビュー"""
import flet as ft
from pathlib import Path
from app.models.video import Video, VideoStore
from app.services.youtube import extract_video_id, get_thumbnail_url, get_embed_url, format_time
from app.services.transcript import get_transcript
from app.services.gemini import summarize_transcript, set_api_key, get_api_key


class MainView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "YT Summarizer"
        self.page.window.width = 1200
        self.page.window.height = 800
        self.page.padding = 0

        # データストア
        data_path = Path(__file__).parent.parent.parent / "data" / "videos.json"
        self.store = VideoStore(data_path)
        self.current_video_id: str | None = None

        # UI要素
        self.url_input = ft.TextField(
            hint_text="YouTube URL を入力...",
            expand=True,
            on_submit=self.add_video,
        )
        self.video_list = ft.ListView(expand=True, spacing=5, padding=10)
        self.webview = ft.WebView(
            expand=True,
            url="about:blank",
        )
        self.summary_text = ft.Text("動画を選択してください", selectable=True)
        self.transcript_list = ft.ListView(expand=True, spacing=2, padding=10)
        self.tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="要約", content=self._build_summary_tab()),
                ft.Tab(text="字幕", content=self._build_transcript_tab()),
            ],
            expand=True,
        )

        self._build_ui()
        self._refresh_video_list()

    def _build_ui(self):
        """UIを構築"""
        # サイドバー
        sidebar = ft.Container(
            width=280,
            bgcolor=ft.Colors.GREY_100,
            content=ft.Column([
                # URL入力
                ft.Container(
                    padding=10,
                    content=ft.Row([
                        self.url_input,
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            tooltip="追加",
                            on_click=self.add_video,
                        ),
                    ]),
                ),
                ft.Divider(height=1),
                # 動画リスト
                ft.Container(
                    expand=True,
                    content=self.video_list,
                ),
            ]),
        )

        # メインエリア
        main_area = ft.Column([
            # 動画プレイヤー
            ft.Container(
                height=400,
                bgcolor=ft.Colors.BLACK,
                content=self.webview,
            ),
            # タブ（要約・字幕）
            ft.Container(
                expand=True,
                content=self.tabs,
            ),
        ], expand=True)

        # ヘッダー
        header = ft.Container(
            height=50,
            bgcolor=ft.Colors.BLUE_700,
            padding=ft.padding.symmetric(horizontal=15),
            content=ft.Row([
                ft.Text("YT Summarizer", size=20, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    icon_color=ft.Colors.WHITE,
                    tooltip="設定",
                    on_click=self.show_settings,
                ),
            ]),
        )

        # レイアウト
        self.page.add(
            ft.Column([
                header,
                ft.Row([
                    sidebar,
                    ft.VerticalDivider(width=1),
                    ft.Container(content=main_area, expand=True, padding=10),
                ], expand=True),
            ], expand=True, spacing=0)
        )

    def _build_summary_tab(self) -> ft.Container:
        """要約タブを構築"""
        return ft.Container(
            padding=15,
            content=ft.Column([
                ft.Row([
                    ft.Text("要約", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "要約を生成",
                        icon=ft.Icons.AUTO_AWESOME,
                        on_click=self.generate_summary,
                    ),
                ]),
                ft.Divider(),
                ft.Container(
                    expand=True,
                    content=ft.Column([self.summary_text], scroll=ft.ScrollMode.AUTO),
                ),
            ]),
        )

    def _build_transcript_tab(self) -> ft.Container:
        """字幕タブを構築"""
        return ft.Container(
            padding=15,
            content=ft.Column([
                ft.Row([
                    ft.Text("字幕", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "字幕を取得",
                        icon=ft.Icons.SUBTITLES,
                        on_click=self.fetch_transcript,
                    ),
                ]),
                ft.Divider(),
                self.transcript_list,
            ]),
        )

    def _refresh_video_list(self):
        """動画リストを更新"""
        self.video_list.controls.clear()
        for video in self.store.videos:
            self.video_list.controls.append(self._create_video_item(video))
        self.page.update()

    def _create_video_item(self, video: Video) -> ft.Container:
        """動画リストアイテムを作成"""
        is_selected = video.id == self.current_video_id
        return ft.Container(
            bgcolor=ft.Colors.BLUE_50 if is_selected else None,
            border_radius=5,
            padding=5,
            on_click=lambda e, v=video: self.select_video(v),
            content=ft.Row([
                ft.Image(src=video.thumbnail, width=100, height=56, fit=ft.ImageFit.COVER, border_radius=3),
                ft.Column([
                    ft.Text(video.title, size=12, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(video.id, size=10, color=ft.Colors.GREY_600),
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=12, color=ft.Colors.GREEN) if video.summary else ft.Container(),
                    ], spacing=5),
                ], expand=True, spacing=2),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_size=18,
                    tooltip="削除",
                    on_click=lambda e, v=video: self.remove_video(v),
                ),
            ]),
        )

    def add_video(self, e):
        """動画を追加"""
        url = self.url_input.value.strip()
        if not url:
            return

        video_id = extract_video_id(url)
        if not video_id:
            self.show_snackbar("有効なYouTube URLを入力してください", error=True)
            return

        if self.store.get(video_id):
            self.show_snackbar("この動画は既に追加されています", error=True)
            return

        video = Video(
            id=video_id,
            url=url,
            title=f"動画 {video_id}",
            thumbnail=get_thumbnail_url(video_id),
        )
        self.store.add(video)
        self.url_input.value = ""
        self._refresh_video_list()
        self.select_video(video)
        self.show_snackbar("動画を追加しました")

    def remove_video(self, video: Video):
        """動画を削除"""
        self.store.remove(video.id)
        if self.current_video_id == video.id:
            self.current_video_id = None
            self.webview.url = "about:blank"
        self._refresh_video_list()
        self.show_snackbar("動画を削除しました")

    def select_video(self, video: Video):
        """動画を選択"""
        self.current_video_id = video.id
        self.webview.url = get_embed_url(video.id)
        self._refresh_video_list()
        self._update_summary_display(video)
        self._update_transcript_display(video)

    def fetch_transcript(self, e):
        """字幕を取得"""
        if not self.current_video_id:
            self.show_snackbar("動画を選択してください", error=True)
            return

        video = self.store.get(self.current_video_id)
        if not video:
            return

        self.show_snackbar("字幕を取得中...")
        self.page.update()

        try:
            transcript = get_transcript(video.id)
            self.store.update(video.id, transcript=transcript)
            video = self.store.get(video.id)
            self._update_transcript_display(video)
            self.show_snackbar("字幕を取得しました")
        except Exception as ex:
            self.show_snackbar(f"エラー: {ex}", error=True)

    def generate_summary(self, e):
        """要約を生成"""
        if not self.current_video_id:
            self.show_snackbar("動画を選択してください", error=True)
            return

        video = self.store.get(self.current_video_id)
        if not video:
            return

        if not video.transcript:
            self.show_snackbar("先に字幕を取得してください", error=True)
            return

        if not get_api_key():
            self.show_snackbar("設定からAPIキーを入力してください", error=True)
            return

        self.show_snackbar("要約を生成中...")
        self.summary_text.value = "生成中..."
        self.page.update()

        try:
            transcript_text = " ".join([t.text for t in video.transcript])
            summary = summarize_transcript(transcript_text)
            self.store.update(video.id, summary=summary)
            video = self.store.get(video.id)
            self._update_summary_display(video)
            self._refresh_video_list()
            self.show_snackbar("要約を生成しました")
        except Exception as ex:
            self.show_snackbar(f"エラー: {ex}", error=True)
            self.summary_text.value = f"エラー: {ex}"
            self.page.update()

    def _update_summary_display(self, video: Video | None):
        """要約表示を更新"""
        if video and video.summary:
            self.summary_text.value = video.summary
        elif video and not video.transcript:
            self.summary_text.value = "「字幕」タブで字幕を取得してから要約を生成してください"
        elif video:
            self.summary_text.value = "「要約を生成」ボタンを押してください"
        else:
            self.summary_text.value = "動画を選択してください"
        self.page.update()

    def _update_transcript_display(self, video: Video | None):
        """字幕表示を更新"""
        self.transcript_list.controls.clear()
        if video and video.transcript:
            for entry in video.transcript:
                self.transcript_list.controls.append(
                    ft.Container(
                        padding=5,
                        content=ft.Row([
                            ft.Text(format_time(entry.start), size=11, color=ft.Colors.GREY_600, width=50),
                            ft.Text(entry.text, size=12, expand=True),
                        ]),
                    )
                )
        else:
            self.transcript_list.controls.append(
                ft.Text("「字幕を取得」ボタンを押してください", color=ft.Colors.GREY_600)
            )
        self.page.update()

    def show_settings(self, e):
        """設定ダイアログを表示"""
        api_key_field = ft.TextField(
            label="Gemini API キー",
            value=get_api_key() or "",
            password=True,
            can_reveal_password=True,
        )

        def save_settings(e):
            set_api_key(api_key_field.value)
            dlg.open = False
            self.show_snackbar("設定を保存しました")
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("設定"),
            content=ft.Column([
                api_key_field,
                ft.Text(
                    "Google AI Studio でAPIキーを取得: https://aistudio.google.com/app/apikey",
                    size=11,
                    color=ft.Colors.GREY_600,
                ),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(dlg, "open", False) or self.page.update()),
                ft.ElevatedButton("保存", on_click=save_settings),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def show_snackbar(self, message: str, error: bool = False):
        """スナックバーを表示"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
