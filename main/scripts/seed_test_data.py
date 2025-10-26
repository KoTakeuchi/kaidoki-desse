from main.models import Product, PriceHistory, Category
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

user = User.objects.first()
cat, _ = Category.objects.get_or_create(category_name="テストカテゴリ")

# 既存データ削除
PriceHistory.objects.all().delete()
Product.objects.all().delete()

# ✅ テスト商品50件 + 各30日分履歴を作成（URL重複防止）
for i in range(1, 51):
    p = Product.objects.create(
        user=user,
        category=cat,
        product_name=f"テスト商品{i}",
        shop_name="テストショップ",
        product_url=f"https://example.com/item/{i}",  # ← ユニークURL
        threshold_price=random.randint(500, 2000),
        priority="高" if i % 2 == 0 else "普通",
        is_in_stock=True if i % 3 != 0 else False,
    )

    # 各商品の30日分の価格履歴を追加
    base_price = random.randint(500, 2500)
    for d in range(30):
        PriceHistory.objects.create(
            product=p,
            price=base_price + random.randint(-100, 100),
            stock_count=random.randint(0, 5),
            checked_at=timezone.now() - timedelta(days=(30 - d)),
        )

print("✅ テスト商品50件 × 30日分の履歴を作成しました。")
