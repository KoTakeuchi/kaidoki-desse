# 実行ディレクトリ: C:\Users\takeuchi\Desktop\kaidoki-desse\main\tasks_send_notifications.py
import os
import sys
import django
from datetime import datetime
from django.utils import timezone
from django.core.mail import send_mail

# === プロジェクトルートをパスに追加 ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# === Django設定ロード ===
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kaidoki.settings")
django.setup()

# === モデルimport ===
from main.models import NotificationEvent, UserNotificationSetting


def send_notifications():
    """ユーザー通知設定を考慮してGmail経由でメール送信"""
    events = NotificationEvent.objects.filter(sent_flag=False).select_related("user", "product")
    if not events.exists():
        print("📭 新しい通知はありません。")
        return

    # 現在時刻（JSTベース）
    now = timezone.localtime()
    current_hour = now.hour
    current_minute = now.minute

    print(f"🕒 現在時刻: {current_hour:02}:{current_minute:02}")
    print("===============================================")

    user_settings = {s.user_id: s for s in UserNotificationSetting.objects.all()}
    grouped = {}
    for e in events:
        grouped.setdefault(e.user, []).append(e)

    sent_total = 0
    skipped_users = []

    for user, user_events in grouped.items():
        setting = user_settings.get(user.id)
        if not setting or not setting.enabled:
            skipped_users.append(user.username)
            continue

        # 時刻外の通知はスキップ
        if setting.notify_hour != current_hour or setting.notify_minute != current_minute:
            skipped_users.append(f"{user.username}（時刻外）")
            continue

        # メールアドレス未設定時はスキップ
        if not setting.email:
            skipped_users.append(f"{user.username}（メール未設定）")
            continue

        # === メール送信内容作成 ===
        subject = f"【買い時でっせ】{len(user_events)}件の通知があります"
        body_lines = [f"{ev.message}\n（{ev.occurred_at.strftime('%Y-%m-%d %H:%M:%S')}）"
                      for ev in user_events]
        body = "\n\n".join(body_lines)

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=None,  # settings.DEFAULT_FROM_EMAIL を使用
                recipient_list=[setting.email],
                fail_silently=False,
            )
            print(f"📨 {user.username} さんへメール送信成功 → {setting.email}")
        except Exception as e:
            print(f"⚠️ {user.username} さんへの送信エラー: {e}")
            continue

        # === 通知済みに更新 ===
        NotificationEvent.objects.filter(id__in=[e.id for e in user_events]).update(
            sent_flag=True, sent_at=timezone.now()
        )
        sent_total += len(user_events)
        print(f"✅ {user.username} さんの通知を送信済みに更新しました。\n")

    print("===============================================")
    print(f"✨ 全{sent_total}件の通知メール送信が完了しました。({datetime.now().strftime('%H:%M:%S')})")
    if skipped_users:
        print(f"⏩ スキップ対象: {', '.join(skipped_users)}")


if __name__ == "__main__":
    send_notifications()
