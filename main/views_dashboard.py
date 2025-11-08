# --- START: main/views_dashboard.py ---
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import Product, PriceHistory, NotificationEvent


# ======================================================
# ダッシュボード（通知・価格推移・登録状況）
# ======================================================
@login_required
def dashboard_view(request):
    """ユーザーダッシュボード"""
    user = request.user

    # --- 登録商品数 ---
    product_count = Product.objects.filter(user=user).count()

    # --- 通知イベント（最新5件） ---
    notifications = (
        NotificationEvent.objects.filter(user=user)
        .order_by("-created_at")[:5]
    )

    # --- 通知未送信・送信済み数 ---
    unread_count = NotificationEvent.objects.filter(
        user=user, is_sent=False
    ).count()

    sent_count = NotificationEvent.objects.filter(
        user=user, is_sent=True
    ).count()

    # --- 最近1週間の価格履歴更新件数 ---
    one_week_ago = timezone.now() - timedelta(days=7)
    price_updates = (
        PriceHistory.objects.filter(
            product__user=user, created_at__gte=one_week_ago
        )
        .values("product__product_name")
        .annotate(update_count=Count("id"))
        .order_by("-update_count")[:5]
    )

    # --- グラフ用データ（例: 登録商品カテゴリ別数） ---
    category_stats = (
        Product.objects.filter(user=user)
        .values("categories__category_name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    context = {
        "product_count": product_count,
        "notifications": notifications,
        "unread_count": unread_count,
        "sent_count": sent_count,
        "price_updates": price_updates,
        "category_stats": category_stats,
    }
    return render(request, "user/dashboard.html", context)


# ======================================================
# 通知履歴一覧
# ======================================================
@login_required
def notification_history(request):
    """通知履歴ページ"""
    user = request.user
    logs = NotificationEvent.objects.filter(user=user).order_by("-created_at")

    return render(request, "user/notification_history.html", {"logs": logs})


# ======================================================
# 通知既読化処理
# ======================================================
@login_required
def mark_notification_read(request, pk):
    """通知を既読にする"""
    try:
        notif = NotificationEvent.objects.get(pk=pk, user=request.user)
        notif.is_sent = True
        notif.save()
        messages.success(request, "通知を既読にしました。")
    except NotificationEvent.DoesNotExist:
        messages.error(request, "指定された通知が存在しません。")

    return redirect("main:notification_history")
# --- END: main/views_dashboard.py ---
