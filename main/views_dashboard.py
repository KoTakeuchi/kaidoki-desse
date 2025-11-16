# --- START: main/views_dashboard.py ---
import random
from main.models import NotificationEvent, Product
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import Product, PriceHistory, NotificationEvent, UserNotificationSetting


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
        .order_by("-occurred_at")[:5]
    )

    # --- 通知未送信・送信済み数 ---
    unread_count = NotificationEvent.objects.filter(
        user=user, is_read=False
    ).count()

    sent_count = NotificationEvent.objects.filter(
        user=user, is_read=True
    ).count()

    # --- 最近1週間の価格履歴更新件数 ---
    one_week_ago = timezone.now() - timedelta(days=7)
    price_updates = (
        PriceHistory.objects.filter(
            product__user=user, checked_at__gte=one_week_ago
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
    """通知履歴ページ（優先度「高」の商品のみ）"""
    user = request.user

    # ユーザーの通知設定を取得
    try:
        setting = UserNotificationSetting.objects.get(user=user)
    except UserNotificationSetting.DoesNotExist:
        setting = None

    # ✅ 基本クエリ：未読 + 優先度「高」のみ
    logs = NotificationEvent.objects.filter(
        user=user,
        is_read=False,
        product__priority="高"  # ✅ 優先度「高」のみ
    )

    # ✅ アプリ内通知がOFFの場合は空にする
    if setting and not setting.app_notification_enabled:
        logs = logs.none()

    # ✅ 通知のまとめ方：商品ごとに最新の通知のみ（買い時通知と在庫通知は区別）
    from django.db.models import OuterRef, Subquery, Q

    # 買い時通知の最新
    latest_buy_time = NotificationEvent.objects.filter(
        product=OuterRef('product'),
        event_type__in=["threshold_hit", "discount_over", "lowest_price"],
        is_read=False
    ).order_by('-occurred_at').values('id')[:1]

    # 在庫通知の最新
    latest_stock = NotificationEvent.objects.filter(
        product=OuterRef('product'),
        event_type__in=["stock_restore", "stock_few"],
        is_read=False
    ).order_by('-occurred_at').values('id')[:1]

    # 最新の通知のみを取得
    logs = logs.filter(
        Q(id__in=Subquery(latest_buy_time)) | Q(id__in=Subquery(latest_stock))
    ).order_by("-occurred_at")

    products = Product.objects.filter(user=user)

    return render(request, "main/notifications.html", {
        "logs": logs,
        "products": products,
        "setting": setting,
    })
# ======================================================
# 通知既読化処理
# ======================================================


@login_required
def mark_notification_read(request, pk):
    """通知を既読にする"""
    try:
        notif = NotificationEvent.objects.get(pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        messages.success(request, "通知を既読にしました。")
    except NotificationEvent.DoesNotExist:
        messages.error(request, "指定された通知が存在しません。")

    return redirect("main:notification_history")


@login_required
def notification_redirect(request, pk):
    """
    通知クリック時：
    - 既読フラグをTrueに変更（削除はしない）
    - ユーザー画面では既読通知を非表示
    - 関連商品詳細へ遷移（なければランダム遷移）
    """
    try:
        notif = get_object_or_404(NotificationEvent, pk=pk, user=request.user)

        # ✅ 削除ではなく既読化
        if not notif.is_read:
            notif.is_read = True
            notif.save(update_fields=["is_read"])

        # ✅ ユーザー側では既読を一覧に表示しないようにするため、
        #     notifications.html 側で「{% if not n.is_read %}」条件を使う
        product = notif.product or Product.objects.filter(
            user=request.user).order_by("?").first()

        if product:
            return redirect("main:product_detail", pk=product.id)
        else:
            return redirect("main:notifications")

    except NotificationEvent.DoesNotExist:
        messages.warning(request, "指定された通知は存在しません。")
        return redirect("main:notifications")


@login_required
def unread_notification_count(request):
    """未読通知件数を返すAPI"""
    count = NotificationEvent.objects.filter(
        user=request.user, is_read=False).count()
    return JsonResponse({"unread_count": count})


# 一括既読APIを追加する関数

@login_required
def mark_all_read_api(request):
    """一括既読API"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        notification_ids = data.get('notification_ids', [])

        NotificationEvent.objects.filter(
            id__in=notification_ids,
            user=request.user
        ).update(is_read=True)

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)
