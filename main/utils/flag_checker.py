# --- START: main/utils/flag_checker.py ---
from main.models import Product


def update_flag_status(product: Product):
    """
    最新価格と通知条件に基づき flag_reached を更新する。
    """
    try:
        if not product.latest_price:
            product.flag_reached = False
            product.save(update_fields=["flag_reached"])
            return

        if product.flag_type == "buy_price" and product.threshold_price:
            product.flag_reached = product.latest_price <= product.threshold_price

        elif product.flag_type == "percent_off" and product.flag_value:
            discounted_price = product.initial_price * \
                (1 - product.flag_value / 100)
            product.flag_reached = product.latest_price <= discounted_price

        elif product.flag_type == "lowest_price" and product.threshold_price:
            product.flag_reached = product.latest_price <= product.threshold_price

        else:
            product.flag_reached = False

        product.save(update_fields=["flag_reached"])

    except Exception as e:
        print("DEBUG flag update error:", e)
# --- END: main/utils/flag_checker.py ---
