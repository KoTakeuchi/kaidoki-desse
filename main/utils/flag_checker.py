# --- START: main/utils/flag_checker.py ---
from django.utils import timezone
from main.models import Product, NotificationEvent


def update_flag_status(product: Product):
    """
    最新価格と通知条件に基づき flag_reached を更新する。
    買い時ラインを上抜けして再度下回ったときだけ通知を生成する。
    """
    try:
        if not product.latest_price:
            product.flag_reached = False
            product.save(update_fields=["flag_reached"])
            return

        # 更新前のflag_reachedを記録
        was_reached = product.flag_reached
        new_reached = False
        threshold_value = None

        if product.flag_type == "buy_price" and product.threshold_price:
            threshold_value = product.threshold_price
            new_reached = product.latest_price <= threshold_value

        elif product.flag_type == "percent_off" and product.flag_value:
            threshold_value = product.initial_price * \
                (1 - product.flag_value / 100)
            new_reached = product.latest_price <= threshold_value

        elif product.flag_type == "lowest_price":
            # 過去の最安値を取得
            from main.models import PriceHistory
            from django.db.models import Min
            min_price = PriceHistory.objects.filter(
                product=product
            ).exclude(
                price=product.latest_price
            ).aggregate(Min("price"))["price__min"]

            if min_price is not None:
                new_reached = product.latest_price < min_price
            else:
                new_reached = False

        product.flag_reached = new_reached
        product.save(update_fields=["flag_reached"])

        # ======================================================
        # 通知生成：
        # 「前回はラインを超えていた（was_reached=False）」かつ
        # 「今回ラインを下回った（new_reached=True）」ときだけ通知
        # ======================================================
        if new_reached and not was_reached:
            _create_notification(product)

    except Exception as e:
        print(f"[flag_checker] error: {e}")


def _create_notification(product: Product):
    """買い時通知イベントを生成する"""
    try:
        if product.flag_type == "buy_price":
            event_type = "threshold_hit"
            message = (
                f"『{product.product_name}』が買い時価格"
                f"（¥{int(product.threshold_price):,}）を下回りました！"
                f"　現在価格：¥{int(product.latest_price):,}"
            )
        elif product.flag_type == "percent_off":
            event_type = "discount_over"
            message = (
                f"『{product.product_name}』が{product.flag_value}%以上の"
                f"割引になりました！"
                f"　現在価格：¥{int(product.latest_price):,}"
            )
        elif product.flag_type == "lowest_price":
            event_type = "lowest_price"
            message = (
                f"『{product.product_name}』が過去最安値"
                f"（¥{int(product.latest_price):,}）を更新しました！"
            )
        else:
            return

        NotificationEvent.objects.create(
            product=product,
            user=product.user,
            event_type=event_type,
            message=message,
            occurred_at=timezone.now(),
            is_read=False,
        )
        print(f"[flag_checker] 通知生成: {product.product_name} / {event_type}")

    except Exception as e:
        print(f"[flag_checker] 通知生成エラー: {e}")
# --- END: main/utils/flag_checker.py ---
