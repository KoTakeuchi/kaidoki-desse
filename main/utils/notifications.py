# 実行ディレクトリ: I:\school\kaidoki-desse\main\utils\notifications.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.timezone import now
from django.urls import reverse


def send_price_drop_email(user, items, request=None):
    """
    値下がり通知メールを送信
    - items: [{"product_name": str, "new_price": int, "old_price": int, "url": str, "time": str}, ...]
    """
    try:
        # 通知設定ページのURL
        settings_url = request.build_absolute_uri(
            reverse("main:notification_settings")) if request else "#"

        # テンプレートに渡す変数
        context = {
            "user": user.username,
            "items": items,
            "time": now().strftime("%Y-%m-%d %H:%M:%S"),
            "settings_url": settings_url,
        }

        # メール本文生成
        message = render_to_string(
            "emails/price_drop_notification.txt", context)

        # メール送信
        send_mail(
            subject="[買い時でっせ] 本日の値下げ情報",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        print(f"[通知送信完了] {user.username} さん宛 ({len(items)} 件の値下げ情報)")
        return True

    except Exception as e:
        print(f"[通知送信失敗] {user.username}: {type(e).__name__} - {e}")
        return False
