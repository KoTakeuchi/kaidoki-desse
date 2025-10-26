# 実行ディレクトリ: C:\Users\takeuchi\Desktop\kaidoki-desse\auto_update_prices.py
import os
import sys
import time
import random
import schedule
from datetime import datetime

# === プロジェクトルートをパスに追加 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# ✅ 正しい Django 設定モジュール（manage.py と同じ）
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kaidoki.settings")

# ✅ Django の初期化（models より先に必ず実行）
import django
django.setup()

# ✅ setup 完了後にモデルを import（順番が最重要）
from main.models import Product, PriceHistory
from django.utils import timezone


def update_prices():
    """登録済み商品の価格履歴を自動更新（ランダム生成）"""
    products = Product.objects.all()
    if not products.exists():
        print("⚠ 商品データが存在しません。")
        return

    for product in products:
        base_price = float(product.initial_price or product.regular_price or 1000)
        new_price = int(base_price * random.uniform(0.8, 1.2))
        PriceHistory.objects.create(
            product=product,
            price=new_price,
            checked_at=timezone.now(),
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {product.product_name} に ¥{new_price} を追加")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 💾 全商品の価格履歴を更新しました\n")


# === 定期スケジュール設定 ===
schedule.every(1).hours.do(update_prices)
# schedule.every(10).minutes.do(update_prices)  # ← テスト用にコメント解除OK

print("🕒 自動価格更新スケジュールを開始しました...")
update_prices()  # 起動時に一度実行

# === 永続ループ ===
while True:
    schedule.run_pending()
    time.sleep(30)
