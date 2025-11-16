# 実行ディレクトリ: I:\school\kaidoki-desse\main\views_notification.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from main.models import NotificationEvent


# =============================
#  一般ユーザー用 通知機能
# =============================

@login_required
def notifications(request):
    """自分の通知一覧（未読のみ）"""
    # ✅ 未読通知のみを取得
    logs = (
        NotificationEvent.objects
        .filter(user=request.user, is_read=False)  # ✅ is_read=False を追加
        .select_related('product', 'user')
        .order_by("-occurred_at")
    )

    # ✅ デバッグログ
    print(f"[DEBUG] notifications view called")
    print(f"[DEBUG] User: {request.user.username}")
    print(f"[DEBUG] Unread notification count: {logs.count()}")

    # ✅ 最初の3件を表示（デバッグ用）
    for i, n in enumerate(list(logs[:3]), 1):
        product_name = n.product.product_name[:30] if n.product else 'None'
        print(f"[DEBUG] {i}. ID:{n.id} | {product_name} | {n.occurred_at}")

    return render(request, "main/notifications.html", {"logs": logs})


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
        return redirect("main:notifications")


@login_required
def mark_notification_read(request, pk):
    """通知を既読にする"""
    notification = get_object_or_404(
        NotificationEvent, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect("main:notifications")


@login_required
def delete_notification(request, pk):
    """通知を削除する"""
    notification = get_object_or_404(
        NotificationEvent, pk=pk, user=request.user)
    notification.delete()
    return redirect("main:notifications")


@login_required
def unread_count_api(request):
    """未読通知の数を返すAPI"""
    count = NotificationEvent.objects.filter(
        user=request.user, is_read=False).count()

    # ✅ デバッグログ
    print(f"[DEBUG] unread_count_api called")
    print(f"[DEBUG] User: {request.user.username}")
    print(f"[DEBUG] Unread count: {count}")

    return JsonResponse({"unread_count": count})
