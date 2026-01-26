"""YT Summarizer - YouTube動画要約アプリ"""
import flet as ft
import webbrowser
from pathlib import Path
from app.models.video import Video, VideoStore
from app.services.youtube import extract_video_id, get_thumbnail_url, get_video_title, format_time
from app.services.transcript import get_transcript
from app.services.gemini import summarize_transcript, set_api_key, get_api_key


class YTSummarizer:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "YT Summarizer"
        self.page.window.width = 1300
        self.page.window.height = 750
        self.page.padding = 0

        # データストア
        data_path = Path(__file__).parent / "data" / "videos.json"
        self.store = VideoStore(data_path)
        self.current_video_id: str | None = None

        # UI要素
        self.url_input = ft.TextField(
            hint_text="YouTube URL を入力...",
            expand=True,
            on_submit=self.add_video,
            border_radius=8,
        )
        self.video_list = ft.ListView(expand=True, spacing=2, padding=10)

        # 中央・右パネル共通ヘッダー
        self.video_title = ft.Text("", size=16, weight=ft.FontWeight.BOLD, max_lines=2, expand=True)
        self.video_link = ft.TextButton("YouTubeで見る", icon=ft.Icons.OPEN_IN_NEW, on_click=self.open_video, visible=False)

        # 字幕パネル
        self.transcript_list = ft.ListView(expand=True, spacing=1, padding=5)

        # 要約パネル
        self.summary_text = ft.Text("", selectable=True, size=14)

        self._build_ui()
        self._refresh_video_list()

    def _build_ui(self):
        """UIを構築"""
        # ヘッダー
        header = ft.Container(
            height=55,
            bgcolor=ft.Colors.BLUE_700,
            padding=ft.padding.symmetric(horizontal=20),
            content=ft.Row([
                ft.Icon(ft.Icons.SUMMARIZE, color=ft.Colors.WHITE, size=28),
                ft.Text("YT Summarizer", size=22, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    icon_color=ft.Colors.WHITE,
                    tooltip="APIキー設定",
                    on_click=self.show_settings,
                ),
            ]),
        )

        # 左カラム：動画リスト
        left_column = ft.Container(
            width=280,
            bgcolor=ft.Colors.GREY_100,
            content=ft.Column([
                ft.Container(
                    padding=12,
                    content=ft.Row([
                        self.url_input,
                        ft.IconButton(
                            icon=ft.Icons.ADD_CIRCLE,
                            icon_color=ft.Colors.BLUE_600,
                            tooltip="追加",
                            on_click=self.add_video,
                        ),
                    ]),
                ),
                ft.Divider(height=1),
                ft.Container(expand=True, content=self.video_list),
            ]),
        )

        # 中央カラム：字幕
        center_column = ft.Container(
            expand=True,
            padding=15,
            content=ft.Column([
                ft.Row([
                    ft.Text("字幕", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "取得",
                        icon=ft.Icons.DOWNLOAD,
                        on_click=self.fetch_transcript,
                    ),
                ]),
                ft.Divider(),
                ft.Container(expand=True, content=self.transcript_list),
            ]),
        )

        # 右カラム：要約
        right_column = ft.Container(
            expand=True,
            padding=15,
            content=ft.Column([
                ft.Row([
                    ft.Text("要約", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "生成",
                        icon=ft.Icons.AUTO_AWESOME,
                        bgcolor=ft.Colors.BLUE_600,
                        color=ft.Colors.WHITE,
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

        # タイトルバー（中央・右の上部に配置）
        title_bar = ft.Container(
            padding=ft.padding.only(left=15, right=15, top=10, bottom=5),
            content=ft.Row([
                self.video_title,
                self.video_link,
            ]),
        )

        # 中央＋右エリア
        main_area = ft.Column([
            title_bar,
            ft.Divider(height=1),
            ft.Row([
                center_column,
                ft.VerticalDivider(width=1),
                right_column,
            ], expand=True),
        ], expand=True)

        # レイアウト
        self.page.add(
            ft.Column([
                header,
                ft.Row([
                    left_column,
                    ft.VerticalDivider(width=1),
                    ft.Container(content=main_area, expand=True),
                ], expand=True),
            ], expand=True, spacing=0)
        )

    def _refresh_video_list(self):
        """動画リストを更新"""
        self.video_list.controls.clear()
        for video in self.store.videos:
            self.video_list.controls.append(self._create_video_item(video))
        self.page.update()

    def _create_video_item(self, video: Video) -> ft.Container:
        """動画リストアイテム"""
        is_selected = video.id == self.current_video_id

        # タイトルを短縮（25文字以上は省略）
        title = video.title
        if len(title) > 25:
            title = title[:25] + "..."

        return ft.Container(
            bgcolor=ft.Colors.BLUE_100 if is_selected else ft.Colors.WHITE,
            border_radius=8,
            padding=10,
            margin=ft.margin.symmetric(horizontal=5),
            on_click=lambda e, v=video: self.select_video(v),
            content=ft.Row([
                ft.Column([
                    ft.Text(title, size=12, weight=ft.FontWeight.W_500, max_lines=1),
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color=ft.Colors.GREEN) if video.summary else ft.Container(),
                    ], spacing=5),
                ], expand=True, spacing=3),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_size=18,
                    icon_color=ft.Colors.GREY_500,
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

        self.show_snackbar("動画情報を取得中...")
        self.page.update()

        # タイトルを取得
        title = get_video_title(video_id)

        video = Video(
            id=video_id,
            url=url,
            title=title,
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
            self._clear_panels()
        self._refresh_video_list()
        self.show_snackbar("削除しました")

    def select_video(self, video: Video):
        """動画を選択"""
        self.current_video_id = video.id
        self._refresh_video_list()
        self._update_panels(video)

    def _clear_panels(self):
        """パネルをクリア"""
        self.video_title.value = ""
        self.video_link.visible = False
        self.summary_text.value = "動画を選択してください"
        self.transcript_list.controls.clear()
        self.transcript_list.controls.append(
            ft.Text("動画を選択してください", color=ft.Colors.GREY_500)
        )
        self.page.update()

    def _update_panels(self, video: Video):
        """パネルを更新"""
        # タイトル
        self.video_title.value = video.title
        self.video_link.visible = True

        # 要約
        if video.summary:
            self.summary_text.value = video.summary
        elif video.transcript:
            self.summary_text.value = "「生成」ボタンを押して要約を作成してください"
        else:
            self.summary_text.value = "字幕を取得してから要約を生成してください"

        # 字幕
        self._update_transcript_display(video)
        self.page.update()

    def _update_transcript_display(self, video: Video):
        """字幕表示を更新"""
        self.transcript_list.controls.clear()
        if video.transcript:
            for entry in video.transcript:
                self.transcript_list.controls.append(
                    ft.Container(
                        padding=8,
                        border_radius=5,
                        bgcolor=ft.Colors.GREY_50,
                        margin=ft.margin.only(bottom=3),
                        content=ft.Row([
                            ft.Text(
                                format_time(entry.start),
                                size=11,
                                color=ft.Colors.BLUE_600,
                                width=45,
                            ),
                            ft.Text(entry.text, size=12, expand=True),
                        ]),
                    )
                )
        else:
            self.transcript_list.controls.append(
                ft.Text("「取得」ボタンを押して字幕を取得してください", color=ft.Colors.GREY_500)
            )

    def open_video(self, e):
        """ブラウザで動画を開く"""
        if self.current_video_id:
            webbrowser.open(f"https://www.youtube.com/watch?v={self.current_video_id}")

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
            self._update_panels(video)
            self.show_snackbar(f"字幕を取得しました（{len(transcript)}件）")
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
            self._update_panels(video)
            self._refresh_video_list()
            self.show_snackbar("要約を生成しました")
        except Exception as ex:
            self.show_snackbar(f"エラー: {ex}", error=True)
            self.summary_text.value = f"エラー: {ex}"
            self.page.update()

    def show_settings(self, e):
        """設定ダイアログ"""
        api_key_field = ft.TextField(
            label="Gemini API キー",
            value=get_api_key() or "",
            password=True,
            can_reveal_password=True,
            width=400,
        )

        def save(e):
            set_api_key(api_key_field.value)
            dlg.open = False
            self.show_snackbar("APIキーを保存しました")
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("設定"),
            content=ft.Column([
                api_key_field,
                ft.TextButton(
                    "Google AI StudioでAPIキーを取得",
                    icon=ft.Icons.OPEN_IN_NEW,
                    on_click=lambda e: webbrowser.open("https://aistudio.google.com/app/apikey"),
                ),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(dlg, "open", False) or self.page.update()),
                ft.ElevatedButton("保存", on_click=save),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def show_snackbar(self, message: str, error: bool = False):
        """スナックバー表示"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_600 if error else ft.Colors.GREEN_600,
        )
        self.page.snack_bar.open = True
        self.page.update()


def main(page: ft.Page):
    YTSummarizer(page)


if __name__ == "__main__":
    ft.app(target=main)
