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
from main.models import Product, Category, PriceHistory, NotificationEvent, ErrorLog

users = [User.objects.get(username=f'testuser{i}') for i in range(1, 4)]
flag_types = ["buy_price", "percent_off", "lowest_price"]
priorities = ["高", "普通"]
stock_patterns = [(True, 3), (True, 1), (False, 0)]
shop_names = ["楽天ショップA", "テストショップB", "サンプル堂"]
product_names = ["テスト商品_{}", "サンプル品_{}", "デモ商品_{}"]
event_types = ["threshold_hit", "discount_over", "lowest_price", "stock_few", "stock_restore", "stock_none"]
error_types = ["APIError", "DBConnectionError", "ValidationError", "TimeoutError"]
error_sources = ["update_prices", "flag_checker", "mailer", "rakuten_api"]
statuses = ["unresolved", "in_progress", "resolved"]

for user in users:
    global_cats = list(Category.objects.filter(is_global=True, user__isnull=True))
    user_cats = list(Category.objects.filter(user=user, is_global=False).exclude(category_name="未分類"))
    all_cats = global_cats + user_cats

    for i in range(1, 16):
        flag_type = flag_types[i % 3]
        stock = stock_patterns[i % 3]
        initial_price = Decimal(random.randint(1000, 50000))

        if flag_type == "buy_price":
            threshold_price = Decimal(int(initial_price * Decimal("0.8")))
            flag_value = None
        elif flag_type == "percent_off":
            flag_value = Decimal(random.choice([10, 15, 20]))
            threshold_price = (initial_price * (1 - flag_value / 100)).quantize(Decimal("1"))
        else:
            threshold_price = None
            flag_value = None

        p = Product.objects.create(
            user=user,
            product_name=product_names[i % 3].format(i),
            shop_name=shop_names[i % 3],
            product_url=f"https://item.rakuten.co.jp/test/{user.username}-item{i:04d}/",
            initial_price=initial_price,
            latest_price=initial_price,
            threshold_price=threshold_price,
            flag_type=flag_type,
            flag_value=flag_value,
            priority=priorities[i % 2],
            is_in_stock=stock[0],
            latest_stock_count=stock[1],
        )

        if all_cats:
            p.categories.set(random.sample(all_cats, min(2, len(all_cats))))

        for j in range(3):
            variation = Decimal(random.randint(-2000, 2000))
            h_price = max(Decimal("100"), initial_price + variation)
            PriceHistory.objects.create(
                product=p,
                price=h_price,
                stock_count=stock[1],
                checked_at=timezone.now() - timezone.timedelta(days=3 - j)
            )

    print(f"✅ {user.username}: 15件の商品作成完了")

    products = list(Product.objects.filter(user=user)[:5])
    for day in range(7):
        for _ in range(random.randint(2, 6)):
            product = random.choice(products)
            event_type = random.choice(event_types)
            NotificationEvent.objects.create(
                user=user,
                product=product,
                event_type=event_type,
                message=f"テスト通知：{event_type}",
                occurred_at=timezone.now() - timezone.timedelta(days=day),
                is_read=random.choice([True, False]),
                sent_flag=random.choice([True, False]),
            )
    print(f"✅ {user.username}: 通知イベント作成完了")

for day in range(7):
    for _ in range(random.randint(1, 4)):
        user = random.choice(users)
        ErrorLog.objects.create(
            user=user,
            type_name=random.choice(error_types),
            source=random.choice(error_sources),
            message=f"テストエラー：{random.choice(error_sources)}",
            status=random.choice(statuses),
            created_at=timezone.now() - timezone.timedelta(days=day),
        )
print("✅ エラーログ作成完了")
print(f"通知イベント総数: {NotificationEvent.objects.count()}")
print(f"エラーログ総数: {ErrorLog.objects.count()}")
print(f"商品総数: {Product.objects.count()}")
