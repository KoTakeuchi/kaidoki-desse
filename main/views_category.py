# 実行ディレクトリ: I:\school\kaidoki-desse\main\views_category.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods
from .models import Category, Product


# ----------------------------------------
# API: カテゴリ一覧（GET）
# ----------------------------------------
@login_required
@require_http_methods(["GET"])
def api_category_list(request):
    """
    自分のカテゴリ + 共通カテゴリをJSONで返す
    （未分類を除外する）
    """
    user = request.user
    categories = (
        Category.objects
        .filter(Q(is_global=True) | Q(user=user))
        .exclude(category_name="未分類")   # ✅ 未分類を除外
        .order_by("id")
        .values("id", "category_name", "is_global")
    )
    return JsonResponse({"categories": list(categories)}, status=200)


# ----------------------------------------
# API: カテゴリ登録（POST）
# ----------------------------------------
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_category_create(request):
    """新しいカテゴリを登録（is_global=False固定）"""
    user = request.user
    name = (request.POST.get("category_name") or "").strip()

    if not name:
        return JsonResponse({"error": "カテゴリ名を入力してください。"}, status=400)
    if len(name) > 10:
        return JsonResponse({"error": "カテゴリ名は全角10文字以内で入力してください。"}, status=400)

    # 上限チェック（未分類を除外してカウント）
    current_count = Category.objects.filter(
        user=user, is_global=False
    ).exclude(category_name="未分類").count()
    if current_count >= 5:
        return JsonResponse({"error": "登録できるカテゴリは最大5件までです。"}, status=400)

    # 重複チェック
    if Category.objects.filter(user=user, category_name=name, is_global=False).exists():
        return JsonResponse({"error": f"「{name}」はすでに登録済みです。"}, status=400)

    category = Category.objects.create(
        user=user,
        category_name=name,
        is_global=False,
    )

    return JsonResponse({
        "success": True,
        "id": category.id,
        "category_name": category.category_name,
    }, status=201)


# ----------------------------------------
# API: カテゴリ更新（編集）
# ----------------------------------------
@login_required
def api_category_update(request, category_id):
    """カテゴリ編集API"""
    if request.method != "POST":
        return JsonResponse({"error": "POSTメソッドのみ対応"}, status=405)

    new_name = (request.POST.get("category_name") or "").strip()
    if not new_name:
        return JsonResponse({"error": "カテゴリ名を入力してください。"}, status=400)
    if len(new_name) > 10:
        return JsonResponse({"error": "カテゴリ名は全角10文字以内で入力してください。"}, status=400)

    try:
        category = Category.objects.get(
            id=category_id, user=request.user, is_global=False
        )
    except Category.DoesNotExist:
        return JsonResponse({"error": "カテゴリが見つかりません。"}, status=404)

    if category.category_name == "未分類":
        return JsonResponse({"error": "「未分類」は編集できません。"}, status=400)

    exists = Category.objects.filter(
        user=request.user, category_name=new_name, is_global=False
    ).exclude(id=category_id).exists()
    if exists:
        return JsonResponse({"error": f"「{new_name}」はすでに登録されています。"}, status=400)

    category.category_name = new_name
    category.save()

    return JsonResponse({
        "success": True,
        "category_name": category.category_name
    })


# ----------------------------------------
# API: カテゴリ削除（商品を未分類に移動）
# ----------------------------------------
@login_required
def api_category_delete(request, category_id):
    """カテゴリ削除API（紐づく商品は未分類へ）"""
    if request.method != "POST":
        return JsonResponse({"error": "POSTメソッドのみ対応"}, status=405)

    try:
        category = Category.objects.get(
            id=category_id, user=request.user, is_global=False
        )
    except Category.DoesNotExist:
        return JsonResponse({"error": "カテゴリが見つかりません。"}, status=404)

    if category.category_name == "未分類":
        return JsonResponse({"error": "「未分類」は削除できません。"}, status=400)

    uncategorized, _ = Category.objects.get_or_create(
        user=request.user, category_name="未分類", defaults={"is_global": False}
    )

    # 紐づく商品を未分類へ移動
    products = Product.objects.filter(categories=category)
    for product in products:
        product.categories.remove(category)
        product.categories.add(uncategorized)

    category.delete()

    return JsonResponse({"success": True})


# ----------------------------------------
# ページ: カテゴリ管理（一般ユーザー用）
# ----------------------------------------
@login_required
def category_my(request):
    """
    カテゴリ管理ページ
    ・自分のカテゴリのみ（共通カテゴリは除外）
    ・未分類は除外
    ・各カテゴリに紐づく商品の登録数を集計
    """
    categories = (
        Category.objects.filter(user=request.user, is_global=False)
        .exclude(category_name="未分類")
        .annotate(product_count=Count("products"))
        .order_by("id")
    )

    return render(request, "main/category_my.html", {"categories": categories})
