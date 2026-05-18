# main/utils/mailer.py
from main.models import NotificationEvent, UserNotificationSetting
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone


def process_daily_notifications(target_users=None):  # ✅ target_users引数追加
    """
    日次通知バッチ：全ユーザーに対して未送信通知を1通にまとめてメール送信
    - target_users: 対象ユーザーリスト（Noneの場合は全enabledユーザー）
    - メール通知ONのユーザーのみ
    - 優先度「高」の商品の未送信通知
    - 買い時・在庫を1通にまとめて送信
    - sent_flag=False で絞り込み（is_read とは独立）
    """
    # ✅ target_usersが指定された場合はそのユーザーのみ対象
    if target_users is not None:
        settings_list = UserNotificationSetting.objects.filter(
            user__in=target_users, enabled=True
        )
    else:
        settings_list = UserNotificationSetting.objects.filter(enabled=True)

    for setting in settings_list:
        user = setting.user

        if not setting.email:
            print(f"⏩ {user.username} はメールアドレス未設定のためスキップ")
            continue

        # 買い時系イベント
        price_events = NotificationEvent.objects.filter(
            user=user,
            sent_flag=False,
            product__priority="高",
            event_type__in=["threshold_hit", "discount_over", "lowest_price"],
        ).order_by("-occurred_at").select_related("product")

        # 在庫系イベント
        stock_events = NotificationEvent.objects.filter(
            user=user,
            sent_flag=False,
            product__priority="高",
            # 修正後
            event_type__in=["stock_few", "stock_restore",
                            "stock_none"],  # ✅ stock_none追加
        ).order_by("-occurred_at").select_related("product")

        if not price_events.exists() and not stock_events.exists():
            print(f"⏩ {user.username} は未送信通知なしのためスキップ")
            continue

        subject = f"【買い時でっせ】本日の商品情報（{timezone.localtime().strftime('%Y-%m-%d')}）"

        context = {
            "user": user,
            "price_events": price_events,
            "stock_events": stock_events,
            "send_date": timezone.localtime().strftime("%Y-%m-%d"),
            "site_url": "https://kaidoki.local",  # デプロイ後に変更
            "site_name": "買い時でっせ",
        }

        html_content = render_to_string(
            "emails/daily_notification.html", context)

        text_lines = [f"{user.username} 様\n"]
        if price_events.exists():
            text_lines.append("■ 買い時商品")
            for e in price_events:
                text_lines.append(f"・{e.product.product_name}")
                text_lines.append(f"  {e.message}")
            text_lines.append("")
        if stock_events.exists():
            text_lines.append("■ 在庫情報")
            for e in stock_events:
                text_lines.append(f"・{e.product.product_name}")
                text_lines.append(f"  {e.message}")
            text_lines.append("")
        text_lines.append("詳細はアプリでご確認ください。")
        text_content = "\n".join(text_lines)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[setting.email],
        )
        msg.attach_alternative(html_content, "text/html")

        try:
            msg.send(fail_silently=False)

            total = price_events.count() + stock_events.count()
            price_events.update(sent_flag=True)
            stock_events.update(sent_flag=True)

            print(f"✅ {user.username} にメール送信完了（{total}件）")

        except Exception as e:
            print(f"❌ {user.username} へのメール送信失敗: {e}")


def send_notification_email(user, product, message):
    """個別通知メール送信（買い時検知時）"""
    try:
        setting = UserNotificationSetting.objects.get(user=user)
        if not setting.enabled or not setting.email:
            return

        subject = f"【買い時でっせ】{product.product_name} が買い時です！"
        message_body = f"{user.username} 様\n\n{product.product_name}\n{message}\n\n詳細はアプリでご確認ください。"

        from django.core.mail import send_mail
        send_mail(
            subject=subject,
            message=message_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[setting.email],
            fail_silently=False,
        )
        print(f"✅ {user.username} に通知メール送信完了: {product.product_name}")

    except Exception as e:
        print(f"❌ 通知メール送信失敗: {e}")
