# 実行ディレクトリ: C:\Users\takeuchi\Desktop\kaidoki-desse\auto_update_prices.py
import os
import sys
import time
import random
import schedule
import logging
from datetime import datetime, timedelta

import django
from django.utils import timezone
from django.db.models import Min

# === プロジェクトルートをパスに追加 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# === Django設定をロード ===
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kaidoki.settings")
django.setup()

from main.models import Product, PriceHistory, NotificationEvent, Flag
from main.tasks_send_notifications import send_notifications


# ==============================
# ログ設定
# ==============================
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

today_str = datetime.now().strftime("%Y-%m-%d")
LOG_FILE_INFO = os.path.join(LOG_DIR, f"auto_update_{today_str}.log")
LOG_FILE_ERROR = os.path.join(LOG_DIR, f"errors_{today_str}.log")

info_handler = logging.FileHandler(LOG_FILE_INFO, encoding="utf-8")
info_handler.setLevel(logging.INFO)
error_handler = logging.FileHandler(LOG_FILE_ERROR, encoding="utf-8")
error_handler.setLevel(logging.ERROR)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
for h in [info_handler, error_handler, console_handler]:
    h.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(info_handler)
logger.addHandler(error_handler)
logger.addHandler(console_handler)


def log_info(msg):
    print(msg)
    logger.info(msg)


def log_error(msg):
    print(msg)
    logger.error(msg)


# ==============================
# メイン処理
# ==============================
def update_prices():
    """登録済み商品の価格履歴を自動更新し、通知イベントを作成"""
    try:
        log_info("=" * 47)
        log_info(f"🕒 {datetime.now().strftime('%H:%M:%S')} | 価格更新処理を開始")
        log_info("=" * 47)

        products = Product.objects.all()
        if not products.exists():
            log_info("⚠ 商品データが存在しません。")
            return

        for product in products:
            base_price = float(product.initial_price or product.regular_price or 1000)
            new_price = int(base_price * random.uniform(0.8, 1.2))

            # === 価格履歴登録 ===
            PriceHistory.objects.create(
                product=product,
                price=new_price,
                checked_at=timezone.now(),
            )
            log_info(f"✅ {product.product_name} に ¥{new_price} を追加")

            # === 買い時価格通知 ===
            threshold = product.threshold_price
            if threshold and new_price <= float(threshold):
                message = f"💡『{product.product_name}』が買い時価格（¥{int(threshold)}）を下回りました！（現在¥{new_price}）"
                since = timezone.now() - timedelta(hours=24)
                exists = NotificationEvent.objects.filter(
                    user=product.user,
                    product=product,
                    event_type=NotificationEvent.EventType.THRESHOLD_HIT,
                    occurred_at__gte=since,
                ).exists()

                if not exists:
                    NotificationEvent.objects.create(
                        user=product.user,
                        product=product,
                        event_type=NotificationEvent.EventType.THRESHOLD_HIT,
                        message=message,
                    )
                    log_info(f"🧭 イベント記録: {message}")
                else:
                    log_info(f"⏩ 重複通知スキップ: {product.product_name}")

            # === 最安値通知 ===
            try:
                lowest_flag = Flag.objects.filter(
                    product=product, flag_type="LOWEST_PRICE", is_active=True
                ).first()

                if lowest_flag:
                    min_price = PriceHistory.objects.filter(
                        product=product
                    ).aggregate(Min("price"))["price__min"]

                    if min_price is not None and new_price == min_price:
                        message = f"🏷️『{product.product_name}』が過去最安値（¥{min_price:,}）を更新しました！"
                        NotificationEvent.objects.create(
                            user=product.user,
                            product=product,
                            event_type=NotificationEvent.EventType.LOWEST_PRICE,
                            message=message,
                        )
                        log_info(f"✅ 最安値通知: {message}")
            except Exception as e:
                log_error(f"[最安値判定エラー] {product.product_name}: {e}")

            # === 割引率通知 ===
            try:
                discount_flag = Flag.objects.filter(
                    product=product, flag_type="DISCOUNT_OVER", is_active=True
                ).first()

                if discount_flag and product.regular_price:
                    discount_rate = (
                        (float(product.regular_price) - new_price)
                        / float(product.regular_price)
                    ) * 100
                    threshold_rate = float(discount_flag.value or 0)

                    if discount_rate >= threshold_rate:
                        message = (
                            f"💰『{product.product_name}』が{threshold_rate:.0f}%以上の割引になりました！"
                            f"（現在 {discount_rate:.1f}% OFF, ¥{new_price}）"
                        )
                        since = timezone.now() - timedelta(hours=24)
                        exists = NotificationEvent.objects.filter(
                            user=product.user,
                            product=product,
                            event_type=NotificationEvent.EventType.DISCOUNT_OVER,
                            occurred_at__gte=since,
                        ).exists()

                        if not exists:
                            NotificationEvent.objects.create(
                                user=product.user,
                                product=product,
                                event_type=NotificationEvent.EventType.DISCOUNT_OVER,
                                message=message,
                            )
                            log_info(f"🎯 割引率イベント記録: {message}")
                        else:
                            log_info(f"⏩ 割引率通知スキップ: {product.product_name}")

            except Exception as e:
                log_error(f"[割引率判定エラー] {product.product_name}: {e}")

        log_info(f"💾 全商品の価格履歴を更新しました ({datetime.now().strftime('%H:%M:%S')})\n")

        # === 通知処理呼び出し ===
        log_info("💌 通知処理を実行中...")
        send_notifications()
        log_info("💌 通知処理が完了しました。\n")

    except Exception as e:
        log_error(f"❌ 例外発生: {str(e)}", exc_info=True)


# ==============================
# スケジュール設定
# ==============================
schedule.every(1).hours.do(update_prices)
# schedule.every(10).minutes.do(update_prices)  # テスト用

log_info("🕒 自動価格更新＋通知スケジュールを開始しました...")
update_prices()  # 起動時に一度実行

while True:
    schedule.run_pending()
    time.sleep(30)
