# main/management/commands/auto_mark_old_notifications.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from main.models import NotificationEvent, UserNotificationSetting


class Command(BaseCommand):
    """
    ✅ 古い通知を自動既読にするバッチ
    実行例: python manage.py auto_mark_old_notifications
    """

    help = "保持期間を過ぎた通知を自動的に既読にします"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🔄 古い通知の自動既読処理を開始します..."))

        settings = UserNotificationSetting.objects.all()
        total_marked = 0

        for setting in settings:
            user = setting.user
            retention_days = setting.notification_retention_days

            # 無制限（365日）の場合はスキップ
            if retention_days >= 365:
                continue

            # 保持期間を過ぎた日時を計算
            cutoff_date = timezone.now() - timedelta(days=retention_days)

            # 対象の通知を取得
            old_notifications = NotificationEvent.objects.filter(
                user=user,
                is_read=False,
                occurred_at__lt=cutoff_date
            )

            count = old_notifications.count()
            if count > 0:
                # 一括で既読にする
                old_notifications.update(is_read=True)
                total_marked += count
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ {user.username}: {count}件の通知を既読にしました")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\n完了: 合計 {total_marked}件の通知を既読にしました")
        )
