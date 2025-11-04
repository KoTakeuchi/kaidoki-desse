from django.utils import timezone
from main.models import NotificationEvent


def create_restock_event(product, user):
    """
    ✅ 在庫復活時に通知イベントを作成
    """
    try:
        NotificationEvent.objects.create(
            product=product,
            user=user,
            event_type="stock_low",  # モデル内の選択肢に合わせて
            message=f"「{product.product_name}」が再入荷しました！",
            occurred_at=timezone.now(),
            sent_flag=False,
        )
        return True
    except Exception as e:
        print(f"[notify_events] Error creating restock event: {e}")
        return False
