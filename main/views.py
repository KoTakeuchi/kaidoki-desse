# 実行ディレクトリ: I:\school\kaidoki-desse\main\views.py
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from main.models import Product, Category
from .forms import ProductForm, CustomUserCreationForm
from main.utils.error_logger import log_error
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


# ----------------------------------------
# トップページ / LP
# ----------------------------------------


def landing_page(request):
    """未ログイン時のトップページ"""
    if request.user.is_authenticated:
        return redirect("main:product_list")
    return render(request, "main/landing.html")

# ----------------------------------------
# ログイン / ログアウト / サインアップ
# ----------------------------------------


def login_view(request):
    """ログイン処理"""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "ログインしました。")
            return redirect("main:product_list")
        else:
            messages.error(request, "ログイン情報が正しくありません。")
    else:
        form = AuthenticationForm()

    return render(request, "auth/login.html", {"form": form})


def logout_view(request):
    """ログアウト処理"""
    logout(request)
    messages.info(request, "ログアウトしました。")
    return redirect("main:landing_page")


def signup_view(request):
    """新規登録処理（メール必須版）"""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "登録が完了しました。")
            return redirect("main:product_list")
        else:
            messages.error(request, "入力内容に誤りがあります。")
    else:
        form = CustomUserCreationForm()

    return render(request, "auth/signup.html", {"form": form})

# ----------------------------------------
# 商品一覧
# ----------------------------------------


@login_required(login_url="login")
def product_list(request):
    """
    商品一覧ページ
    未ログイン時でもクラッシュしないようtry-exceptで保護
    """
    try:
        # ソートキー取得
        sort = request.GET.get("sort", "cheap")

        # ユーザーの商品を取得
        products = Product.objects.filter(user=request.user)

        # 並び替え
        if sort == "cheap":
            products = products.order_by("initial_price")
        elif sort == "expensive":
            products = products.order_by("-initial_price")
        elif sort == "new":
            products = products.order_by("-created_at")
        elif sort == "old":
            products = products.order_by("created_at")

        # カテゴリ別データ
        global_categories = Category.objects.filter(is_global=True)
        user_categories = Category.objects.filter(
            user=request.user, is_global=False)

        context = {
            "products": products,
            "sort": sort,
            "global_categories": global_categories,
            "user_categories": user_categories,
        }
        return render(request, "main/product_list.html", context)

    except Exception as e:
        log_error(
            user=request.user if request.user.is_authenticated else None,
            type_name=type(e).__name__,
            source="product_list",
            err=e,
        )
        return render(request, "main/error_logs.html", {"error": e})


# ----------------------------------------
# 商品登録・編集・削除・詳細
# ----------------------------------------
@login_required(login_url="login")
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            return redirect("main:product_list")
    else:
        form = ProductForm()
    return render(request, "main/product_form.html", {"form": form})


@login_required(login_url="login")
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    return render(request, "main/product_detail.html", {"product": product})


@login_required(login_url="login")
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect("main:product_detail", pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, "main/product_form.html", {"form": form, "product": product})


@login_required(login_url="login")
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == "POST":
        product.delete()
        return redirect("main:product_list")
    return render(request, "main/product_confirm_delete.html", {"product": product})
