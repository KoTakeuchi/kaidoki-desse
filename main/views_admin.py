# =============================
#  Import
# =============================
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Count, Q
from datetime import datetime, timedelta

from main.models import (
    Product,
    ErrorLog,
    User,
    NotificationLog,  # 新モデル
)

# =============================
#  管理者判定
# =============================


def is_admin(user):
    return user.is_staff or user.is_superuser


# =============================
#  管理者ダッシュボード
# =============================

@user_passes_test(is_admin)
def admin_dashboard(request):
    week_ago = timezone.now() - timedelta(days=7)
    stats = {
        "user_count": User.objects.count(),
        "product_count": Product.objects.count(),
        "notification_week": NotificationLog.objects.filter(
            notified_at__gte=week_ago
        ).count(),
        "error_count": ErrorLog.objects.count(),
    }
    context = {
        "stats": stats,
        "latest_products": Product.objects.select_related("user").order_by("-created_at")[:5],
        "latest_notifications": NotificationLog.objects.select_related("user").order_by("-notified_at")[:5],
    }
    return render(request, "admin/admin_dashboard.html", context)


# =============================
#  ユーザー管理
# =============================

@user_passes_test(is_admin)
def admin_user_list(request):
    """全ユーザー一覧"""
    users = User.objects.annotate(product_count=Count("product"))
    return render(request, "admin/admin_user_list.html", {"users": users})


# =============================
#  商品管理
# =============================

@user_passes_test(is_admin)
def admin_product_list(request):
    """全ユーザーの商品一覧"""
    products = Product.objects.select_related(
        "user", "category").order_by("-created_at")
    return render(request, "admin/admin_product_list.html", {"products": products})


# =============================
#  通知ログ管理
# =============================

@user_passes_test(is_admin)
def admin_notification_list(request):
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

    return render(request, "admin/admin_notifications.html", {
        "logs": logs, "query": query, "start_date": start_date, "end_date": end_date,
    })


@user_passes_test(is_admin)
def admin_notification_detail(request, log_id):
    """通知ログ詳細"""
    log = get_object_or_404(NotificationLog, pk=log_id)
    return render(request, "admin/admin_notification_detail.html", {"log": log})


# =============================
#  エラーログ管理
# =============================

@user_passes_test(is_admin)
def admin_error_logs(request):
    """管理者用エラーログ一覧"""
    logs = ErrorLog.objects.all().order_by("-created_at")
    return render(request, "admin/admin_error_logs.html", {"logs": logs})
