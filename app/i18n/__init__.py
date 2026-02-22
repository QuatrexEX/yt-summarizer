"""多言語対応（i18n）モジュール"""
from pathlib import Path
import json
from typing import Optional, Callable


class I18nManager:
    """多言語対応マネージャー"""

    # サポートする言語とフォント設定
    SUPPORTED_LANGUAGES = {
        "ja": {"name": "日本語", "native_name": "日本語", "font": "Meiryo UI"},
        "en": {"name": "English", "native_name": "English", "font": "Segoe UI"},
        "ko": {"name": "Korean", "native_name": "한국어", "font": "Malgun Gothic"},
        "zh-CN": {"name": "Chinese (Simplified)", "native_name": "简体中文", "font": "Microsoft YaHei"},
        "es": {"name": "Spanish", "native_name": "Español", "font": "Segoe UI"},
        "pt": {"name": "Portuguese", "native_name": "Português", "font": "Segoe UI"},
    }

    def __init__(self, locales_dir: Path, default_language: str = "ja"):
        """
        初期化

        Args:
            locales_dir: 翻訳ファイルのディレクトリパス
            default_language: デフォルト言語コード
        """
        self.locales_dir = locales_dir
        self.default_language = default_language
        self.current_language = default_language
        self._translations: dict[str, dict] = {}
        self._observers: list[Callable] = []
        self._load_translations()

    def _load_translations(self) -> None:
        """全言語の翻訳をロード"""
        for lang in self.SUPPORTED_LANGUAGES:
            file_path = self.locales_dir / f"{lang}.json"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self._translations[lang] = json.load(f)
                except Exception as e:
                    print(f"[WARN] Failed to load translation '{lang}': {e}")

    def set_language(self, language: str) -> bool:
        """
        言語を変更

        Args:
            language: 言語コード

        Returns:
            変更成功時True
        """
        if language in self._translations:
            self.current_language = language
            self._notify_observers()
            return True
        return False

    def get(self, key: str, **kwargs) -> str:
        """
        翻訳文字列を取得（ドット記法対応）

        Args:
            key: 翻訳キー（例: "ui.header.settings"）
            **kwargs: プレースホルダー置換用の引数

        Returns:
            翻訳された文字列
        """
        keys = key.split(".")
        value = self._translations.get(self.current_language, {})

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    # フォールバック: デフォルト言語を試す
                    value = self._get_fallback(key)
                    break
            else:
                value = None
                break

        if value is None:
            return key

        # プレースホルダー置換
        if isinstance(value, str) and kwargs:
            for k, v in kwargs.items():
                value = value.replace(f"{{{k}}}", str(v))

        return value if isinstance(value, str) else key

    def _get_fallback(self, key: str) -> Optional[str]:
        """デフォルト言語からフォールバック値を取得"""
        keys = key.split(".")
        value = self._translations.get(self.default_language, {})

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return None
            else:
                return None

        return value if isinstance(value, str) else None

    def t(self, key: str, **kwargs) -> str:
        """get()のエイリアス"""
        return self.get(key, **kwargs)

    def get_font(self) -> str:
        """現在の言語に適したフォントを取得"""
        return self.SUPPORTED_LANGUAGES.get(
            self.current_language, {}
        ).get("font", "Segoe UI")

    def get_current_language_name(self) -> str:
        """現在の言語のネイティブ名を取得"""
        return self.SUPPORTED_LANGUAGES.get(
            self.current_language, {}
        ).get("native_name", self.current_language)

    def add_observer(self, callback: Callable) -> None:
        """言語変更時のコールバックを登録"""
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable) -> None:
        """コールバックを削除"""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self) -> None:
        """全オブザーバーに通知"""
        for callback in self._observers:
            try:
                callback()
            except Exception as e:
                print(f"[WARN] i18n observer callback failed: {e}")

    def get_supported_languages(self) -> list[tuple[str, str]]:
        """
        サポートする言語リストを取得

        Returns:
            [(言語コード, ネイティブ名), ...]のリスト
        """
        return [
            (code, info["native_name"])
            for code, info in self.SUPPORTED_LANGUAGES.items()
            if code in self._translations
        ]

    def get_all_languages(self) -> list[tuple[str, str]]:
        """
        全てのサポート言語リストを取得（翻訳ファイルの有無に関わらず）

        Returns:
            [(言語コード, ネイティブ名), ...]のリスト
        """
        return [
            (code, info["native_name"])
            for code, info in self.SUPPORTED_LANGUAGES.items()
        ]
