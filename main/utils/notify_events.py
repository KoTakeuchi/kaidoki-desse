from django.utils import timezone
from main.models import NotificationEvent


def create_restock_event(product, user):
    """在庫復活通知（在庫なし → 在庫あり）"""
    try:
        NotificationEvent.objects.create(
            product=product,
            user=user,
            event_type="stock_restore",
            message="在庫が復活しました",
            occurred_at=timezone.now(),
            is_read=False,
        )
        return True
    except Exception as e:
        print(f"[notify_events] create_restock_event error: {e}")
        return False


def create_stock_few_event(product, user):
    """在庫わずか通知（在庫あり → 在庫わずか）"""
    try:
        NotificationEvent.objects.create(
            product=product,
            user=user,
            event_type="stock_few",
            message="在庫がわずかになりました",
            occurred_at=timezone.now(),
            is_read=False,
        )
        return True
    except Exception as e:
        print(f"[notify_events] create_stock_few_event error: {e}")
        return False


def create_stock_none_event(product, user):
    """売り切れ通知（在庫あり/わずか → 在庫なし）"""
    try:
        NotificationEvent.objects.create(
            product=product,
            user=user,
            event_type="stock_none",
            message="売り切れました",
            occurred_at=timezone.now(),
            is_read=False,
        )
        return True
    except Exception as e:
        print(f"[notify_events] create_stock_none_event error: {e}")
        return False
