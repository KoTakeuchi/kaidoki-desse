from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from main.models import NotificationEvent, UserNotificationSetting, NotificationLog


def send_notification_summary(user, events, category):
    """
    ✅ 通知イベントまとめ送信（在庫系／買い時系どちらにも対応）
    - category: "stock" または "price"
    - 各商品画像URLをHTMLテンプレート内で表示
    - メール送信成功時に NotificationLog に履歴を記録
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
        events.update(sent_flag=True, sent_at=timezone.now())

        # === ✅ 通知履歴を記録 ===
        for e in events:
            NotificationLog.objects.create(
                user=user,
                product=e.product,
                message=f"{e.product.product_name}（{e.get_event_type_display()}）通知メール送信済み",
            )

        print(f"📩 {user.username} へ {category} 通知メール送信完了（{events.count()}件）")

    except Exception as e:
        print(f"⚠️ {user.username} への通知メール送信に失敗: {e}")


def process_daily_notifications():
    """
    ✅ 1日1回の定期実行（crontabやバッチで使用）
    各ユーザーの未送信イベントを集約してメール送信
    """
    from django.contrib.auth.models import User

    users = User.objects.all()
    total_sent = 0

    for user in users:
        # --- 通知設定の有効ユーザーのみ ---
        setting = UserNotificationSetting.objects.filter(
            user=user, enabled=True, email__isnull=False
        ).first()
        if not setting:
            continue

        # --- 通知イベント抽出 ---
        stock_events = NotificationEvent.objects.filter(
            user=user,
            event_type__in=["restock", "stock_restore"],
            sent_flag=False,
        )

        price_events = NotificationEvent.objects.filter(
            user=user,
            event_type__in=["threshold_hit", "discount_over", "lowest_price"],
            sent_flag=False,
        )

        # --- カテゴリ別送信 ---
        if stock_events.exists():
            send_notification_summary(user, stock_events, "stock")
            total_sent += 1

        if price_events.exists():
            send_notification_summary(user, price_events, "price")
            total_sent += 1

    print(f"✅ 全ユーザー通知完了（合計 {total_sent} 件送信）")
