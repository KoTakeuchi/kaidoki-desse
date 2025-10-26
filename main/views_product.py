# 実行ディレクトリ: I:\school\kaidoki-desse\main\views_product.py
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.conf import settings

from main.models import Product, Category
from .forms import ProductForm
from main.utils.error_logger import log_error


# =====================================================
# ▼ 内部共通関数群
# =====================================================
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


# =====================================================
# ▼ 商品関連ビュー
# =====================================================
def product_list(request):
    """商品一覧ページ"""
    try:
        if request.method == "POST":
            if request.POST.get("bulk_action") == "delete":
                ids = request.POST.getlist("selected")
                if ids:
                    Product.objects.filter(id__in=ids).delete()
                redirect_url = request.get_full_path().split("?")[0]
                query_str = request.META.get("QUERY_STRING", "")
                return redirect(f"{redirect_url}?{query_str}" if query_str else redirect_url)
            return redirect("main:product_list")

        user = request.user if request.user.is_authenticated else None

        global_categories = Category.objects.filter(is_global=True)
        user_categories = Category.objects.filter(is_global=False, user=user)
        all_categories = list(global_categories) + list(user_categories)

        keyword = request.GET.get("keyword", "").strip()
        selected_cats = _selected_category_ids(request)
        stock = request.GET.get("stock", "all")
        priority = request.GET.get("priority", "all")
        sort = request.GET.get("sort", "")

        qs = Product.objects.all()

        if keyword:
            qs = qs.filter(Q(product_name__icontains=keyword)
                           | Q(shop_name__icontains=keyword))
        if selected_cats:
            qs = qs.filter(category_id__in=selected_cats)
        if stock == "low":
            qs = qs.filter(is_in_stock=True, latest_stock_count__lte=3)
        elif stock == "none":
            qs = qs.filter(is_in_stock=False)
        if priority in ("高", "普通"):
            qs = qs.filter(priority=priority)

        if sort == "cheap":
            qs = qs.order_by("initial_price")
        elif sort == "expensive":
            qs = qs.order_by("-initial_price")
        elif sort == "old":
            qs = qs.order_by("created_at")
        else:
            qs = qs.order_by("-created_at")

        paginator = Paginator(qs, 12)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        filter_tags = _build_filter_tags(
            keyword, selected_cats, stock, priority, sort, all_categories)
        is_filtered = _has_filter(
            keyword, selected_cats, stock, priority, sort)

        return render(request, "main/product_list.html", {
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
        })

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


# =====================================================
# ▼ 楽天API関連
# =====================================================
def fetch_rakuten_data(item_url: str):
    """楽天APIから商品情報を取得"""
    try:
        if "rakuten.co.jp" not in item_url:
            return {"error": "楽天の商品URLを入力してください。"}

        # ✅ URL正規化処理
        clean_url = item_url.split("?")[0].rstrip("/")
        parts = clean_url.replace("https://item.rakuten.co.jp/", "").split("/")
        if len(parts) < 2:
            return {"error": "商品URLの形式が不正です。"}

        shop_code, item_code = parts[0], parts[1]
        base_url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"

        # --- ① itemCode検索 ---
        params_item = {
            "applicationId": settings.RAKUTEN_APP_ID,
            "itemCode": f"{shop_code}:{item_code}",
            "format": "json",
            "hits": 1,
        }
        print("[RakutenAPI] Try itemCode:", params_item)
        res = requests.get(base_url, params=params_item)
        data = res.json()

        # --- ② keyword検索（①で見つからなかった場合） ---
        if res.status_code != 200 or not data.get("Items"):
            print("[RakutenAPI] Fallback → keyword search")
            params_keyword = {
                "applicationId": settings.RAKUTEN_APP_ID,
                "keyword": item_code,
                "format": "json",
                "hits": 1,
            }
            res = requests.get(base_url, params=params_keyword)
            data = res.json()

        if not data.get("Items"):
            print("[RakutenAPI] No items found")
            return {"error": "楽天APIで商品情報を取得できませんでした。"}

        item = data["Items"][0]["Item"]
        print("[RakutenAPI] Success:", item.get("itemName"))

        return {
            "product_name": item.get("itemName", ""),
            "shop_name": item.get("shopName", ""),
            "regular_price": item.get("itemPrice", ""),
            "initial_price": item.get("itemPrice", ""),
            "image_url": item["mediumImageUrls"][0]["imageUrl"]
            if item.get("mediumImageUrls")
            else "/static/images/noimage.png",
        }

    except Exception as e:
        print("❌ fetch_rakuten_data Error:", e)
        return {"error": f"サーバー側で例外発生: {e}"}


def fetch_rakuten_item(request):
    """JSからのfetch用API"""
    item_url = request.GET.get("url", "").strip()
    print(f"[View] Fetching Rakuten item for URL: {item_url}")

    if not item_url:
        return JsonResponse({"error": "商品URLが指定されていません。"}, status=400)

    data = fetch_rakuten_data(item_url)
    if "error" in data:
        return JsonResponse(data, status=500)

    return JsonResponse(data)
