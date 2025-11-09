# --- START: scripts/insert_test_data.py ---
import os
import sys
import django
import random
from datetime import datetime, timedelta

# ====== プロジェクトルートをパスに追加 ======
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

# ====== Django設定モジュール指定 ======
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kaidoki.settings")

# ====== Django初期化 ======
django.setup()

# ====== モデルを初期化後に読み込み ======
from main.models import Product, PriceHistory

# ======================================================
# 既存データ削除
# ======================================================
print("既存 Product / PriceHistory データ削除中...")
PriceHistory.objects.all().delete()
Product.objects.all().delete()

# ======================================================
# 商品パターン定義
# ======================================================
products_info = [
    {
        "product_name": "テスト商品A（買い時価格）",
        "shop_name": "テストショップA",
        "priority": "高",
        "initial_price": 20000,
        "threshold_price": 15000,
        "flag_type": "buy_price",
    },
    {
        "product_name": "テスト商品B（割引率10%）",
        "shop_name": "テストショップB",
        "priority": "普通",
        "initial_price": 30000,
        "threshold_price": 10,
        "flag_type": "percent_off",
    },
    {
        "product_name": "テスト商品C（最安値通知）",
        "shop_name": "テストショップC",
        "priority": "普通",
        "initial_price": 18000,
        "threshold_price": None,
        "flag_type": "lowest_price",
    },
    {
        "product_name": "テスト商品D（在庫0パターンあり）",
        "shop_name": "テストショップD",
        "priority": "普通",
        "initial_price": 25000,
        "threshold_price": 18000,
        "flag_type": "buy_price",
    },
    {
        "product_name": "テスト商品E（在庫わずかパターンあり）",
        "shop_name": "テストショップE",
        "priority": "高",
        "initial_price": 40000,
        "threshold_price": 15,
        "flag_type": "percent_off",
    },
]

# ======================================================
# データ生成
# ======================================================
print("テストデータ作成中...")

for info in products_info:
    product = Product.objects.create(
        product_name=info["product_name"],
        shop_name=info["shop_name"],
        initial_price=info["initial_price"],
        latest_price=info["initial_price"],
        threshold_price=info["threshold_price"],
        flag_type=info["flag_type"],
        priority=info["priority"],
        is_in_stock=True,
        user_id=1,
        product_url=f"https://example.com/test/{random.randint(1000,9999)}",  # ★ユニークURL対応
    )

    # 過去180日分データ生成（日ごと1件ずつ）
    for i in range(180):
        # ✅ 修正：datetime型で180日前から順番に設定
        date = datetime.now() - timedelta(days=(179 - i))
        price_fluctuation = random.randint(-1500, 1500)
        price = max(1000, info["initial_price"] + price_fluctuation)

        # 在庫パターン分岐
        if "在庫0" in info["product_name"]:
            stock = 0 if i % 10 == 0 else random.randint(5, 20)
        elif "在庫わずか" in info["product_name"]:
            stock = 1 if i % 7 == 0 else random.randint(10, 30)
        else:
            stock = random.randint(5, 50)

        PriceHistory.objects.create(
            product=product,
            price=price,
            stock_count=stock,
            checked_at=date,  # ✅ 修正後：datetimeを直接使用
        )

print("✅ テストデータ登録完了")
# --- END: scripts/insert_test_data.py ---
