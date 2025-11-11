# 実行ディレクトリ: D:\school\kaidoki-desse\main\views_notification.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from main.models import NotificationEvent


@login_required
def notification_redirect(request, pk):
    """
    通知クリック時に既読状態にして商品詳細へ遷移
    """
    notification = get_object_or_404(
        NotificationEvent, id=pk, user=request.user)

    # ✅ 未読なら既読に変更
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])

    # 商品が紐づいていれば詳細ページへ
    product = notification.product
    if product:
        return redirect("main:product_detail", pk=product.id)
    else:
        # 商品が削除済みなどの場合は通知一覧に戻す
        return redirect("main:notification_list")
