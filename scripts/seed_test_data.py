import os
import sys
import django
import random
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kaidoki.settings")
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from main.models import Product, Category, PriceHistory

user = User.objects.get(username='testuser')

global_cats = list(Category.objects.filter(is_global=True, user__isnull=True))
user_cats = list(Category.objects.filter(user=user, is_global=False).exclude(category_name="未分類"))
all_cats = global_cats + user_cats

priorities = ["高", "普通"]
flag_types = ["buy_price", "percent_off", "lowest_price"]
stock_patterns = [
    (True, 3),
    (True, 1),
    (False, 0),
]
shop_names = ["楽天ショップA", "テストショップB", "サンプル堂", "D-rink北海道", "大柳ショップ"]
product_names = ["テスト商品_{}", "サンプル品_{}", "デモ商品_{}", "テスト用品_{}", "検証商品_{}"]

created = 0
for i in range(1, 101):
    priority = priorities[i % 2]
    flag_type = flag_types[i % 3]
    stock = stock_patterns[i % 3]
    initial_price = Decimal(random.randint(1000, 50000))

    if flag_type == "buy_price":
        threshold_price = Decimal(int(initial_price * Decimal("0.8")))
        flag_value = None
    elif flag_type == "percent_off":
        flag_value = Decimal(random.choice([10, 15, 20, 25, 30]))
        threshold_price = (initial_price * (1 - flag_value / 100)).quantize(Decimal("1"))
    else:
        threshold_price = None
        flag_value = None

    name_template = product_names[i % 5]
    p = Product.objects.create(
        user=user,
        product_name=name_template.format(i),
        shop_name=shop_names[i % 5],
        product_url=f"https://item.rakuten.co.jp/test/item{i:04d}/",
        initial_price=initial_price,
        latest_price=initial_price,
        threshold_price=threshold_price,
        flag_type=flag_type,
        flag_value=flag_value,
        priority=priority,
        is_in_stock=stock[0],
        latest_stock_count=stock[1],
    )

    cat_count = random.randint(1, 2)
    selected_cats = random.sample(all_cats, min(cat_count, len(all_cats)))
    p.categories.set(selected_cats)

    history_count = random.randint(3, 5)
    for j in range(history_count):
        price_variation = Decimal(random.randint(-2000, 2000))
        h_price = max(Decimal("100"), initial_price + price_variation)
        PriceHistory.objects.create(
            product=p,
            price=h_price,
            stock_count=stock[1],
            checked_at=timezone.now() - timezone.timedelta(days=history_count - j)
        )
    created += 1

print(f"✅ {created}件のテスト商品を作成しました")
print(f"優先度高: {Product.objects.filter(user=user, priority='高').count()}件")
print(f"優先度普通: {Product.objects.filter(user=user, priority='普通').count()}件")
print(f"在庫なし: {Product.objects.filter(user=user, latest_stock_count=0).count()}件")
print(f"在庫わずか: {Product.objects.filter(user=user, latest_stock_count=1).count()}件")
print(f"在庫あり: {Product.objects.filter(user=user, latest_stock_count=3).count()}件")
