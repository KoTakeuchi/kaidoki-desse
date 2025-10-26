# main/views_category.py
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required  # ←★これを追加
from django.db.models import Q

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Category
from .serializers import CategorySerializer
from .permissions import IsOwnerOrReadOnlyCategory


class CategoryViewSet(viewsets.ModelViewSet):
    """
    /api/categories/
      GET: 自分のカテゴリ一覧（共通カテゴリ＋自分のカテゴリ）
      POST: 新規登録（is_global=False固定）
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnlyCategory]

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(Q(is_global=True) | Q(user=user)).order_by("id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_global=False)


# ===== ここからページ用ビュー（ORM直アクセス） =====

@login_required
def category_list(request):
    """カテゴリ一覧（APIは使わずORMで直取得）"""
    categories = (
        Category.objects
        .filter(Q(is_global=True) | Q(user=request.user))
        .order_by("id")
    )
    return render(request, "main/category_list.html", {"categories": categories})


@login_required
def category_create(request):
    """カテゴリ登録（APIは使わずORMで直作成）"""
    if request.method == "POST":
        name = (request.POST.get("category_name") or "").strip()
        if not name:
            messages.warning(request, "カテゴリ名を入力してください。")
            return render(request, "main/category_create.html", {"error": "カテゴリ名を入力してください。"})

        # 重複（自分のカテゴリ名）を軽くガード（必要なければ削除OK）
        exists = Category.objects.filter(
            user=request.user, category_name=name, is_global=False).exists()
        if exists:
            messages.info(request, f"「{name}」はすでに登録済みです。")
            return redirect("main:category_list")

        Category.objects.create(
            user=request.user,
            category_name=name,
            is_global=False,
        )
        messages.success(request, f"カテゴリ「{name}」を登録しました。")
        return redirect("main:category_list")

    # GET
    return render(request, "main/category_create.html")
