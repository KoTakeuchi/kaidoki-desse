# 実行ディレクトリ: D:\school\kaidoki-desse\main\scripts\create_test_notifications.py
import os
import sys
import django

# ✅ manage.py shell でも単体実行でも動作するように設定
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    sys.path.append(r"D:\school\kaidoki-desse")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kaidoki.settings")
    django.setup()
else:
    django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from main.models import Product, NotificationEvent

User = get_user_model()


def run():
    user = User.objects.first()
    if not user:
        print("❌ ユーザーが存在しません。")
        return

    products = list(Product.objects.filter(user=user)[:10])
    if not products:
        print("❌ 商品データがありません。")
        return

    # ✅ 各イベントタイプを英語キーで定義（モデルに合わせる）
    event_map = {
        "stock_restore": "在庫復活通知",
        "stock_few": "在庫少通知",
        "threshold_hit": "買い時価格を下回る価格検知",
        "lowest_price": "過去最安値を更新",
        "discount_over": "指定割引率を下回る価格検知",
    }

    NotificationEvent.objects.all().delete()
    print("🧹 既存通知を削除しました。")

    # ✅ 各イベントタイプごとに2件ずつ生成
    for event_type, label in event_map.items():
        for p in products[:2]:
            NotificationEvent.objects.create(
                product=p,
                user=user,
                event_type=event_type,  # ← 英語キーを保存
                message=f"『{p.product_name}』で{label}が発生しました！",
                occurred_at=timezone.now(),
                is_read=False,
            )

    print(
        f"✅ 全イベント種別（{len(event_map)}種）× 各2件 = {len(event_map)*2}件 の通知を投入しました。"
    )


if __name__ == "__main__":
    run()
else:
    # manage.py shell 経由での呼び出し対応
    run()
