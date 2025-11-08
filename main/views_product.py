# --- START(1/2): main/views_product.py ---
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
import json

from main.forms import ProductForm, ThresholdPriceForm
from main.models import Product, Category, PriceHistory
from main.utils.error_logger import log_error


# ======================================================
# 内部共通関数
# ======================================================
def _selected_category_ids(request: HttpRequest):
    """GETパラメータからカテゴリIDリストを取得"""
    return request.GET.getlist("cat")


def _has_filter(keyword, selected_cats, stock, priority, sort):
    """フィルタが1つでも設定されているかを判定"""
    return any([
        keyword,
        selected_cats,
        stock != "all",
        priority != "all",
        sort != "new",
    ])


# ======================================================
# 商品一覧
# ======================================================
@login_required
def product_list(request: HttpRequest) -> HttpResponse:
    """商品一覧ページ"""
    try:
        user = request.user

        # 一括削除処理
        if request.method == "POST" and request.POST.get("bulk_action") == "delete":
            ids = request.POST.getlist("selected")
            if ids:
                Product.objects.filter(id__in=ids, user=user).delete()
            return redirect("main:product_list")

        # 絞り込みパラメータ取得
        keyword = request.GET.get("keyword", "").strip()
        selected_cats = request.GET.getlist("cat")
        stock = request.GET.get("stock", "all")
        priority = request.GET.get("priority", "all")
        sort = request.GET.get("sort", "new")

        # ベースクエリ
        qs = Product.objects.filter(user=user).prefetch_related(
            Prefetch("categories", queryset=Category.objects.all().order_by("id"))
        )

        if keyword:
            qs = qs.filter(Q(product_name__icontains=keyword)
                           | Q(shop_name__icontains=keyword))

        if selected_cats:
            try:
                ids = [int(c) for c in selected_cats]
                qs = qs.filter(categories__id__in=ids).distinct()
            except ValueError:
                pass

        if stock == "low":
            qs = qs.filter(latest_stock_count__lte=3, latest_stock_count__gt=0)
        elif stock == "none":
            qs = qs.filter(is_in_stock=False)

        if priority in ["高", "普通"]:
            qs = qs.filter(priority=priority)

        if sort == "cheap":
            qs = qs.order_by("threshold_price")
        elif sort == "expensive":
            qs = qs.order_by("-threshold_price")
        elif sort == "old":
            qs = qs.order_by("created_at")
        else:
            qs = qs.order_by("-created_at")

        paginator = Paginator(qs, 20)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        global_categories = Category.objects.filter(
            is_global=True, user__isnull=True)
        user_categories = Category.objects.filter(user=user, is_global=False)

        return render(
            request,
            "main/product_list.html",
            {
                "products": page_obj.object_list,
                "page_obj": page_obj,
                "paginator": paginator,
                "global_categories": global_categories,
                "user_categories": user_categories,
                "selected_cats": selected_cats,
                "keyword": keyword,
                "stock": stock,
                "priority": priority,
                "sort": sort,
                "is_filtered": _has_filter(keyword, selected_cats, stock, priority, sort),
            },
        )
    except Exception as e:
        log_error(user=request.user, type_name=type(
            e).__name__, source="product_list", err=e)
        raise
# --- END(1/2): main/views_product.py ---
