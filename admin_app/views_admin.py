# =============================
#  Import
# =============================
from admin_app.models import CommonCategory
from django.shortcuts import render, redirect, get_object_or_404
from main.models import Category, Product, ErrorLog, User, NotificationEvent
from django.db.models import Prefetch, Count, Q
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from datetime import timedelta


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
        "notification_week": NotificationEvent.objects.filter(
            occurred_at__gte=week_ago
        ).count(),
        "error_count": ErrorLog.objects.count(),
    }
    context = {
        "stats": stats,
        "latest_products": Product.objects.select_related("user").order_by("-created_at")[:5],
        "latest_notifications": NotificationEvent.objects.select_related("user").order_by("-occurred_at")[:5],
    }
    return render(request, "admin_app/admin_dashboard.html", context)


# =============================
#  ユーザー管理
# =============================

@user_passes_test(is_admin)
def admin_user_list(request):
    """全ユーザー一覧"""
    users = User.objects.annotate(product_count=Count("products"))
    return render(request, "admin_app/admin_user_list.html", {"users": users})


# =============================
#  商品管理
# =============================

@user_passes_test(is_admin)
def admin_product_list(request):
    """全ユーザーの商品一覧"""
    products = (
        Product.objects
        .select_related("user")
        .prefetch_related("categories")
        .order_by("-created_at")
    )
    return render(request, "admin_app/admin_product_list.html", {"products": products})


# =============================
#  カテゴリ管理
# =============================

def is_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_admin)
def admin_category(request):
    """
    共通カテゴリ管理（追加・編集・削除）
    """
    categories = CommonCategory.objects.all().order_by('id')

    if request.method == "POST":
        add_name = request.POST.get("add_name", "").strip()
        edit_id = request.POST.get("edit_id")
        new_name = request.POST.get("new_name", "").strip()
        delete_id = request.POST.get("delete_id")

        # ✅ 新規追加
        if add_name:
            if CommonCategory.objects.filter(category_name=add_name).exists():
                messages.warning(request, "同名のカテゴリが既に存在します。")
            else:
                CommonCategory.objects.create(
                    category_name=add_name,
                    updated_by=request.user
                )
                messages.success(request, f"カテゴリ「{add_name}」を追加しました。")
            return redirect("admin_app:admin_category")

        # ✅ 編集
        elif edit_id and new_name:
            try:
                cat = CommonCategory.objects.get(id=edit_id)
                cat.category_name = new_name
                cat.updated_by = request.user
                cat.save()
                messages.success(request, f"カテゴリ名を「{new_name}」に変更しました。")
            except CommonCategory.DoesNotExist:
                messages.error(request, "指定されたカテゴリが見つかりません。")
            return redirect("admin_app:admin_category")

        # ✅ 削除
        elif delete_id:
            try:
                cat = CommonCategory.objects.get(id=delete_id)
                name = cat.category_name
                cat.delete()
                messages.info(request, f"カテゴリ「{name}」を削除しました。")
            except CommonCategory.DoesNotExist:
                messages.error(request, "削除対象が見つかりません。")
            return redirect("admin_app:admin_category")

    return render(request, "admin_app/admin_categories.html", {
        "common_categories": categories
    })


# =============================
#  通知ログ管理
# =============================

@user_passes_test(is_admin)
def admin_notification_list(request):
    query = request.GET.get("q", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    logs = NotificationEvent.objects.select_related(
        "user", "product").order_by("-occurred_at")

    if query:
        logs = logs.filter(
            Q(user__username__icontains=query)
            | Q(product__product_name__icontains=query)
            | Q(message__icontains=query)
        )
    if start_date:
        logs = logs.filter(occurred_at__gte=start_date)
    if end_date:
        logs = logs.filter(occurred_at__lte=end_date)

    return render(request, "admin_app/admin_notifications.html", {
        "logs": logs,
        "query": query,
        "start_date": start_date,
        "end_date": end_date,
    })


@user_passes_test(is_admin)
def admin_notification_detail(request, log_id):
    """通知ログ詳細"""
    log = get_object_or_404(NotificationEvent, pk=log_id)
    return render(request, "admin_app/admin_notification_detail.html", {"log": log})


# =============================
#  エラーログ管理
# =============================

@user_passes_test(is_admin)
def admin_error_logs(request):
    """管理者用エラーログ一覧"""
    logs = ErrorLog.objects.all().order_by("-created_at")
    return render(request, "admin_app/admin_error_logs.html", {"logs": logs})
