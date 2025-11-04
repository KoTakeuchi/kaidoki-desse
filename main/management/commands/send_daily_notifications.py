# main/management/commands/send_daily_notifications.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from main.utils.mailer import process_daily_notifications


class Command(BaseCommand):
    """
    ✅ 1日1回の通知メール送信バッチ
    実行例: python manage.py send_daily_notifications
    """

    help = "全ユーザーに対して在庫・買い時通知メールを送信します。"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("📧 通知メール送信バッチを開始します..."))
        start_time = timezone.localtime()

        try:
            process_daily_notifications()
            self.stdout.write(self.style.SUCCESS("✅ 全ユーザーへの通知メール送信が完了しました。"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ エラーが発生しました: {e}"))

        end_time = timezone.localtime()
        duration = (end_time - start_time).total_seconds()
        self.stdout.write(self.style.HTTP_INFO(f"🕒 実行時間: {duration:.2f} 秒"))
