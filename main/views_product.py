# 実行ディレクトリ: I:\school\kaidoki-desse\main\views_product.py
from django.http import HttpResponse, JsonResponse
from main.forms import ProductForm
from django.shortcuts import render, redirect
import requests
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from main.models import Product, Category, PriceHistory
from .forms import ProductForm
from main.utils.error_logger import log_error
from main.constants import SORT_OPTIONS as sort_options

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
        tags.append(("key   word", f"キーワード: {keyword}"))

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
# ▼ 商品関連ビュー（最終整合版）
# =====================================================


# =====================================================
# 商品一覧
# =====================================================
def product_list(request):
    """商品一覧ページ"""
    try:
        # --- 一括削除処理 ---
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

        # --- カテゴリ取得 ---
        global_categories = Category.objects.filter(is_global=True)
        user_categories = Category.objects.filter(is_global=False, user=user)
        all_categories = list(global_categories) + list(user_categories)

        # --- 検索・絞り込み条件 ---
        keyword = request.GET.get("keyword", "").strip()
        selected_cats = _selected_category_ids(request)
        stock = request.GET.get("stock", "all")
        priority = request.GET.get("priority", "all")
        sort = request.GET.get("sort", "")
        buy_flag = request.GET.get("buy_flag")

        # --- ソートオプション ---
        sort_options = [
            ("new", "新しい順"),
            ("old", "古い順"),
            ("cheap", "安い順"),
            ("expensive", "高い順"),
        ]

        # --- 商品クエリ構築 ---
        qs = Product.objects.filter(
            user=user) if user else Product.objects.none()

        if keyword:
            qs = qs.filter(
                Q(product_name__icontains=keyword) | Q(
                    shop_name__icontains=keyword)
            )

        if selected_cats:
            qs = qs.filter(categories__id__in=selected_cats).distinct()

        if stock == "low":
            qs = qs.filter(is_in_stock=True, latest_stock_count__lte=3)
        elif stock == "none":
            qs = qs.filter(is_in_stock=False)

        if priority in ("高", "普通"):
            qs = qs.filter(priority=priority)

        if buy_flag == "1":
            qs = qs.filter(flag_reached=True)

        # --- 並び替え ---
        order_map = {
            "cheap": "initial_price",
            "expensive": "-initial_price",
            "old": "created_at",
            "new": "-created_at",
        }
        qs = qs.order_by(order_map.get(sort, "-created_at"))

        # --- ページネーション ---
        paginator = Paginator(qs, 12)
        page_obj = paginator.get_page(request.GET.get("page"))

        # --- フィルタ状態 ---
        filter_tags = _build_filter_tags(
            keyword, selected_cats, stock, priority, sort, all_categories)
        if buy_flag == "1":
            filter_tags.append(("buy_flag", "買い時のみ"))

        is_filtered = _has_filter(
            keyword, selected_cats, stock, priority, sort) or (buy_flag == "1")

        # --- 出力 ---
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
            "sort_options": sort_options,
            "filter_tags": filter_tags,
            "is_filtered": is_filtered,
            "buy_flag": buy_flag,
        })

    except Exception as e:
        log_error(user=request.user if request.user.is_authenticated else None,
                  type_name=type(e).__name__, source="product_list", err=e)
        return render(request, "main/error_generic.html", {"error": e})


# =====================================================
# 商品詳細
# =====================================================
@login_required
def product_detail(request, pk):
    """商品詳細ページ"""
    try:
        product = get_object_or_404(Product, pk=pk, user=request.user)

        # --- 在庫通知トグル ---
        if request.method == "POST" and "toggle_restock_notify" in request.POST:
            product.restock_notify_enabled = not product.restock_notify_enabled
            product.save(update_fields=["restock_notify_enabled"])
            status = "有効" if product.restock_notify_enabled else "無効"
            messages.success(request, f"在庫復活通知を{status}にしました。")
            return redirect("main:product_detail", pk=pk)

        # --- 買い時価格更新 ---
        if request.method == "POST" and "save_threshold" in request.POST:
            form = ProductForm(
                request.POST, instance=product, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "買い時価格を更新しました。")
                return redirect("main:product_detail", pk=pk)
        else:
            form = ProductForm(instance=product, user=request.user)

        # --- 履歴データ生成 ---
        history = product.pricehistory_set.all().order_by("checked_at")
        price_data = [{"date": h.checked_at.strftime("%Y-%m-%d"),
                       "price": float(h.price),
                       "stock": h.stock_count or 0} for h in history]

        # --- 買い時判定 ---
        is_kaidoki = bool(
            price_data and product.threshold_price and price_data[-1]["price"] <= float(product.threshold_price))

        return render(request, "main/product_detail.html", {
            "product": product,
            "form": form,
            "price_data_json": json.dumps(price_data, ensure_ascii=False),
            "has_history": bool(price_data),
            "is_kaidoki": is_kaidoki,
        })

    except Exception as e:
        log_error(user=request.user, type_name=type(
            e).__name__, source="product_detail", err=e)
        return render(request, "main/error_generic.html", {"error": e})


# =====================================================
# 商品登録
# =====================================================
@login_required
def product_create(request):
    """商品登録ページ"""
    try:
        if request.method == "POST":
            form = ProductForm(request.POST, user=request.user)
            if form.is_valid():
                product = form.save(commit=False)
                product.user = request.user
                if product.flag_type == "buy_price":
                    product.threshold_price = product.flag_value
                product.save()
                form.save_m2m()

                # 登録時に初回履歴を追加
                PriceHistory.objects.create(
                    product=product,
                    price=product.initial_price or product.regular_price or 0,
                    stock_count=product.latest_stock_count or 0,
                )
                messages.success(request, f"「{product.product_name}」を登録しました。")
                return redirect("main:product_list")
        else:
            form = ProductForm(user=request.user)

        percent_list = [i for i in range(5, 55, 5)]

        return render(request, "main/product_form.html", {
            "form": form,
            "is_edit": False,
            "percent_list": percent_list,
        })

    except Exception as e:
        log_error(user=request.user, type_name=type(
            e).__name__, source="product_create", err=e)
        return render(request, "main/error_generic.html", {"error": e})


# =====================================================
# 商品編集
# =====================================================
@login_required
def product_edit(request, pk):
    """商品編集ページ"""
    try:
        product = get_object_or_404(Product, pk=pk, user=request.user)
        if request.method == "POST":
            form = ProductForm(
                request.POST, instance=product, user=request.user)
            if form.is_valid():
                updated = form.save(commit=False)
                if updated.flag_type == "buy_price":
                    updated.threshold_price = updated.flag_value
                updated.save()
                form.save_m2m()

                # 履歴追加
                PriceHistory.objects.create(
                    product=updated,
                    price=updated.initial_price or updated.regular_price or 0,
                    stock_count=updated.latest_stock_count or 0,
                )
                messages.success(request, f"「{updated.product_name}」を更新しました。")
                return redirect("main:product_detail", pk=updated.pk)
        else:
            form = ProductForm(instance=product, user=request.user)

        percent_list = [i for i in range(5, 55, 5)]

        return render(request, "main/product_form.html", {
            "form": form,
            "is_edit": True,
            "product": product,
            "percent_list": percent_list,
        })

    except Exception as e:
        log_error(user=request.user, type_name=type(
            e).__name__, source="product_edit", err=e)
        return render(request, "main/error_generic.html", {"error": e})


# =====================================================
# 商品削除
# =====================================================
@login_required
def product_delete(request, pk):
    """商品削除"""
    try:
        product = get_object_or_404(Product, pk=pk, user=request.user)
        if request.method == "POST":
            product.delete()
            messages.success(request, f"「{product.product_name}」を削除しました。")
            return redirect("main:product_list")

        return render(request, "main/product_confirm_delete.html", {"product": product})

    except Exception as e:
        log_error(user=request.user, type_name=type(
            e).__name__, source="product_delete", err=e)
        return render(request, "main/error_generic.html", {"error": e})

# =====================================================
# 商品詳細（最終整合版）
# =====================================================


@login_required
def product_detail(request, pk):
    """商品詳細ページ"""
    user = request.user if request.user.is_authenticated else None
    try:
        product = get_object_or_404(Product, pk=pk, user=user)

        # =============================
        # ✅ POST処理分岐
        # =============================
        if request.method == "POST":
            # --- 在庫復活通知トグル ---
            if "toggle_restock_notify" in request.POST:
                product.restock_notify_enabled = not product.restock_notify_enabled
                product.save(update_fields=["restock_notify_enabled"])
                status = "有効" if product.restock_notify_enabled else "無効"
                messages.success(request, f"在庫復活通知を{status}にしました。")
                return redirect("main:product_detail", pk=pk)

            # --- 買い時価格更新 ---
            elif "save_threshold" in request.POST:
                form = ProductForm(request.POST, instance=product, user=user)
                if form.is_valid():
                    form.save()

                    # ✅ 履歴登録（価格変動があった場合）
                    PriceHistory.objects.create(
                        product=product,
                        price=product.regular_price or product.initial_price or 0,
                        stock_count=product.latest_stock_count or 0,
                    )

                    messages.success(request, "買い時価格を更新しました。")
                    return redirect("main:product_detail", pk=pk)
                else:
                    messages.error(request, "入力内容に誤りがあります。")
            else:
                messages.warning(request, "無効な操作です。")
                return redirect("main:product_detail", pk=pk)
        else:
            form = ProductForm(instance=product, user=user)

        # =============================
        # ✅ 履歴データ取得・グラフ整形
        # =============================
        history = product.pricehistory_set.all().order_by("checked_at")
        price_data = [
            {"date": h.checked_at.strftime("%Y-%m-%d"),
             "price": float(h.price),
             "stock": h.stock_count or 0}
            for h in history
        ]

        # ✅ 買い時判定
        is_kaidoki = (
            bool(price_data)
            and product.threshold_price
            and price_data[-1]["price"] <= float(product.threshold_price)
        )

        # =============================
        # ✅ レンダリング
        # =============================
        return render(request, "main/product_detail.html", {
            "product": product,
            "form": form,
            "price_data_json": json.dumps(price_data, ensure_ascii=False),
            "has_history": bool(price_data),
            "is_kaidoki": is_kaidoki,
        })

    except Exception as e:
        log_error(user=user, type_name=type(e).__name__,
                  source="product_detail", err=e)
        return render(request, "main/error_generic.html", {"error": e})


# =====================================================
# ▼ 楽天API関連ビュー
# =====================================================

def fetch_rakuten_item(request):
    """
    楽天商品URLからAPI経由で商品情報を取得
    例: /api/fetch_rakuten_item/?url=https://item.rakuten.co.jp/shopname/itemcode/
    """
    item_url = request.GET.get("url")
    if not item_url:
        return JsonResponse({"error": "urlパラメータが指定されていません。"}, status=400)

    try:
        # --- URL形式チェック ---
        if "rakuten.co.jp" not in item_url:
            return JsonResponse({"error": "楽天市場の商品URLを指定してください。"}, status=400)

        # --- URL正規化 ---
        clean_url = item_url.split("?")[0].rstrip("/")
        parts = clean_url.replace("https://item.rakuten.co.jp/", "").split("/")
        if len(parts) < 2:
            return JsonResponse({"error": "商品URLの形式が不正です。"}, status=400)

        shop_code, item_code = parts[0], parts[1]
        base_url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"

        # --- itemCode検索 ---
        params_item = {
            "applicationId": settings.RAKUTEN_APP_ID,
            "itemCode": f"{shop_code}:{item_code}",
            "format": "json",
            "hits": 1,
        }
        res = requests.get(base_url, params=params_item, timeout=10)
        data = res.json()

        # --- keyword検索 fallback ---
        if res.status_code != 200 or not data.get("Items"):
            params_keyword = {
                "applicationId": settings.RAKUTEN_APP_ID,
                "keyword": item_code,
                "format": "json",
                "hits": 1,
            }
            res = requests.get(base_url, params=params_keyword, timeout=10)
            data = res.json()

        if not data.get("Items"):
            return JsonResponse({"error": "楽天APIで商品情報を取得できませんでした。"}, status=404)

        item = data["Items"][0]["Item"]

        # --- 画像URL整形 ---
        if item.get("mediumImageUrls"):
            raw_url = item["mediumImageUrls"][0]["imageUrl"]
            # すでに _ex パラメータがある場合はそのまま利用
            if "_ex=" in raw_url:
                image_url = raw_url
            else:
                # クエリを削除し、?ではなく&_ex=を安全に追加
                if "?" in raw_url:
                    image_url = raw_url.split("?")[0] + "&_ex=300x300"
                else:
                    image_url = raw_url + "?_ex=300x300"
        else:
            image_url = "/static/images/no_image.png"

        # --- 価格を数値化 ---
        try:
            price = int(item.get("itemPrice", 0))
        except (ValueError, TypeError):
            price = 0

        # --- JSON出力（日本語をそのまま表示） ---
        json_data = json.dumps({
            "product_name": item.get("itemName", ""),
            "shop_name": item.get("shopName", ""),
            "regular_price": price,
            "initial_price": price,
            "image_url": image_url,
            "url": item_url,
        }, ensure_ascii=False)

        return HttpResponse(json_data, content_type="application/json; charset=utf-8")

    except requests.exceptions.RequestException as e:
        log_error(None, "RequestException", "fetch_rakuten_item", e)
        return JsonResponse({"error": f"外部API通信エラー: {e}"}, status=500)

    except Exception as e:
        log_error(None, type(e).__name__, "fetch_rakuten_item", e)
        return JsonResponse({"error": f"サーバー内部エラー: {e}"}, status=500)
