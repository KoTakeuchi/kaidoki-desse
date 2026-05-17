# main/management/commands/send_daily_notifications.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import UserNotificationSetting
from main.utils.mailer import process_daily_notifications


class Command(BaseCommand):
    """
    1日1回の通知メール送信バッチ
    cronで毎時実行し、ユーザーごとの設定時刻と一致した場合のみ送信
    実行例: python manage.py send_daily_notifications
    """
    help = "全ユーザーに対して在庫・買い時通知メールを送信します。"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='時刻判定をスキップして強制送信（テスト用）',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("📧 通知メール送信バッチを開始します..."))
        start_time = timezone.localtime()
        now = start_time

        force = options.get('force', False)

        try:
            if force:
                # ✅ --force オプション時は全ユーザーに即送信
                self.stdout.write(self.style.WARNING("⚠️ 強制送信モード（時刻判定スキップ）"))
                process_daily_notifications()
            else:
                # ✅ ユーザーごとの設定時刻と現在時刻を照合
                current_hour = now.hour
                current_minute = now.minute

                matched = UserNotificationSetting.objects.filter(
                    enabled=True,
                    notify_hour=current_hour,
                    notify_minute=current_minute,
                )

                if not matched.exists():
                    self.stdout.write(
                        self.style.HTTP_INFO(
                            f"⏩ {current_hour:02d}:{current_minute:02d} に送信対象ユーザーなし"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"✅ {matched.count()}ユーザーが送信対象"
                        )
                    )
                    process_daily_notifications(
                        target_users=[s.user for s in matched])

            self.stdout.write(self.style.SUCCESS("✅ 送信バッチ完了"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ エラーが発生しました: {e}"))

        end_time = timezone.localtime()
        duration = (end_time - start_time).total_seconds()
        self.stdout.write(self.style.HTTP_INFO(f"🕒 実行時間: {duration:.2f} 秒"))
