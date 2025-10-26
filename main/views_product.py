from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from main.models import Product, Category
from .forms import ProductForm
from main.utils.error_logger import log_error
from django.http import JsonResponse
from main.utils.rakuten_api import fetch_rakuten_item
from django.views.decorators.http import require_GET


def _selected_category_ids(request):
    """GETパラメータ 'cat' をリストで取得（絞り込み保持用）"""
    return request.GET.getlist("cat")


def _has_filter(keyword, selected_cats, stock, priority, sort):
    """絞り込み中かどうかを判定（クリアボタン制御用）"""
    return any([
        keyword,
        selected_cats,
        stock != "all",
        priority != "all",
        sort in ("cheap", "expensive", "new", "old"),
    ])


def _build_filter_tags(keyword, selected_cats, stock, priority, sort, all_categories):
    """画面上部に表示する条件タグを構築"""
    tags = []

    if keyword:
        tags.append(("keyword", f"キーワード: {keyword}"))

    # カテゴリ名を名前解決
    if selected_cats:
        id_to_name = {str(c.id): c.category_name for c in all_categories}
        names = [id_to_name.get(cid, f"ID:{cid}") for cid in selected_cats]
        if names:
            tags.append(("cat", "カテゴリ: " + "・".join(names)))

    if stock == "low":
        tags.append(("stock", "在庫: わずか"))
    elif stock == "none":
        tags.append(("stock", "在庫: なし"))

    if priority in ("高", "普通"):
        tags.append(("priority", f"優先度: {priority}"))

    if sort == "cheap":
        tags.append(("sort", "並び順: 安い順"))
    elif sort == "expensive":
        tags.append(("sort", "並び順: 高い順"))
    elif sort == "new":
        tags.append(("sort", "並び順: 新しい順"))
    elif sort == "old":
        tags.append(("sort", "並び順: 古い順"))

    return tags


def product_list(request):
    """
    商品一覧ページ
    - フィルタリング、並び替え、ページング、一括削除対応
    - モーダル確認後削除（POST）
    - ページング: 1ページ12件
    """
    try:
        # 🔹 一括削除処理（POST時）
        if request.method == "POST":
            if request.POST.get("bulk_action") == "delete":
                ids = request.POST.getlist("selected")
                if ids:
                    Product.objects.filter(id__in=ids).delete()
                # 削除後、現在のGETクエリ（sort等）を維持して再表示
                redirect_url = request.get_full_path().split("?")[0]
                query_str = request.META.get("QUERY_STRING", "")
                return redirect(f"{redirect_url}?{query_str}" if query_str else redirect_url)
            else:
                # 想定外のPOSTは一覧再表示
                return redirect("main:product_list")

        user = request.user if request.user.is_authenticated else None

        # 🔹 カテゴリ取得
        global_categories = Category.objects.filter(is_global=True)
        user_categories = Category.objects.filter(is_global=False, user=user)
        all_categories = list(global_categories) + list(user_categories)

        # 🔹 GETパラメータ取得
        keyword = request.GET.get("keyword", "").strip()
        selected_cats = _selected_category_ids(request)
        stock = request.GET.get("stock", "all")
        priority = request.GET.get("priority", "all")
        sort = request.GET.get("sort", "")

        # 🔹 クエリ構築
        qs = Product.objects.all()

        # キーワード検索（商品名・ショップ名）
        if keyword:
            qs = qs.filter(Q(product_name__icontains=keyword)
                           | Q(shop_name__icontains=keyword))

        # カテゴリ
        if selected_cats:
            qs = qs.filter(category_id__in=selected_cats)

        # 在庫条件
        if stock == "low":
            qs = qs.filter(is_in_stock=True, latest_stock_count__lte=3)
        elif stock == "none":
            qs = qs.filter(is_in_stock=False)

        # 優先度条件
        if priority in ("高", "普通"):
            qs = qs.filter(priority=priority)

        # 並び順（新しい順をデフォルト）
        if sort == "cheap":
            qs = qs.order_by("initial_price")
        elif sort == "expensive":
            qs = qs.order_by("-initial_price")
        elif sort == "new" or not sort:
            qs = qs.order_by("-created_at")
        elif sort == "old":
            qs = qs.order_by("created_at")
        else:
            qs = qs.order_by("-updated_at")

        # 🔹 ページング（12件）
        paginator = Paginator(qs, 12)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # 🔹 条件タグとクリアボタン表示制御
        filter_tags = _build_filter_tags(
            keyword, selected_cats, stock, priority, sort, all_categories)
        is_filtered = _has_filter(
            keyword, selected_cats, stock, priority, sort)

        # 🔹 コンテキスト
        context = {
            "products": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "global_categories": global_categories,
            "user_categories": user_categories,
            "keyword": keyword,
            "selected_cats": selected_cats,
            "stock": stock,
            "priority": priority,
            "sort": sort,
            "filter_tags": filter_tags,
            "is_filtered": is_filtered,
        }

        return render(request, "main/product_list.html", context)

    except Exception as e:
        user = request.user if request.user.is_authenticated else None
        log_error(user=user, type_name=type(e).__name__,
                  source="product_list", err=e)
        return render(request, "main/error_generic.html", {"error": e})


def product_detail(request, pk):
    """商品詳細"""
    try:
        product = get_object_or_404(Product, pk=pk)
        return render(request, "main/product_detail.html", {"product": product})
    except Exception as e:
        user = request.user if request.user.is_authenticated else None
        log_error(user=user, type_name=type(e).__name__,
                  source="product_detail", err=e)
        return render(request, "main/error_generic.html", {"error": e})


def product_create(request):
    """商品登録"""
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("main:product_list")
    else:
        form = ProductForm()
    return render(request, "main/product_form.html", {"form": form})


def product_edit(request, pk):
    """商品編集"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect("main:product_detail", pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, "main/product_form.html", {"form": form, "product": product})


def product_delete(request, pk):
    """個別削除"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        return redirect("main:product_list")
    return render(request, "main/product_confirm_delete.html", {"product": product})


@require_GET
def fetch_rakuten_info(request):
    """
    楽天商品URLから商品情報を取得するAPIエンドポイント
    例: /main/api/fetch_rakuten_item/?url=https://item.rakuten.co.jp/xxxx/
    """
    rakuten_url = request.GET.get("url")

    if not rakuten_url:
        return JsonResponse({"error": "URL parameter is missing."}, status=400)

    try:
        item_data = fetch_rakuten_item(rakuten_url)
        if not item_data:
            return JsonResponse({"error": "Failed to fetch item info."}, status=500)

        return JsonResponse(item_data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
