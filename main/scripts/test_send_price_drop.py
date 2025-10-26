# 実行ディレクトリ: I:\school\kaidoki-desse\main\scripts\test_send_price_drop.py
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils.timezone import now
from main.utils.notifications import send_price_drop_email

User = get_user_model()

# ダミーリクエスト生成（URL構築用）
factory = RequestFactory()
request = factory.get("/")

# 宛先ユーザー（既存のtestuserを利用）
user = User.objects.get(username="testuser")

# ダミー商品データ（複数商品）
items = [
    {
        "product_name": "Fire TV Stick 4K Max",
        "new_price": 6480,
        "old_price": 7980,
        "url": "https://www.amazon.co.jp/dp/B09XXX",
        "time": now().strftime("%Y-%m-%d %H:%M"),
    },
    {
        "product_name": "AirPods Pro（第2世代）",
        "new_price": 32800,
        "old_price": 39800,
        "url": "https://www.apple.com/jp/airpods-pro/",
        "time": now().strftime("%Y-%m-%d %H:%M"),
    },
]

# テスト送信
send_price_drop_email(user, items, request)
