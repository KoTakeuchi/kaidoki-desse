from main.models import Notification, NotificationEvent
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import statistics

from .models import NotificationLog, Product, PriceHistory, Notification, NotificationEvent
from main.utils.error_logger import log_error


# ===============================
# 📊 商品ダッシュボード（既存）
# ===============================
@login_required
def product_dashboard(request, pk):
    """
    商品の価格・在庫履歴をグラフ表示
    ※ここは既存処理をそのまま残す
    """
    product = get_object_or_404(Product, pk=pk, user=request.user)
    period = int(request.GET.get("days", 30))
    start_date = timezone.now() - timedelta(days=period)

    histories = PriceHistory.objects.filter(
        product=product, checked_at__gte=start_date
    ).order_by("checked_at")

    labels = [h.checked_at.strftime("%m/%d") for h in histories]
    prices = [h.price for h in histories]
    avg_price = round(statistics.mean(prices), 1) if prices else None

    data = {
        "labels": labels,
        "prices": prices,
        "avg_price": avg_price,
        "in_stock": product.is_in_stock,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(data, safe=False)

    return render(
        request,
        "main/dashboard.html",
        {"product": product, "data": data, "period": period},
    )


# ===============================
# 🔔 通知関連ビュー（統合版）
# ===============================
@login_required
def notification_list(request):
    """通知一覧ページ（Notification + NotificationEvent統合）"""
    try:
        filter_type = request.GET.get("filter", "all")
        sort_order = request.GET.get("sort", "desc")

        # --- 旧通知 ---
        notifications = Notification.objects.filter(user=request.user)
        # --- 新イベント ---
        events = NotificationEvent.objects.filter(user=request.user)

        unified = []

        for n in notifications:
            unified.append({
                "id": f"n-{n.id}",
                "type": "旧通知",
                "product_name": n.product.product_name,
                "message": n.message,
                "created_at": n.created_at,
                "is_read": n.is_read,
            })

        for e in events:
            unified.append({
                "id": f"e-{e.id}",
                "type": e.get_event_type_display(),
                "product_name": e.product.product_name,
                "message": e.message,
                "created_at": e.occurred_at,
                "is_read": e.sent_flag,  # sent_flag を既読扱い
            })

        # --- フィルタ処理 ---
        if filter_type == "unread":
            unified = [u for u in unified if not u["is_read"]]
        elif filter_type == "read":
            unified = [u for u in unified if u["is_read"]]

        # --- 並び順 ---
        unified.sort(key=lambda x: x["created_at"],
                     reverse=(sort_order == "desc"))

        return render(request, "main/notifications.html", {
            "notifications": unified,
            "filter_type": filter_type,
            "sort_order": sort_order,
        })

    except Exception as e:
        log_error(
            user=request.user,
            type_name=type(e).__name__,
            source="notification_list",
            err=e,
        )
        return render(request, "main/error_generic.html", {"error": e})


@login_required
def unread_count_api(request):
    """未読通知件数を返す（Notification + NotificationEvent 統合版）"""
    try:
        unread_notifications = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()

        unread_events = NotificationEvent.objects.filter(
            user=request.user, sent_flag=False
        ).count()

        total_unread = unread_notifications + unread_events
        return JsonResponse({"unread_count": total_unread})

    except Exception as e:
        log_error(
            user=request.user,
            type_name=type(e).__name__,
            source="unread_count_api",
            err=e,
        )
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def mark_notification_read(request, pk):
    """
    ✅ 通知を既読にする（Notification / NotificationEvent 両対応）
    """
    try:
        # --- IDが "n-40" のような形式なら整数に変換 ---
        if str(pk).startswith("n-"):
            pk = pk.replace("n-", "")

        # --- 通常通知 ---
        n = Notification.objects.filter(pk=pk, user=request.user).first()
        if n:
            n.is_read = True
            n.save(update_fields=["is_read"])
            return redirect("main:notifications")

        # --- イベント通知 ---
        e = NotificationEvent.objects.filter(pk=pk, user=request.user).first()
        if e:
            e.sent_flag = True
            e.save(update_fields=["sent_flag"])
            return redirect("main:notifications")

        # --- 見つからなかった場合 ---
        return JsonResponse({"error": "対象の通知が存在しません。"}, status=404)

    except Exception as e:
        log_error(
            user=request.user,
            type_name=type(e).__name__,
            source="mark_notification_read",
            err=e,
        )
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def notification_log_list(request):
    """送信済み通知ログ一覧"""
    try:
        logs = NotificationLog.objects.filter(
            user=request.user).order_by("-notified_at")

        return render(request, "main/notification_log.html", {
            "logs": logs,
        })
    except Exception as e:
        log_error(
            user=request.user,
            type_name=type(e).__name__,
            source="notification_log_list",
            err=e,
        )
        return render(request, "main/error_generic.html", {"error": e})
