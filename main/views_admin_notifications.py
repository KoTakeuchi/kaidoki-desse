# 実行ディレクトリ: D:\school\kaidoki-desse\main\views_admin_notifications.py
from django.contrib.auth.decorators import login_required
from main.models import ErrorLog  # すでに存在しているモデルを利用
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, timedelta
from .models import NotificationLog

# =============================
#  管理者判定
# =============================


def is_admin(user):
    return user.is_staff or user.is_superuser


# =============================
#  管理者用通知ログ
# =============================

@user_passes_test(is_admin)
def notification_log_list(request):
    """通知ログ一覧（管理者専用）"""
    query = request.GET.get("q", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    logs = NotificationLog.objects.all().order_by("-notified_at")

    if query:
        logs = logs.filter(
            Q(user__username__icontains=query)
            | Q(product__product_name__icontains=query)
            | Q(message__icontains=query)
        )
    if start_date:
        logs = logs.filter(notified_at__gte=start_date)
    if end_date:
        logs = logs.filter(notified_at__lte=end_date)

    context = {
        "logs": logs,
        "query": query,
        "start_date": start_date,
        "end_date": end_date,
    }
    return render(request, "admin_notifications.html", context)


@user_passes_test(is_admin)
def notification_log_detail(request, log_id):
    """通知ログ詳細画面（管理者専用）"""
    log = get_object_or_404(NotificationLog, pk=log_id)
    return render(request, "admin_notification_detail.html", {"log": log})


# ============================================================
#  管理者用：エラーログ一覧
# ============================================================


@user_passes_test(is_admin)
def error_logs(request):
    """管理者用のエラーログ一覧"""
    logs = ErrorLog.objects.all().order_by("-created_at")
    return render(request, "main/error_logs.html", {"logs": logs})


# =============================
#  一般ユーザー用 通知機能
# =============================

@login_required
def notifications(request):
    """自分の通知一覧"""
    logs = NotificationLog.objects.filter(
        user=request.user).order_by("-notified_at")
    return render(request, "main/notifications.html", {"logs": logs})


@login_required
def mark_notification_read(request, pk):
    """通知を既読にする"""
    notification = get_object_or_404(NotificationLog, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect("main:notifications")


@login_required
def delete_notification(request, pk):
    """通知を削除する"""
    notification = get_object_or_404(NotificationLog, pk=pk, user=request.user)
    notification.delete()
    return redirect("main:notifications")


@login_required
def unread_count_api(request):
    """未読通知の数を返すAPI"""
    count = NotificationLog.objects.filter(
        user=request.user, is_read=False).count()
    return JsonResponse({"unread_count": count})
