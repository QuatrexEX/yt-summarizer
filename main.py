"""YT Summarizer - YouTube動画要約アプリ"""
import flet as ft
from app.views.main_view import MainView


def main(page: ft.Page):
    MainView(page)


if __name__ == "__main__":
    ft.app(target=main)
