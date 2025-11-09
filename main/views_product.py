# --- START: main/views_product.py ---
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from main.forms import ProductForm
from main.models import Product, Category, PriceHistory
from main.utils.error_logger import log_error
from admin_app.models import CommonCategory


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
                    common_cats = CommonCategory.objects.filter(
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

                common_cats = CommonCategory.objects.filter(id__in=global_ids)
                for c in common_cats:
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

        # --- カテゴリ情報 ---
        global_categories = CommonCategory.objects.all().order_by("id")
        user_categories = Category.objects.filter(user=user, is_global=False)

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


# ======================================================
# 商品詳細
# ======================================================
@login_required
def product_detail(request, pk):
    """商品詳細ページ"""
    product = get_object_or_404(Product, pk=pk, user=request.user)
    price_history = PriceHistory.objects.filter(
        product=product).order_by("checked_at")

    return render(request, "main/product_detail.html", {
        "product": product,
        "price_history": price_history,
    })


@login_required
def product_create(request):
    """新規商品登録"""
    try:
        if request.method == "POST":
            form = ProductForm(request.POST, user=request.user)

            # --- デバッグ出力 ---
            print("DEBUG POST[selected_cats]:",
                  request.POST.get("selected_cats"))
            print("DEBUG POST[categories]:",
                  request.POST.getlist("categories"))
            print("DEBUG POST[flag_type]:", request.POST.get("flag_type"))
            print("DEBUG POST[flag_value]:", request.POST.get("flag_value"))

            if form.is_valid():
                product = form.save(commit=False)
                product.user = request.user

                # --- 画像URL設定 ---
                image_url = request.POST.get("image_url")
                if image_url:
                    product.image_url = image_url

                # --- 割引率(flag_value)保存 ---
                flag_type = form.cleaned_data.get("flag_type")
                flag_value = request.POST.get("flag_value")

                product.flag_type = flag_type  # ← この行を追加

                if flag_type == "percent_off" and flag_value:
                    try:
                        product.flag_value = float(flag_value)
                    except ValueError:
                        product.flag_value = None
                else:
                    product.flag_value = None

                product.save()

                # --- 買い時フラグ更新 ---
                from main.utils.flag_checker import update_flag_status
                update_flag_status(product)

                # --- カテゴリ紐づけ処理（selected_cats → M2M） ---
                selected_cats_raw = request.POST.get("selected_cats", "")
                if selected_cats_raw:
                    try:
                        cat_ids = [int(x) for x in selected_cats_raw.split(
                            ",") if x.strip().isdigit()]
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
        log_error(user=request.user, type_name=type(
            e).__name__, source="product_create", err=e)
        messages.error(request, "商品登録中にエラーが発生しました。")
        return redirect("main:product_list")


@login_required
def product_edit(request, pk):
    """商品編集"""
    try:
        product = get_object_or_404(Product, pk=pk, user=request.user)

        if request.method == "POST":
            form = ProductForm(
                request.POST, instance=product, user=request.user)
            if form.is_valid():
                product = form.save(commit=False)

                # --- 割引率更新処理 ---
                flag_type = form.cleaned_data.get("flag_type")
                flag_value = request.POST.get("flag_value")

                product.flag_type = flag_type  # ← この行を追加

                if flag_type == "percent_off" and flag_value:
                    try:
                        product.flag_value = float(flag_value)
                    except ValueError:
                        product.flag_value = None
                else:
                    product.flag_value = None

                product.save()

                # --- 買い時フラグ更新 ---
                from main.utils.flag_checker import update_flag_status
                update_flag_status(product)

                form.save_m2m()

                messages.success(request, "商品情報を更新しました。")
                return redirect("main:product_list")
            else:
                messages.error(request, "入力内容に誤りがあります。")
        else:
            form = ProductForm(instance=product, user=request.user)

        global_categories = Category.objects.filter(
            is_global=True, user__isnull=True)
        user_categories = Category.objects.filter(
            user=request.user, is_global=False)
        selected_category_ids = list(
            product.categories.values_list("id", flat=True))

        return render(
            request,
            "main/product_form.html",
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
        log_error(user=request.user, type_name=type(
            e).__name__, source="product_edit", err=e)
        messages.error(request, "商品編集中にエラーが発生しました。")
        return redirect("main:product_list")


@login_required
def product_delete(request, pk):
    """商品削除"""
    try:
        product = get_object_or_404(Product, pk=pk, user=request.user)

        if request.method == "POST":
            product.delete()
            messages.success(request, "商品を削除しました。")
            return redirect("main:product_list")

        return render(request, "main/product_confirm_delete.html", {
            "product": product
        })
    except Exception as e:
        log_error(user=request.user, type_name=type(
            e).__name__, source="product_delete", err=e)
        messages.error(request, "商品削除中にエラーが発生しました。")
        return redirect("main:product_list")
# --- END: main/views_product.py ---
