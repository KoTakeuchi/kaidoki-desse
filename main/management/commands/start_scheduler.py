# 実行ディレクトリ: I:\school\kaidoki-desse\main\management\commands\start_scheduler.py
from django.core.management.base import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler  # ✅ 本番用スケジューラ
from django.core.management import call_command
from django.utils import timezone


class Command(BaseCommand):
    """
    ✅ APScheduler による本番スケジューラ
    毎朝9時に send_daily_notifications を実行
    """

    help = "本番スケジューラ：毎朝9時に通知メール送信処理を実行します。"

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone="Asia/Tokyo")

        def job():
            self.stdout.write(self.style.HTTP_INFO(
                f"[{timezone.localtime()}] 🕒 通知メールバッチ開始"))
            call_command("send_daily_notifications")
            self.stdout.write(self.style.SUCCESS(
                f"[{timezone.localtime()}] ✅ 通知メールバッチ完了"))

        # === 毎朝9時に実行 ===
        scheduler.add_job(job, "cron", hour=9, minute=0)
        self.stdout.write(self.style.NOTICE("⏰ スケジューラ起動中...（毎朝9時に実行）"))

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write(self.style.WARNING("🛑 スケジューラを停止しました。"))
