from datetime import datetime, timedelta
from statistics import mean
from django.utils import timezone
from django.conf import settings
from .models import (
    PriceHistory,
    Product,
    Notification,
    UserNotificationSetting,
    ErrorLog,
)
import requests
import logging

logger = logging.getLogger(__name__)

# ============================================================
# 🔹 楽天商品検索APIから在庫・数量情報を取得する関数（数量対応版）
# ============================================================


def fetch_rakuten_product_data(product_name, user=None):
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"
    params = {
        "applicationId": settings.RAKUTEN_APP_ID,
        "keyword": product_name,
        "hits": 1,
        "format": "json",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "Items" not in data or len(data["Items"]) == 0:
            msg = f"楽天APIレスポンスに商品がありません: {product_name}"
            logger.warning(msg)
            if user:
                ErrorLog.objects.create(
                    user=user,
                    type="RakutenAPIWarning",
                    source="fetch_rakuten_product_data",
                    detail=msg,
                )
            return {
                "availability": None,
                "stock_count": None,
                "price": None,
                "shop_name": None,
                "url": None,
            }

        item = data["Items"][0]["Item"]
        availability = item.get("availability", None)
        price = item.get("itemPrice", None)
        shop_name = item.get("shopName", None)
        url = item.get("itemUrl", None)

        stock_count = None
        if "stockQuantity" in item:
            try:
                stock_count = int(item["stockQuantity"])
            except (TypeError, ValueError):
                stock_count = None
        elif "availability" in item:
            stock_count = 1 if item["availability"] == 1 else 0

        logger.info(
            f"[RakutenAPI] {product_name}: availability={availability}, stock_count={stock_count}, price={price}"
        )

        return {
            "availability": availability,
            "stock_count": stock_count,
            "price": price,
            "shop_name": shop_name,
            "url": url,
        }

    except requests.exceptions.Timeout:
        msg = f"楽天APIタイムアウト: {product_name}"
    except requests.exceptions.HTTPError as e:
        msg = f"楽天API HTTPエラー: {product_name} ({e})"
    except requests.exceptions.RequestException as e:
        msg = f"楽天API通信エラー: {product_name} ({e})"
    except Exception as e:
        msg = f"楽天APIその他エラー: {product_name} ({e})"

    logger.error(msg)
    if user:
        ErrorLog.objects.create(
            user=user,
            type="RakutenAPIError",
            source="fetch_rakuten_product_data",
            detail=msg,
        )

    return {
        "availability": None,
        "stock_count": None,
        "price": None,
        "shop_name": None,
        "url": None,
    }

# ============================================================
# 🔹 在庫情報更新ロジック
# ============================================================


def update_stock_status(product, api_data):
    try:
        availability = api_data.get("availability")
        stock_count = api_data.get("stock_count")

        if availability is None:
            return

        new_stock = True if str(availability) == "1" else False
        product.is_in_stock = new_stock

        if stock_count is not None:
            product.latest_stock_count = stock_count

        product.save(update_fields=["is_in_stock", "latest_stock_count"])

        # 再入荷通知
        if new_stock and product.flag_type == "restock":
            recent_time = timezone.now() - timedelta(hours=24)
            if not Notification.objects.filter(
                user=product.user,
                product=product,
                type="restock",
                created_at__gte=recent_time,
            ).exists():
                Notification.objects.create(
                    user=product.user,
                    product=product,
                    message=f"{product.product_name} が再入荷しました！ 🛒",
                    type="restock",
                )
                logger.info(
                    f"[RestockNotify] {product.product_name} に再入荷通知を送信")

        # 在庫少通知
        if product.priority == "高" and stock_count is not None and stock_count > 0:
            threshold = 3
            if stock_count <= threshold:
                recent_time = timezone.now() - timedelta(hours=1)
                already_sent = Notification.objects.filter(
                    user=product.user,
                    product=product,
                    type="stock_low",
                    created_at__gte=recent_time,
                ).exists()

                if not already_sent:
                    Notification.objects.create(
                        user=product.user,
                        product=product,
                        message=f"{product.product_name} の在庫が残りわずかです（{stock_count}個）⚠️",
                        type="stock_low",
                    )
                    logger.info(
                        f"[StockLowNotify] {product.product_name} 残り {stock_count} 個")

    except Exception as e:
        logger.error(f"[StockUpdateError] {product.id}: {e}")
        ErrorLog.objects.create(
            user=product.user,
            type="StockUpdateError",
            source="update_stock_status",
            detail=str(e),
        )

# ============================================================
# 🔹 買い時判定
# ============================================================


def should_notify(product, latest_price):
    try:
        if not product.threshold_price or latest_price is None:
            return False

        threshold = float(product.threshold_price)
        price = float(latest_price)
        return price <= threshold

    except Exception as e:
        msg = f"[should_notify] Error for {product.product_name}: {e}"
        logger.error(msg)
        if getattr(product, "user", None):
            ErrorLog.objects.create(
                user=product.user,
                type="LogicError",
                source="should_notify",
                detail=msg,
            )
        return False

# ============================================================
# 🔹 通知送信可否
# ============================================================


def can_send_notification(user, product):
    try:
        setting = UserNotificationSetting.objects.filter(user=user).first()
        if not setting or not setting.enabled:
            return False

        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        recent_exists = Notification.objects.filter(
            user=user,
            product=product,
            created_at__gte=one_hour_ago
        ).exists()

        return not recent_exists

    except Exception as e:
        ErrorLog.objects.create(
            user=user,
            type="LogicError",
            source="can_send_notification",
            detail=str(e)
        )
        return False

# ============================================================
# 🔹 統計ロジック
# ============================================================


def calc_price_change_rate(old_price: int, new_price: int) -> float:
    if old_price == 0:
        return 0.0
    return round(((new_price - old_price) / old_price) * 100, 2)


def get_average_price(product: Product, days: int = 30) -> float:
    cutoff = datetime.now().date() - timedelta(days=days)
    records = PriceHistory.objects.filter(
        product=product, checked_at__date__gte=cutoff)
    prices = [r.price for r in records if r.price is not None]
    return round(mean(prices), 2) if prices else 0


def get_price_deviation(product: Product) -> float:
    avg = get_average_price(product, 30)
    if avg == 0:
        return 0.0
    latest = PriceHistory.objects.filter(
        product=product).order_by('-checked_at').first()
    if not latest:
        return 0.0
    return round(((float(latest.price) - float(avg)) / float(avg)) * 100, 2)

# ============================================================
# 🔹 グラフ描画用データ生成（価格＋在庫数）
# ============================================================


def get_price_trend_data(product: Product):
    """
    グラフ描画用：価格＋在庫数（stock）をJSON形式で返す。
    None値でも0で埋めて必ずグラフに表示できるように修正。
    """
    price_histories = PriceHistory.objects.filter(
        product=product
    ).order_by("checked_at")

    result = []
    for p in price_histories:
        price_val = float(p.price) if p.price is not None else 0.0
        stock_val = int(p.stock_count) if p.stock_count is not None else 0

        result.append({
            "date": p.checked_at.strftime("%Y-%m-%d %H:%M"),
            "price": price_val,
            "stock": stock_val,
        })

    # ✅ データが全て0でも、空配列は返さない
    if not result:
        result = [{
            "date": timezone.now().strftime("%Y-%m-%d %H:%M"),
            "price": 0,
            "stock": 0,
        }]

    return result

# ============================================================
# 🔹 グラフ補助線（平均価格・買い時価格ライン）
# ============================================================


def get_trend_lines(product: Product):
    """
    グラフ上に表示する補助線データを返す。
    平均価格（過去30日）と買い時閾値。
    """
    try:
        avg_price = get_average_price(product, 30)
        threshold = float(
            product.threshold_price) if product.threshold_price else None
        return {"average": avg_price, "threshold": threshold}
    except Exception:
        return {"average": 0, "threshold": None}
