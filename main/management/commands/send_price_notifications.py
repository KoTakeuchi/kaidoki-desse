# 実行ディレクトリ: I:\school\kaidoki-desse
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import models   # ✅ ← これを追加！
from main.models import Product, NotificationLog
from main.utils.notifications import send_price_drop_email
from django.utils.timezone import now


class Command(BaseCommand):
    help = "1日1回、価格フラグ達成ユーザーに通知メールを送信"

    def handle(self, *args, **options):
        print("📨 [開始] 価格通知メール送信バッチ")
        today = now().strftime("%Y-%m-%d %H:%M:%S")
        success_cnt = 0
        fail_cnt = 0

        users = User.objects.filter(is_active=True)

        for user in users:
            try:
                # ✅ 通知対象: 現在価格が閾値以下の商品
                flagged_items = Product.objects.filter(
                    user=user,
                    threshold_price__isnull=False,
                    regular_price__lte=models.F("threshold_price"),
                )

                if not flagged_items.exists():
                    continue

                # ✅ メール本文に渡す形式
                items = [
                    {
                        "product_name": p.product_name,
                        "new_price": p.regular_price,
                        "old_price": p.initial_price or p.regular_price,
                        "url": p.product_url,
                        "time": today,
                    }
                    for p in flagged_items
                ]

                send_price_drop_email(user, items)
                success_cnt += 1

                # ✅ 通知ログ記録
                for p in flagged_items:
                    NotificationLog.objects.create(
                        product=p,
                        user=user,
                        message=f"{p.product_name} の値下げ通知を送信",
                    )

            except Exception as e:
                fail_cnt += 1
                print(f"[通知失敗] {user.username}: {e}")

        print(f"✅ [完了] 通知成功: {success_cnt}件 / 失敗: {fail_cnt}件")
