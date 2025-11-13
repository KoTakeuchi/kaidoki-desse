# --- START: main/views_product.py ---
from .models import Product, PriceHistory
from django.utils import timezone
from django.http import JsonResponse
from main.models import Product, PriceHistory
from datetime import timedelta, datetime
from django.db.models import Min, Max, F
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from main.forms import ProductForm
from main.models import Product, Category, PriceHistory
from main.utils.error_logger import log_error
from main.utils.flag_checker import update_flag_status
import decimal
import json
from django.http import JsonResponse
from main.models import Product, PriceHistory


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
        sort != "newest",
    ])


# ======================================================
# 商品一覧
# ======================================================
@login_required
def product_list(request: HttpRequest) -> HttpResponse:
    """商品一覧ページ"""
    try:
        user = request.user

        # --- 一括削除処理 ---
        if request.method == "POST" and request.POST.get("bulk_action") == "delete":
            ids = request.POST.getlist("selected")
            if ids:
                Product.objects.filter(id__in=ids, user=user).delete()
                messages.success(request, f"{len(ids)}件の商品を削除しました。")
            return redirect("main:product_list")

        # --- 絞り込みパラメータ取得 ---
        keyword = request.GET.get("keyword", "").strip()
        selected_cats = request.GET.getlist("cat")
        stock = request.GET.get("stock", "all")
        priority = request.GET.get("priority", "all")
        sort = request.GET.get("sort", "newest")

        # --- ベースクエリ ---
        qs = Product.objects.filter(user=user).prefetch_related(
            Prefetch("categories", queryset=Category.objects.all().order_by("id"))
        )

        # --- キーワード検索 ---
        if keyword:
            qs = qs.filter(
                Q(product_name__icontains=keyword) |
                Q(shop_name__icontains=keyword)
            )

        # --- カテゴリ絞り込み ---
        if selected_cats:
            try:
                ids = [int(c) for c in selected_cats]
                global_ids = [i - 100 for i in ids if i >= 100]  # 共通カテゴリ
                user_ids = [i for i in ids if i < 100]           # 独自カテゴリ

                q_filter = Q()

                # 共通カテゴリを実際の Category に変換
                if global_ids:
                    common_cats = Category.objects.filter(
                        id__in=global_ids)
                    cat_names = [c.category_name for c in common_cats]
                    q_filter |= Q(
                        categories__category_name__in=cat_names,
                        categories__is_global=True,
                        categories__user__isnull=True
                    )

                # 独自カテゴリ（ユーザー紐づき）
                if user_ids:
                    q_filter |= Q(
                        categories__id__in=user_ids,
                        categories__user=user,
                        categories__is_global=False
                    )

                if q_filter:
                    qs = qs.filter(q_filter).distinct()

            except ValueError:
                pass

        # --- 在庫フィルタ ---
        if stock == "low":
            qs = qs.filter(latest_stock_count__lte=3, latest_stock_count__gt=0)
        elif stock == "none":
            qs = qs.filter(is_in_stock=False)

        # --- 優先度フィルタ ---
        if priority in ["高", "普通"]:
            qs = qs.filter(priority=priority)

        # --- 並び替え ---
        if sort == "newest":
            qs = qs.order_by("-created_at")
        elif sort == "oldest":
            qs = qs.order_by("created_at")
        elif sort == "price_asc":
            qs = qs.order_by("latest_price", "initial_price")
        elif sort == "price_desc":
            qs = qs.order_by("-latest_price", "-initial_price")
        else:
            qs = qs.order_by("-created_at")

        # --- 並び順オプション ---
        sort_options = [
            ("newest", "新しい順"),
            ("oldest", "古い順"),
            ("price_asc", "価格が安い順"),
            ("price_desc", "価格が高い順"),
        ]

        # --- フィルタタグ生成 ---
        filter_tags = []
        if keyword:
            filter_tags.append(
                ("keyword", f"キーワード：{keyword}", "filter-tag-sort"))

        if selected_cats:
            try:
                ids = [int(c) for c in selected_cats]
                global_ids = [i - 100 for i in ids if i >= 100]
                user_ids = [i for i in ids if i < 100]

                category_cats = Category.objects.filter(
                    id__in=global_ids, is_global=True)
                for c in category_cats:
                    filter_tags.append(
                        ("cat", f"{c.category_name}", "filter-tag-common"))

                user_cats = Category.objects.filter(id__in=user_ids, user=user)
                for c in user_cats:
                    filter_tags.append(
                        ("cat", f"{c.category_name}", "filter-tag-user"))
            except ValueError:
                pass

        if stock in ["low", "none"]:
            label = "わずか" if stock == "low" else "なし"
            filter_tags.append(("stock", f"在庫：{label}", "filter-tag-stock"))

        if priority in ["高", "普通"]:
            filter_tags.append(
                ("priority", f"優先度：{priority}", "filter-tag-priority"))

        sort_labels = {
            "newest": "新しい順",
            "oldest": "古い順",
            "price_asc": "価格が安い順",
            "price_desc": "価格が高い順",
        }

        if sort in sort_labels:
            filter_tags.append(
                ("sort", f"並び順：{sort_labels[sort]}", "filter-tag-sort"))

        # --- ページネーション ---
        paginator = Paginator(qs, 20)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # --- カテゴリ情報（商品登録と同じ構成に統一） ---
        global_categories = Category.objects.filter(
            is_global=True, user__isnull=True
        ).order_by("id")

        user_categories = Category.objects.filter(
            user=request.user, is_global=False
        )

        # 一覧画面では特定の商品は選択されていないため空でOK
        selected_category_ids = []

        # --- 表示 ---
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
                "filter_tags": filter_tags,
                "is_filtered": _has_filter(keyword, selected_cats, stock, priority, sort),
                "sort_options": sort_options,
            },
        )

    except Exception as e:
        log_error(
            user=request.user,
            type_name=type(e).__name__,
            source="product_list",
            err=e
        )
        messages.error(request, "商品一覧の表示中にエラーが発生しました。")
        return redirect("main:landing_page")


@login_required
def product_detail(request, pk):
    """商品詳細ページ"""
    product = get_object_or_404(Product, pk=pk, user=request.user)

    # ======================================================
    # 価格履歴データ取得（過去180日分・昇順）
    # ======================================================
    histories = (
        PriceHistory.objects.filter(product=product)
        .order_by("checked_at")[:180]
    )

    # ======================================================
    # 閾値ライン計算（通知条件に応じて）
    # ======================================================
    threshold_value = None
    if product.flag_type == "buy_price" and product.threshold_price:
        threshold_value = float(product.threshold_price)
    elif product.flag_type == "percent_off" and product.threshold_price:
        if product.initial_price:
            threshold_value = float(product.initial_price) * \
                (1 - float(product.threshold_price) / 100)
    elif product.flag_type == "lowest_price":
        threshold_value = None

    # ======================================================
    # 価格履歴データの整形
    # ======================================================
    price_data = []
    for h in histories:
        # 価格と在庫のデータを整形と補完
        price = float(h.price) if h.price is not None else 0.0
        stock = int(h.stock_count) if h.stock_count is not None else 0

        price_data.append({
            "date": h.checked_at.strftime("%Y-%m-%d"),
            "price": price,
            "stock": stock,
            "threshold_value": threshold_value,
        })

    # ======================================================
    # データが存在しない場合（登録直後）
    # ======================================================
    if not price_data:
        price_data.append({
            "date": timezone.now().strftime("%Y-%m-%d"),
            "price": float(product.latest_price or product.initial_price or 0),
            "stock": int(product.is_in_stock) if product.is_in_stock is not None else 0,
            "threshold_value": threshold_value,
        })

    # ======================================================
    # デバッグ：price_dataの確認
    # ======================================================
    print("=== DEBUG: price_data ===")
    print(f"データ件数: {len(price_data)}")
    print(f"先頭5件: {price_data[:5]}")

    # ======================================================
    # テンプレートに渡す（JSON化は不要！json_scriptが自動でやる）
    # ======================================================
    context = {
        "product": product,
        "price_data": price_data,  # ← json.dumps() を削除！
    }
    return render(request, "main/product_detail.html", context)


def get_price_data(request, product_id):
    try:
        # 商品情報を取得
        product = Product.objects.get(id=product_id)

        # 価格履歴データの取得（チェック日順で並べ替え）
        price_history = PriceHistory.objects.filter(
            product=product).order_by('checked_at')

        # threshold_price が None の場合は 0 を設定
        threshold_price = float(
            product.threshold_price) if product.threshold_price is not None else 0.0

        # 価格データを整形
        price_data = [
            {
                # 日付を 'YYYY-MM-DD' 形式に変換
                'date': record.checked_at.strftime('%Y-%m-%d'),
                'price': float(record.price),  # 価格を数値に変換
                'stock': record.stock_count,  # 在庫数を取得
                'threshold_price': threshold_price  # 閾値を設定
            }
            for record in price_history
        ]

        # 価格データが空であればエラーレスポンスを返す
        if not price_data:
            return JsonResponse({"error": "価格データがありません"}, status=404)

        # 価格データが正しく取得できた場合はそれを返す
        return JsonResponse({"price_data": price_data})

    except Product.DoesNotExist:
        # 商品が見つからない場合はエラーレスポンスを返す
        return JsonResponse({"error": "商品が見つかりません"}, status=404)

# ======================================================
# 商品登録
# ======================================================


@login_required
def product_create(request):
    """新規商品登録"""
    try:
        if request.method == "POST":
            form = ProductForm(request.POST, user=request.user)

            if form.is_valid():
                product = form.save(commit=False)
                product.user = request.user

                # --- 画像URL設定 ---
                image_url = request.POST.get("image_url")
                if image_url:
                    product.image_url = image_url

                # ======================================================
                # ✅ 修正：initial_price が 0 または None の場合、
                #    楽天APIから再取得して設定する
                # ======================================================
                if not product.initial_price or product.initial_price == 0:
                    product_url = request.POST.get("product_url")
                    if product_url:
                        from main.utils.rakuten_api import fetch_rakuten_item
                        api_result = fetch_rakuten_item(product_url)

                        if api_result and api_result.get("initial_price"):
                            try:
                                product.initial_price = decimal.Decimal(
                                    str(api_result["initial_price"]))
                                product.latest_price = product.initial_price
                                print(
                                    f"[product_create] ✅ API価格を設定: {product.initial_price}円")
                            except (ValueError, TypeError, decimal.InvalidOperation) as e:
                                print(f"[product_create] ⚠️ 価格変換エラー: {e}")

                # ======================================================
                # ✅ 修正：通知条件設定（flag_type を正しく保存）
                # ======================================================
                flag_type_raw = request.POST.get(
                    "flag_type")  # ← "1", "2", "5" などの数値文字列
                threshold_price_input = request.POST.get(
                    "threshold_price", "").strip()
                flag_value_input = request.POST.get("flag_value", "").strip()

                print(f"[DEBUG] flag_type_raw: {flag_type_raw}")
                print(
                    f"[DEBUG] threshold_price_input: {threshold_price_input}")
                print(f"[DEBUG] flag_value_input: {flag_value_input}")

                # --- flag_type を文字列に変換してDBに保存 ---
                flag_type_map = {
                    "1": "lowest_price",
                    "2": "percent_off",
                    "5": "buy_price",
                }
                product.flag_type = flag_type_map.get(
                    flag_type_raw, "lowest_price")
                print(
                    f"[DEBUG] product.flag_type (mapped): {product.flag_type}")

                # --- 通知条件ごとの処理 ---
                if flag_type_raw == "2" and flag_value_input:  # 割引率
                    try:
                        product.flag_value = decimal.Decimal(flag_value_input).quantize(
                            decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)

                        # 割引後価格の計算
                        if product.initial_price:
                            discounted_price = product.initial_price * \
                                (1 - product.flag_value / 100)
                            product.threshold_price = discounted_price.quantize(
                                decimal.Decimal("1"), rounding=decimal.ROUND_HALF_UP)
                            print(
                                f"[product_create] 割引率: {product.flag_value}% → 閾値: {product.threshold_price}円")
                    except (ValueError, decimal.InvalidOperation):
                        product.flag_value = None
                        product.threshold_price = None

                elif flag_type_raw == "5" and threshold_price_input:  # 買い時価格
                    try:
                        product.threshold_price = decimal.Decimal(threshold_price_input).quantize(
                            decimal.Decimal("1"), rounding=decimal.ROUND_HALF_UP)
                        product.flag_value = None  # 買い時価格の場合は flag_value は不要
                        print(
                            f"[product_create] 買い時価格: {product.threshold_price}円")
                    except (ValueError, decimal.InvalidOperation):
                        product.threshold_price = None
                        product.flag_value = None

                elif flag_type_raw == "1":  # 最安値
                    product.threshold_price = None
                    product.flag_value = None
                    print(f"[product_create] 最安値通知モード")

                # ======================================================
                # ✅ 重要：save() の直前に flag_type を確認
                # ======================================================
                print(f"[DEBUG] 保存直前の product.flag_type: {product.flag_type}")
                print(
                    f"[DEBUG] 保存直前の product.threshold_price: {product.threshold_price}")

                # --- 保存 ---
                product.save()

                # ======================================================
                # ✅ 保存後に値を確認
                # ======================================================
                product.refresh_from_db()
                print(f"[DEBUG] 保存後の product.flag_type: {product.flag_type}")
                print(
                    f"[DEBUG] 保存後の product.threshold_price: {product.threshold_price}")

                # ======================================================
                # ✅ 修正：初回の価格履歴を PriceHistory に追加
                # ======================================================
                if product.initial_price and product.initial_price > 0:
                    PriceHistory.objects.create(
                        product=product,
                        price=product.initial_price,
                        stock_count=1,
                        checked_at=timezone.now()
                    )
                    print(
                        f"[product_create] ✅ 初回価格履歴を追加: {product.initial_price}円")

                # --- 買い時フラグ更新 ---
                from main.utils.flag_checker import update_flag_status
                update_flag_status(product)

                # --- カテゴリ紐づけ処理 ---
                selected_cats_raw = request.POST.get("selected_cats", "")
                if selected_cats_raw:
                    try:
                        cat_ids = [
                            int(x) for x in selected_cats_raw.split(",") if x.strip().isdigit()
                        ]
                        if cat_ids:
                            categories = Category.objects.filter(
                                Q(id__in=cat_ids),
                                Q(is_global=True, user__isnull=True)
                                | Q(is_global=False, user=request.user)
                            ).distinct()
                            product.categories.set(categories)
                    except Exception as e:
                        print("DEBUG category linkage error:", e)

                messages.success(request, "商品を登録しました。")
                return redirect("main:product_list")

            else:
                messages.error(request, "入力内容に誤りがあります。")

        else:
            form = ProductForm(user=request.user)

        global_categories = Category.objects.filter(
            is_global=True, user__isnull=True)
        user_categories = Category.objects.filter(
            user=request.user, is_global=False)

        return render(
            request,
            "main/product_form.html",
            {
                "form": form,
                "is_edit": False,
                "global_categories": global_categories,
                "user_categories": user_categories,
                "selected_category_ids": [],
            },
        )

    except Exception as e:
        log_error(
            user=request.user,
            type_name=type(e).__name__,
            source="product_create",
            err=e
        )
        messages.error(request, "商品登録中にエラーが発生しました。")
        return redirect("main:product_list")


@login_required
def product_edit(request, pk):
    """商品編集ページ（商品情報＋通知条件）"""
    import decimal
    from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

    try:
        product = get_object_or_404(Product, pk=pk, user=request.user)

        if request.method == "POST":
            form = ProductForm(
                request.POST, instance=product, user=request.user)
            if form.is_valid():
                product = form.save(commit=False)

                flag_type = product.flag_type
                flag_value_raw = request.POST.get("flag_value", "").strip()
                threshold_raw = request.POST.get("threshold_price", "").strip()

                # --- 通知条件ごとのflag_value設定 ---
                new_flag_value = None  # ←安全な代入前変数

                if flag_type == "percent_off" and flag_value_raw:
                    try:
                        new_flag_value = Decimal(flag_value_raw).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP)
                    except (InvalidOperation, ValueError):
                        form.add_error("flag_value", "割引率は数値で入力してください。")

                elif flag_type == "buy_price" and threshold_raw:
                    try:
                        val = Decimal(threshold_raw).quantize(
                            Decimal("1"), rounding=ROUND_HALF_UP)
                        if product.initial_price and val > product.initial_price:
                            form.add_error("threshold_price",
                                           "登録時価格より大きい値は設定できません。")
                        else:
                            new_flag_value = val
                            product.threshold_price = val
                    except (InvalidOperation, ValueError):
                        form.add_error("threshold_price", "価格は数値で入力してください。")

                # --- 正常値のみ反映 ---
                if new_flag_value is not None:
                    product.flag_value = new_flag_value

                # --- 型保証：不正なDecimalを除外 ---
                if not isinstance(product.flag_value, Decimal):
                    product.flag_value = Decimal("0")

                # --- 保存処理 ---
                if not form.errors:
                    product.save()

                    # ✅ カテゴリ更新
                    selected_cats_raw = request.POST.get("selected_cats", "")
                    if selected_cats_raw:
                        try:
                            cat_ids = [int(x) for x in selected_cats_raw.split(
                                ",") if x.strip().isdigit()]
                            categories = Category.objects.filter(
                                Q(id__in=cat_ids),
                                Q(is_global=True, user__isnull=True) | Q(
                                    is_global=False, user=request.user)
                            ).distinct()
                            product.categories.set(categories)
                        except Exception as e:
                            print("product_edit category linkage error:", e)
                    else:
                        product.categories.clear()

                    update_flag_status(product)
                    messages.success(request, "商品情報を更新しました。")
                    return redirect("main:product_list")
                else:
                    messages.error(request, "入力内容に誤りがあります。")

            else:
                messages.error(request, "入力内容に誤りがあります。")

        else:
            form = ProductForm(instance=product, user=request.user)

        global_categories = Category.objects.filter(
            is_global=True, user__isnull=True
        ).exclude(category_name="未分類").order_by("id")

        user_categories = Category.objects.filter(
            user=request.user, is_global=False
        ).exclude(category_name="未分類")

        selected_category_ids = list(
            product.categories.values_list("id", flat=True))

        return render(
            request,
            "main/product_edit.html",
            {
                "form": form,
                "is_edit": True,
                "product": product,
                "global_categories": global_categories,
                "user_categories": user_categories,
                "selected_category_ids": selected_category_ids,
            },
        )

    except Exception as e:
        log_error(
            user=request.user,
            type_name=type(e).__name__,
            source="product_edit",
            err=e,
        )
        return redirect("main:product_list")


# --- 修正後: main/views_product.py ---
@login_required
def product_delete(request, pk):
    """商品削除（論理削除対応）"""
    try:
        product = get_object_or_404(Product, pk=pk, user=request.user)

        if request.method == "POST":
            # ✅ 論理削除に変更
            product.is_deleted = True
            product.save(update_fields=["is_deleted"])

            messages.success(request, "商品を削除しました（論理削除）。")
            return redirect("main:product_list")

        return render(request, "main/product_confirm_delete.html", {
            "product": product
        })

    except Exception as e:
        log_error(
            user=request.user,
            type_name=type(e).__name__,
            source="product_delete",
            err=e,
        )
        messages.error(request, "商品削除中にエラーが発生しました。")
        return redirect("main:product_list")
# --- END: main/views_product.py ---
