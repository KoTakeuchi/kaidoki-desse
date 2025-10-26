from django.core.management.base import BaseCommand
from main.models import Notification
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = "古い通知（30日以上）を削除します。"

    def handle(self, *args, **kwargs):
        expiration_date = timezone.now() - timedelta(days=30)
        deleted_count, _ = Notification.objects.filter(
            created_at__lt=expiration_date
        ).delete()
        self.stdout.write(self.style.SUCCESS(f"{deleted_count} 件の通知を削除しました。"))
