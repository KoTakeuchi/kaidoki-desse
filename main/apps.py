# 実行ディレクトリ: I:\school\kaidoki-desse\main\apps.py
from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    def ready(self):
        import main.signals  # ✅ signalsを読み込む
