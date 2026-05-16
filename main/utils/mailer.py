# main/utils/mailer.py
from main.models import NotificationEvent, UserNotificationSetting, Product
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db.models import Q


def send_notification_summary(user, events, category):
    """
    ✅ 通知イベントまとめ送信（在庫系／買い時系どちらにも対応）
    - category: "stock" または "price"
    - メール送信成功時に sent_flag=True に更新（is_read は触らない）
    """
    if not events.exists():
        return

    try:
        setting = UserNotificationSetting.objects.get(user=user)
    except UserNotificationSetting.DoesNotExist:
        return

    if not setting.enabled or not setting.email:
        return

    if category == "stock":
        subject = f"【買い時でっせ】在庫のお知らせ（{timezone.localtime().strftime('%Y-%m-%d')}）"
        template_html = "email/stock_notification.html"
        template_txt = "email/stock_notification.txt"
    else:
        subject = f"【買い時でっせ】本日の買い時まとめ（{timezone.localtime().strftime('%Y-%m-%d')}）"
        template_html = "email/price_notification.html"
        template_txt = "email/price_notification.txt"

    context = {
        "user": user,
        "events": events,
        "send_date": timezone.localtime().strftime("%Y-%m-%d"),
        "category": category,
        "site_name": "買い時でっせ",
        "site_url": "https://kaidoki.local",
    }

    text_content = render_to_string(template_txt, context)
    html_content = render_to_string(template_html, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[setting.email],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)

        # ✅ 修正：is_read ではなく sent_flag を更新
        events.update(sent_flag=True)

        print(f"📩 {user.username} へ {category} 通知メール送信完了（{events.count()}件）")

    except Exception as e:
        print(f"⚠️ {user.username} への通知メール送信に失敗: {e}")


def process_daily_notifications():
    """
    ✅ 日次通知バッチ：全ユーザーに対して未送信通知をメール送信
    - メール通知ONのユーザーのみ
    - 優先度「高」の商品の未送信通知をまとめて送信
    - sent_flag=False で絞り込み（is_read とは独立）
    """
    settings_list = UserNotificationSetting.objects.filter(enabled=True)

    for setting in settings_list:
        user = setting.user

        # ✅ 修正：is_read → sent_flag=False で絞り込み
        unsent_events = NotificationEvent.objects.filter(
            user=user,
            sent_flag=False,          # ✅ メール未送信のもの
            product__priority="高"
        ).order_by("-occurred_at")

        if not unsent_events.exists():
            continue

        subject = f"【買い時でっせ】{unsent_events.count()}件の通知があります"

        message = f"{user.username} 様\n\n"
        message += f"現在、{unsent_events.count()}件の通知があります。\n\n"

        for event in unsent_events[:10]:
            message += f"・{event.product.product_name}\n"
            message += f"  {event.message}\n\n"

        if unsent_events.count() > 10:
            message += f"他 {unsent_events.count() - 10} 件\n\n"

        message += "詳細はアプリでご確認ください。\n"

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[setting.email or user.email],
                fail_silently=False,
            )

            # ✅ 修正：送信済みフラグを更新（is_read は触らない）
            unsent_events.update(sent_flag=True)

            print(f"✅ {user.username} にメール送信完了（{unsent_events.count()}件）")

        except Exception as e:
            print(f"❌ {user.username} へのメール送信失敗: {e}")


def send_notification_email(user, product, message):
    """
    ✅ 個別通知メール送信（買い時検知時）
    """
    try:
        setting = UserNotificationSetting.objects.get(user=user)
        if not setting.enabled:
            return

        subject = f"【買い時でっせ】{product.product_name} が買い時です！"

        email_message = f"{user.username} 様\n\n"
        email_message += f"{product.product_name}\n"
        email_message += f"{message}\n\n"

        send_mail(
            subject=subject,
            message=email_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[setting.email or user.email],
            fail_silently=False,
        )
        print(f"✅ {user.username} に通知メール送信完了: {product.product_name}")

    except Exception as e:
        print(f"❌ 通知メール送信失敗: {e}")
