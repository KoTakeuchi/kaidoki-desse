
from .models import Category
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes
from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwnerOrReadOnlyCategory  # ← 追加
from .serializers import CategorySerializer, MyCategoryCreateSerializer

from .models import Product, PriceHistory, NotificationEvent, UserNotificationSetting
from .serializers import (
    ProductSerializer, ProductWriteSerializer, PriceHistorySerializer,
    NotificationEventSerializer, UserNotificationSettingSerializer
)
from rest_framework.permissions import IsAuthenticated

User = get_user_model()


class HealthCheck(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class ProductViewSet(viewsets.ModelViewSet):
    """
    /api/products/
    GET: 読み取り（全件 or ID指定）
    POST: 登録
    PATCH: 更新
    DELETE: 削除
    """
    queryset = Product.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # ✅ Swaggerにcategory_id / q を明示的に追加
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="category_id",
                description="カテゴリIDで商品を絞り込み（例: 1）",
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="q",
                description="商品名の部分一致検索（例: 冷蔵庫）",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """GET /api/products/ 一覧取得（category_id / q 対応版）"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        """クエリパラメータで絞り込み"""
        user = self.request.user

        # 👇 匿名ユーザーの場合は None に置き換え
        if not user.is_authenticated:
            user = None

        qs = Product.objects.all()

        # 認証ユーザーは自分の商品だけ
        if user:
            qs = qs.filter(user=user)

        # --- category_id指定で絞り込み ---
        category_id = self.request.query_params.get("category_id")
        if category_id and category_id.isdigit():
            qs = qs.filter(category_id=int(category_id))

        # --- q指定で部分一致検索 ---
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(product_name__icontains=q)

        return qs.order_by("id")

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductWriteSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    読み取り用: /api/notifications/
    """
    queryset = NotificationEvent.objects.all().order_by('-occurred_at')
    serializer_class = NotificationEventSerializer
    permission_classes = [permissions.AllowAny]


class ProductPriceHistoryView(APIView):
    """
    読み取り用: /api/products/{product_id}/price-history/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, product_id: int, *args, **kwargs):
        product = get_object_or_404(Product, pk=product_id)
        qs = PriceHistory.objects.filter(
            product=product).order_by('-created_at')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        items = qs[start:end]
        return Response({
            "count": total,
            "page": page,
            "results": PriceHistorySerializer(items, many=True).data
        })


class CategoryViewSet(viewsets.ModelViewSet):
    """
    /api/categories/
      GET: 自分のカテゴリ一覧（共通カテゴリ＋独自カテゴリ）
      POST: 独自カテゴリ新規作成（is_global=False固定）
      PATCH/DELETE: 自分の独自カテゴリのみ可能
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = []  # 開発中は無認証で動作OK

    def get_queryset(self):
        user = self.request.user

        # ✅ 未ログインなら共通カテゴリのみ
        if not user.is_authenticated:
            return Category.objects.filter(is_global=True).order_by("id")

        # 共通カテゴリ + 自分のカテゴリ
        return Category.objects.filter(
            models.Q(is_global=True) | models.Q(user=user)
        ).order_by("id")

    def get_serializer_class(self):
        if self.action == "create":
            return MyCategoryCreateSerializer
        return CategorySerializer

    def perform_create(self, serializer):
        """
        POST /api/categories/
        """
        user = self.request.user

        # ✅ 未ログイン時は強制的に「testuser」を紐付ける（開発用）
        if not user.is_authenticated:
            user = User.objects.filter(username="testuser").first()
            print("⚠️ 未ログインのため 'testuser' を代入")

        # ⚙️ 重複エラーの原因 → user と is_global は Serializer 側で設定
        serializer.save()


class UserNotificationSettingView(APIView):
    """
    認証ユーザーの通知設定を参照・更新
    GET/PUT/PATCH /api/user/settings/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        setting, _ = UserNotificationSetting.objects.get_or_create(user=user)
        return Response(UserNotificationSettingSerializer(setting).data)

    def put(self, request, *args, **kwargs):
        user = request.user
        setting, _ = UserNotificationSetting.objects.get_or_create(user=user)
        ser = UserNotificationSettingSerializer(setting, data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(user=user)
        return Response(ser.data)

    def patch(self, request, *args, **kwargs):
        user = request.user
        setting, _ = UserNotificationSetting.objects.get_or_create(user=user)
        ser = UserNotificationSettingSerializer(
            setting, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save(user=user)
        return Response(ser.data)
