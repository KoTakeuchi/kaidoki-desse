# 実行ディレクトリ: C:\Users\takeuchi\Desktop\kaidoki-desse\main\test_send_mail.py
import os
import sys
import django
from django.core.mail import send_mail

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kaidoki.settings")
django.setup()

subject = "【買い時でっせ】テストメール送信"
message = "このメールはGmail SMTP経由のテスト送信です。\n設定は正しく機能しています。"
recipient = os.getenv("GMAIL_USER")  # 自分宛に送信

send_mail(subject, message, None, [recipient])
print(f"✅ テストメールを送信しました → {recipient}")
