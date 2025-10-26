# 実行ディレクトリ: I:\school\kaidoki-desse\main\views_dashboard.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import statistics

from .models import Product, PriceHistory, Notification


# ===============================
# 📊 商品ダッシュボード（価格・在庫履歴）
# ===============================
@login_required
def product_dashboard(request, pk):
    """価格・在庫履歴の可視化ページ"""
    product = get_object_or_404(Product, pk=pk, user=request.user)
    period = int(request.GET.get("days", 30))  # 期間指定(デフォ30日)
    start_date = timezone.now() - timedelta(days=period)
    histories = PriceHistory.objects.filter(
        product=product, checked_at__gte=start_date
    ).order_by("checked_at")

    # グラフデータ整形
    labels = [h.checked_at.strftime("%m/%d") for h in histories]
    prices = [h.price for h in histories]
    avg_price = round(statistics.mean(prices), 1) if prices else None

    data = {
        "labels": labels,
        "prices": prices,
        "avg_price": avg_price,
        "in_stock": product.is_in_stock,
    }

    # AjaxアクセスならJSON返却
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(data, safe=False)

    return render(
        request,
        "main/dashboard.html",
        {"product": product, "data": data, "period": period},
    )


# ===============================
# 🔔 通知関連ビュー
# ===============================
@login_required
def notification_list(request):
    """通知一覧ページ"""
    notifications = Notification.objects.filter(
        user=request.user).order_by("-created_at")
    return render(request, "main/notifications.html", {"notifications": notifications})


@login_required
def unread_count_api(request):
    """未読通知件数を返す"""
    count = Notification.objects.filter(
        user=request.user, is_read=False).count()
    return JsonResponse({"unread_count": count})


@login_required
def mark_notification_read(request, pk):
    """通知を既読にする"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({"status": "success"})


@login_required
def delete_notification(request, pk):
    """通知を削除する"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    return JsonResponse({"status": "deleted"})
