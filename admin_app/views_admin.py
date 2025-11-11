# =============================
#  Import
# =============================
from django.shortcuts import render
# ← NotificationLogではなくNotificationEvent
from main.models import Product, NotificationEvent, ErrorLog, User, Category
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from admin_app.models import CommonCategory, NotificationLog
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Prefetch, Count, Q
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from datetime import timedelta
from main.utils.pagination_helper import paginate_queryset
from django.core.paginator import Paginator
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
    """管理者ダッシュボード"""
    from main.models import Product, User, NotificationEvent, ErrorLog
    from django.utils import timezone

    # ---- 統計情報 ----
    stats = {
        "user_count": User.objects.count(),
        "product_count": Product.objects.count(),
        "notification_week": NotificationEvent.objects.filter(
            occurred_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count(),
        "error_count": ErrorLog.objects.count(),
    }

    # ---- 最新の通知（5件）----
    latest_notifications = (
        NotificationEvent.objects
        .select_related("user", "product")
        .order_by("-occurred_at")[:5]
    )

    # ---- 最新のエラー（5件）----
    latest_errors = (
        ErrorLog.objects
        .select_related("user")
        .order_by("-created_at")[:5]
    )

    context = {
        "stats": stats,
        "latest_notifications": latest_notifications,
        "latest_errors": latest_errors,
    }
    return render(request, "admin_app/admin_dashboard.html", context)


# =============================
#  ユーザー管理
# =============================

@user_passes_test(is_admin)
def admin_user_list(request):
    """全ユーザー一覧（検索＋絞り込み＋ページネーション＋ログイン情報付き）"""
    query = request.GET.get("q", "").strip()
    role = request.GET.get("role", "")
    is_active = request.GET.get("is_active", "")
    date_field = request.GET.get(
        "date_field", "date_joined")  # 基準項目（登録日 or 最終ログイン）
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    # ✅ 商品数・プロフィール情報付きで取得
    users = (
        User.objects
        .annotate(product_count=Count("products"))
        .select_related("profile")  # UserProfile（login_count）JOIN
        .order_by("id")
    )

    # 🔍 キーワード検索
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

    # 👤 権限フィルタ
    if role == "staff":
        users = users.filter(is_staff=True)
    elif role == "user":
        users = users.filter(is_staff=False)

    # ⚙ 状態フィルタ
    if is_active == "true":
        users = users.filter(is_active=True)
    elif is_active == "false":
        users = users.filter(is_active=False)

    # 📅 日付範囲（登録日 or 最終ログインで切替）
    if start_date:
        users = users.filter(**{f"{date_field}__date__gte": start_date})
    if end_date:
        users = users.filter(**{f"{date_field}__date__lte": end_date})

    # ✅ ページネーション
    page_obj, paginator = paginate_queryset(request, users, per_page=20)

    context = {
        "users": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "query": query,
        "role": role,
        "is_active": is_active,
        "date_field": date_field,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "admin_app/admin_user_list.html", context)


def admin_user_detail_modal(request, user_id):
    """ユーザー詳細モーダル用"""
    user = get_object_or_404(User, id=user_id)

    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email or "-",
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "last_login": user.last_login.strftime("%Y/%m/%d %H:%M") if user.last_login else "-",
        "date_joined": user.date_joined.strftime("%Y/%m/%d") if user.date_joined else "-",
        "product_count": user.products.filter(is_deleted=False).count(),
        "login_count": getattr(user, "login_count", 0),
    }
    return JsonResponse(data)


# =============================
#  商品管理
# =============================
@user_passes_test(is_admin)
def admin_product_list(request):
    """全ユーザーの商品一覧 + 絞り込み検索 + ページネーション"""
    query = request.GET.get("q", "").strip()
    flag_type = request.GET.get("flag_type", "").strip()
    priority = request.GET.get("priority", "").strip()
    is_deleted = request.GET.get("is_deleted", "").strip()
    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()

    # ✅ 論理削除を含めて取得
    products = (
        Product.objects.all_with_deleted()
        .select_related("user")
        .prefetch_related("categories")
        .order_by("-created_at")
    )

    # 🔍 キーワード検索
    if query:
        products = products.filter(
            Q(product_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(categories__category_name__icontains=query)
        ).distinct()

    # 🟩 状態フィルタ
    if is_deleted == "true":
        products = products.filter(is_deleted=True)
    elif is_deleted == "false":
        products = products.filter(is_deleted=False)

    # 🟦 通知条件フィルタ
    if flag_type:
        products = products.filter(flag_type=flag_type)

    # 🟧 優先度フィルタ
    if priority:
        products = products.filter(priority=priority)

    # 📅 登録日フィルタ
    if start_date:
        products = products.filter(created_at__date__gte=start_date)
    if end_date:
        products = products.filter(created_at__date__lte=end_date)

    # ✅ ページネーション
    page_obj, paginator = paginate_queryset(request, products, per_page=20)

    context = {
        "products": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "query": query,
        "flag_type": flag_type,
        "priority": priority,
        "is_deleted": is_deleted,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "admin_app/admin_product_list.html", context)


# =============================
#  カテゴリ管理
# =============================

def is_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_admin)
def admin_category(request):
    """
    共通カテゴリ管理（追加・編集・削除）
    ステータス / 登録ユーザー数 / 登録商品数は、
    Product.categories の category_name と CommonCategory.category_name を
    名前一致で集計して表示する。
    """
    from main.models import Product
    from django.db.models import Count

    # 共通カテゴリ一覧
    categories = CommonCategory.objects.all().order_by("id")

    # ✅ 各共通カテゴリごとに「全ユーザーの商品」を集計
    for cat in categories:
        # 共通カテゴリ名と同じ名前を持つユーザーカテゴリに紐づく商品
        qs = Product.objects.filter(
            categories__category_name=cat.category_name,
            is_deleted=False,
        )

        # 登録商品数（重複なし）
        cat.product_count = qs.distinct().count()
        # 登録ユーザー数（商品を登録しているユニークユーザー数）
        cat.user_count = qs.values("user").distinct().count()

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
                    updated_by=request.user,
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

    return render(
        request,
        "admin_app/admin_categories.html",
        {"common_categories": categories},
    )


# =============================
#  通知ログ管理
# =============================

# 実行ディレクトリ: I:\school\kaidoki-desse\admin_app\views_admin.py

@user_passes_test(is_admin)
def admin_notification_list(request):
    """通知ログ一覧 + キーワード・日付・通知条件検索 + ページネーション"""
    query = request.GET.get("q", "").strip()
    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()
    method = request.GET.get("method", "").strip()
    ntype = request.GET.get("type", "").strip()

    logs = NotificationEvent.objects.select_related(
        "user", "product"
    ).order_by("-occurred_at")

    # 🔍 キーワード検索
    if query:
        logs = logs.filter(
            Q(user__username__icontains=query)
            | Q(product__product_name__icontains=query)
            | Q(message__icontains=query)
        )

    # 📨 通知方法フィルタ
    if method == "email":
        logs = logs.filter(event_type__startswith="mail_")  # メール通知
    elif method == "app":
        logs = logs.exclude(event_type__startswith="mail_")  # アプリ通知

    # 🔔 通知種別フィルタ（日本語→内部キー変換対応）
    if ntype:
        type_map = {
            "買い時お知らせ": "mail_buy_timing",
            "在庫お知らせ": "mail_stock",
            "買い時価格": "threshold_hit",
            "割引率": "discount_over",
            "最安値": "lowest_price",
            "在庫少": "stock_few",
            "在庫復活": "stock_restore",
        }
        ntype_key = type_map.get(ntype, ntype)
        logs = logs.filter(event_type=ntype_key)

    # 📅 日付フィルタ
    if start_date:
        logs = logs.filter(occurred_at__date__gte=start_date)
    if end_date:
        logs = logs.filter(occurred_at__date__lte=end_date)

    # ✅ 通知方法属性を一時付与（テンプレート用）
    for log in logs:
        log.method = "email" if log.event_type.startswith("mail_") else "app"

    # ✅ ページネーション
    per_page = int(request.GET.get("per_page", 20))
    page_obj, paginator = paginate_queryset(request, logs, per_page=per_page)

    # プルダウン候補（テンプレート用）
    type_list = [
        "mail_buy_timing",
        "mail_stock",
        "threshold_hit",
        "discount_over",
        "lowest_price",
        "stock_few",
        "stock_restore",
    ]

    context = {
        "logs": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "query": query,
        "start_date": start_date,
        "end_date": end_date,
        "method": method,
        "type": ntype,
        "type_list": type_list,
    }

    return render(request, "admin_app/admin_notifications.html", context)


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
    from .models import ErrorLog

    logs = ErrorLog.objects.all()

    query = request.GET.get("q", "")
    status = request.GET.get("status", "")
    type_name = request.GET.get("type_name", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    if query:
        logs = logs.filter(
            Q(user__username__icontains=query)
            | Q(source__icontains=query)
            | Q(message__icontains=query)
        )
    if status:
        logs = logs.filter(status=status)
    if type_name:
        logs = logs.filter(type_name=type_name)
    if start_date:
        logs = logs.filter(created_at__date__gte=start_date)
    if end_date:
        logs = logs.filter(created_at__date__lte=end_date)

    # エラー種別リストを distinct で抽出
    type_list = ErrorLog.objects.values_list(
        "type_name", flat=True).distinct().order_by("type_name")

    # ページネーション
    per_page = int(request.GET.get("per_page", 20))
    paginator = Paginator(logs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "admin_app/admin_error_logs.html",  # ← ここを修正
        {
            "logs": page_obj,
            "paginator": paginator,
            "page_obj": page_obj,
            "query": query,
            "status": status,
            "type_name": type_name,
            "start_date": start_date,
            "end_date": end_date,
            "type_list": type_list,
        },
    )


User = get_user_model()


@user_passes_test(is_admin)
def update_error_status(request, log_id):
    """エラーログの対応ステータス・対応者・メモ更新"""
    if request.method == "POST":
        log = get_object_or_404(ErrorLog, pk=log_id)
        new_status = request.POST.get("status")
        note = request.POST.get("note", "").strip()
        handled_by_id = request.POST.get("handled_by")

        if new_status in ["unresolved", "in_progress", "resolved"]:
            log.status = new_status
            log.note = note or log.note
            if handled_by_id:
                try:
                    admin_user = User.objects.get(
                        id=handled_by_id, is_staff=True)
                    log.handled_by = admin_user
                except User.DoesNotExist:
                    pass
            log.save(update_fields=["status", "note", "handled_by"])
            messages.success(request, f"エラーID {log.id} の対応状況を更新しました。")

    return redirect("admin_app:admin_error_logs")


User = get_user_model()


def is_admin(user):
    return user.is_staff  # 既に定義済みならそれを使う


@user_passes_test(is_admin)
def admin_error_detail(request, log_id):
    """エラーログ詳細 + 対応編集フォーム"""
    log = get_object_or_404(ErrorLog, pk=log_id)

    # スタッフ(管理者)だけを候補にする
    admin_users = User.objects.filter(is_staff=True).order_by("username")

    if request.method == "POST":
        # フォームから値を拾う
        status = request.POST.get("status") or "unresolved"
        handled_by_id = request.POST.get("handled_by") or None
        note = (request.POST.get("note") or "").strip()

        log.status = status
        log.note = note

        if handled_by_id:
            try:
                log.handled_by = User.objects.get(pk=handled_by_id)
            except User.DoesNotExist:
                log.handled_by = None
        else:
            log.handled_by = None

        log.save(update_fields=["status", "note", "handled_by"])

        messages.success(request, "エラー対応情報を更新しました。")

        return redirect("admin_app:admin_error_logs")

    context = {
        "log": log,
        "admin_users": admin_users,
    }
    return render(request, "admin_app/admin_error_detail.html", context)
