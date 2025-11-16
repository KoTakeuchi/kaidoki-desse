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
    - 各商品画像URLをHTMLテンプレート内で表示
    - メール送信成功時に NotificationEvent を既読にする
    """
    if not events.exists():
        return

    # --- ユーザー設定確認 ---
    try:
        setting = UserNotificationSetting.objects.get(user=user)
    except UserNotificationSetting.DoesNotExist:
        return

    if not setting.enabled or not setting.email:
        return

    # --- カテゴリ別テンプレート設定 ---
    if category == "stock":
        subject = f"【買い時でっせ】在庫のお知らせ（{timezone.localtime().strftime('%Y-%m-%d')}）"
        template_html = "email/stock_notification.html"
        template_txt = "email/stock_notification.txt"
    else:
        subject = f"【買い時でっせ】本日の買い時まとめ（{timezone.localtime().strftime('%Y-%m-%d')}）"
        template_html = "email/price_notification.html"
        template_txt = "email/price_notification.txt"

    # --- コンテキスト生成 ---
    context = {
        "user": user,
        "events": events,
        "send_date": timezone.localtime().strftime("%Y-%m-%d"),
        "category": category,
        "site_name": "買い時でっせ",
        "site_url": "https://kaidoki.local",
    }

    # --- テンプレートをレンダリング ---
    text_content = render_to_string(template_txt, context)
    html_content = render_to_string(template_html, context)

    # --- メール生成 ---
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[setting.email],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        # === メール送信 ===
        msg.send(fail_silently=False)

        # === 対象イベントを送信済みに更新 ===
        events.update(is_read=True)

        print(f"📩 {user.username} へ {category} 通知メール送信完了（{events.count()}件）")

    except Exception as e:
        print(f"⚠️ {user.username} への通知メール送信に失敗: {e}")


def process_daily_notifications():
    """
    ✅ 日次通知バッチ：全ユーザーに対して未読通知をメール送信
    - メール通知ONのユーザーのみ
    - 優先度「高」の商品の未読通知をまとめて送信
    - 1日1回、設定された時刻に実行
    """
    # 通知設定でメール通知を有効にしているユーザーを取得
    settings_list = UserNotificationSetting.objects.filter(enabled=True)

    for setting in settings_list:
        user = setting.user

        # 未読の通知イベントを取得（優先度「高」のみ）
        unread_events = NotificationEvent.objects.filter(
            user=user,
            is_read=False,
            product__priority="高"
        ).order_by("-occurred_at")

        if not unread_events.exists():
            continue

        # メール本文を生成
        subject = f"【買い時でっせ】{unread_events.count()}件の通知があります"

        # テキストメール
        message = f"{user.username} 様\n\n"
        message += f"現在、{unread_events.count()}件の未読通知があります。\n\n"

        for event in unread_events[:10]:  # 最大10件
            message += f"・{event.product.product_name}\n"
            message += f"  {event.message}\n\n"

        if unread_events.count() > 10:
            message += f"他 {unread_events.count() - 10} 件\n\n"

        message += "詳細はアプリでご確認ください。\n"

        # メール送信
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[setting.email or user.email],
                fail_silently=False,
            )
            print(f"✅ {user.username} にメール送信完了（{unread_events.count()}件）")
        except Exception as e:
            print(f"❌ {user.username} へのメール送信失敗: {e}")
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
        # email_message += f"詳細: {settings.SITE_URL}/main/product/detail/{product.id}/\n"  # SITE_URLが未定義のため一時的にコメントアウト

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
