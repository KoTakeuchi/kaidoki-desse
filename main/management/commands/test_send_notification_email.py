
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from main.models import Product, NotificationEvent
from main.utils.mailer import send_notification_summary


class Command(BaseCommand):
    """
    ✅ メールテンプレート送信テストコマンド
    実行例：
        python manage.py test_send_notification_email stock
        python manage.py test_send_notification_email price
    """

    help = "メール通知テンプレートをテスト送信します（stock / price）"

    def add_arguments(self, parser):
        parser.add_argument(
            "category",
            type=str,
            choices=["stock", "price"],
            help="テストするテンプレートの種類（stock または price）",
        )

    def handle(self, *args, **options):
        category = options["category"]
        self.stdout.write(self.style.NOTICE(f"📧 テストメール送信開始 ({category})"))

        user = User.objects.filter(is_active=True).first()
        if not user:
            self.stdout.write(self.style.ERROR("❌ 有効なユーザーが存在しません。"))
            return

        # ダミー商品を取得または作成
        product, _ = Product.objects.get_or_create(
            user=user,
            product_name="テスト商品A",
            defaults={
                "product_url": "https://www.rakuten.co.jp/",
                "regular_price": 12345,
                "image_url": "https://thumbnail.image.rakuten.co.jp/@0_mall/example/cabinet/sample.jpg",
            },
        )

        # ダミーイベントを作成（メール内容用）
        event, _ = NotificationEvent.objects.get_or_create(
            user=user,
            product=product,
            event_type="restock" if category == "stock" else "threshold_hit",
            defaults={
                "message": "テスト通知メッセージ",
                "occurred_at": timezone.now(),
                "sent_flag": False,
            },
        )

        # --- メール送信実行 ---
        from django.db.models import QuerySet
        send_notification_summary(
            user, NotificationEvent.objects.filter(pk=event.pk), category)

        self.stdout.write(self.style.SUCCESS("✅ テストメール送信完了"))
