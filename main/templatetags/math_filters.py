# 実行ディレクトリ: I:\school\kaidoki-desse\main\templatetags\math_filters.py
from django import template

register = template.Library()


@register.filter
def percent_off(price, discount_percent):
    """
    登録時価格 × (1 - 割引率 / 100) を計算して返す。
    - price: Decimal or int
    - discount_percent: Decimal or int
    """
    try:
        if price is None or discount_percent is None:
            return None
        result = float(price) * (1 - float(discount_percent) / 100)
        return round(result)
    except Exception:
        return None
