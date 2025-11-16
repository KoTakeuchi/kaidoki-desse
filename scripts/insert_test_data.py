import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトのルートパスを追加
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# DJANGO_SETTINGS_MODULEを設定
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kaidoki.settings")

# ✅ 修正：django.setup() を先に実行
import django
django.setup()

# ✅ 修正：django.setup() の後に import
from django.utils import timezone
from main.models import Product, PriceHistory
from django.contrib.auth import get_user_model

User = get_user_model()

# ======================================================
# 設定
# ======================================================
# 既存データを削除するか（True: 全削除, False: 追加のみ）
DELETE_EXISTING = False

# 特定商品にのみデータ追加（None なら新規作成）
TARGET_PRODUCT_ID = 358  # Noneにすると新規商品作成

# 過去何日分のデータを作成するか
DAYS = 30

# ======================================================
# 既存データ削除（オプション）
# ======================================================
if DELETE_EXISTING:
    print("既存 Product / PriceHistory データ削除中...")
    PriceHistory.objects.all().delete()
    Product.objects.all().delete()

# ======================================================
# 特定商品に価格履歴を追加
# ======================================================
if TARGET_PRODUCT_ID:
    try:
        product = Product.objects.get(id=TARGET_PRODUCT_ID)
        print(f"商品ID {TARGET_PRODUCT_ID} ({product.product_name}) に価格履歴を追加します...")

        # 既存の履歴を削除（オプション）
        # PriceHistory.objects.filter(product=product).delete()

        base_price = float(product.latest_price or product.initial_price or 5000)

        for i in range(DAYS, 0, -1):
            date = timezone.now() - timedelta(days=i)
            price_fluctuation = random.randint(-500, 500)
            price = max(1000, int(base_price + price_fluctuation))
            stock = random.randint(0, 5)

            # 重複チェック
            if not PriceHistory.objects.filter(product=product, checked_at__date=date.date()).exists():
                PriceHistory.objects.create(
                    product=product,
                    price=price,
                    stock_count=stock,
                    checked_at=date,
                )

        print(f"✅ {DAYS}件の価格履歴を追加しました")

    except Product.DoesNotExist:
        print(f"❌ 商品ID {TARGET_PRODUCT_ID} が見つかりません")
        sys.exit(1)

# ======================================================
# 新規商品作成（TARGET_PRODUCT_ID が None の場合）
# ======================================================
else:
    # ユーザー取得（最初のユーザーを使用）
    user = User.objects.first()
    if not user:
        print("❌ ユーザーが存在しません")
        sys.exit(1)

    print(f"新規テストデータ作成中（ユーザー: {user.username}）...")

    # 商品パターン定義
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
            "flag_value": 10,
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
    ]

    def get_stock_count(info, i):
        if "在庫0" in info["product_name"]:
            return 0 if i % 10 == 0 else random.randint(5, 20)
        elif "在庫わずか" in info["product_name"]:
            return 1 if i % 7 == 0 else random.randint(10, 30)
        else:
            return random.randint(5, 50)

    for info in products_info:
        product = Product.objects.create(
            product_name=info["product_name"],
            shop_name=info["shop_name"],
            initial_price=info["initial_price"],
            latest_price=info["initial_price"],
            threshold_price=info.get("threshold_price"),
            flag_type=info["flag_type"],
            flag_value=info.get("flag_value"),
            priority=info["priority"],
            is_in_stock=True,
            user=user,
            product_url=f"https://example.com/test/{random.randint(1000, 9999)}",
        )

        # 過去180日分データ生成
        for i in range(180):
            date = timezone.now() - timedelta(days=(179 - i))
            price_fluctuation = random.randint(-1500, 1500)
            price = max(1000, info["initial_price"] + price_fluctuation)
            stock = get_stock_count(info, i)

            if not PriceHistory.objects.filter(product=product, checked_at=date).exists():
                PriceHistory.objects.create(
                    product=product,
                    price=price,
                    stock_count=stock,
                    checked_at=date,
                )

    print("✅ テストデータ登録完了")
