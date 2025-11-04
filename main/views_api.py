# 実行ディレクトリ: I:\school\kaidoki-desse\main\views_api.py
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from urllib.parse import urlparse
import requests
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from main.utils.error_logger import log_error

from .models import (
    Category,
    Product,
    PriceHistory,
    NotificationEvent,
    UserNotificationSetting,
)
from .serializers import (
    CategorySerializer,
    MyCategoryCreateSerializer,
    ProductSerializer,
    ProductWriteSerializer,
    PriceHistorySerializer,
    NotificationEventSerializer,
    UserNotificationSettingSerializer,
)
from .permissions import IsOwnerOrReadOnlyCategory

User = get_user_model()


# ======================================================
# Health Check
# ======================================================
class HealthCheck(APIView):
    """サーバ稼働確認用"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


# ======================================================
# ProductViewSet
# ======================================================
class ProductViewSet(viewsets.ModelViewSet):
    """
    /api/products/
    GET: 一覧取得
    POST: 登録
    PATCH: 更新
    DELETE: 削除
    """
    queryset = Product.objects.all().order_by("id")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="category_id",
                description="カテゴリID（単一または複数指定）",
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="q",
                description="商品名での部分一致検索（例: 冷蔵庫）",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """GET /api/products/"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        """クエリパラメータで絞り込み"""
        user = self.request.user if self.request.user.is_authenticated else None
        qs = Product.objects.all()

        if user:
            qs = qs.filter(user=user)

        # --- カテゴリ絞り込み（複数対応） ---
        category_ids = self.request.query_params.getlist("category_id")
        if category_ids:
            qs = qs.filter(categories__id__in=category_ids).distinct()

        # --- 商品名検索 ---
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(product_name__icontains=q)

        return qs.order_by("id")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProductWriteSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ======================================================
# NotificationEventViewSet
# ======================================================
class NotificationEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/notifications/
    読み取り専用（在庫・価格変動通知イベント）
    """
    queryset = NotificationEvent.objects.all().order_by("-occurred_at")
    serializer_class = NotificationEventSerializer
    permission_classes = [permissions.AllowAny]  # 本番時は IsAuthenticated に変更予定


# ======================================================
# ProductPriceHistoryView
# ======================================================
class ProductPriceHistoryView(APIView):
    """
    /api/products/{product_id}/price-history/
    商品ごとの価格履歴（ページング対応）
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, product_id: int, *args, **kwargs):
        product = get_object_or_404(Product, pk=product_id)
        qs = PriceHistory.objects.filter(
            product=product).order_by("-created_at")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = qs.count()
        items = qs[start:end]
        return Response({
            "count": total,
            "page": page,
            "results": PriceHistorySerializer(items, many=True).data
        })


# ======================================================
# CategoryViewSet
# ======================================================
class CategoryViewSet(viewsets.ModelViewSet):
    """
    /api/categories/
    GET: 自分のカテゴリ一覧（共通カテゴリ＋独自カテゴリ）
    POST: 独自カテゴリ新規作成
    PATCH/DELETE: 自分のカテゴリのみ
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Category.objects.filter(is_global=True).order_by("id")
        return Category.objects.filter(
            models.Q(is_global=True) | models.Q(user=user)
        ).order_by("id")

    def get_serializer_class(self):
        if self.action == "create":
            return MyCategoryCreateSerializer
        return CategorySerializer

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            user = User.objects.filter(username="testuser").first()
        serializer.save(user=user, is_global=False)


# ======================================================
# UserNotificationSettingView
# ======================================================
class UserNotificationSettingView(APIView):
    """
    /api/user/settings/
    GET: 通知設定の取得
    PUT/PATCH: 通知設定の更新
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        setting, _ = UserNotificationSetting.objects.get_or_create(user=user)
        return Response(UserNotificationSettingSerializer(setting).data)

    def put(self, request, *args, **kwargs):
        try:
            user = request.user
            setting, _ = UserNotificationSetting.objects.get_or_create(
                user=user)
            ser = UserNotificationSettingSerializer(setting, data=request.data)
            ser.is_valid(raise_exception=True)
            ser.save(user=user)
            return Response(ser.data)
        except Exception as e:
            log_error(user=request.user, type_name=type(
                e).__name__, source="user_settings_put", err=e)
            return Response({"error": str(e)}, status=500)

    def patch(self, request, *args, **kwargs):
        try:
            user = request.user
            setting, _ = UserNotificationSetting.objects.get_or_create(
                user=user)
            ser = UserNotificationSettingSerializer(
                setting, data=request.data, partial=True)
            ser.is_valid(raise_exception=True)
            ser.save(user=user)
            return Response(ser.data)
        except Exception as e:
            log_error(user=request.user, type_name=type(
                e).__name__, source="user_settings_patch", err=e)
            return Response({"error": str(e)}, status=500)


# ======================================================
# fetch_rakuten_item（楽天商品情報取得API）
# ======================================================


@require_GET
def fetch_rakuten_item(request):
    """
    ✅ 楽天市場の商品URLから商品情報を取得して返す
    例:
      /api/fetch_rakuten_item/?url=https://item.rakuten.co.jp/xxxx/yyyy
    """
    url = request.GET.get("url")
    if not url:
        return JsonResponse({"error": "URLが指定されていません。"}, status=400)

    try:
        parsed = urlparse(url)
        if "rakuten.co.jp" not in parsed.netloc:
            return JsonResponse({"error": "楽天市場の商品URLを指定してください。"}, status=400)

        app_id = getattr(settings, "RAKUTEN_APP_ID", None)
        if not app_id:
            return JsonResponse({"error": "RAKUTEN_APP_ID が未設定です。"}, status=500)

        # URLからショップコードとアイテムコードを推定
        try:
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) < 2:
                return JsonResponse({"error": "URL形式が不正です。"}, status=400)
            shop_code, item_code = path_parts[-2], path_parts[-1]
        except Exception:
            return JsonResponse({"error": "URL解析に失敗しました。"}, status=400)

        # 楽天API呼び出し
        endpoint = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"
        params = {
            "applicationId": app_id,
            "hits": 1,
            "shopCode": shop_code,
            "itemCode": f"{shop_code}:{item_code}",
        }
        res = requests.get(endpoint, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()

        if not data.get("Items"):
            return JsonResponse({"error": "商品が見つかりませんでした。"}, status=404)

        item = data["Items"][0]["Item"]

        result = {
            "product_name": item.get("itemName"),
            "image_url": item.get("mediumImageUrls", [{}])[0].get("imageUrl"),
            "price": item.get("itemPrice"),
            "shop_name": item.get("shopName"),
            "url": item.get("itemUrl"),
        }

        return JsonResponse(result)

    except requests.RequestException as e:
        log_error(
            user=request.user if request.user.is_authenticated else None,
            type_name=type(e).__name__,
            source="fetch_rakuten_item",
            err=e,
        )
        return JsonResponse({"error": f"API通信エラー: {e}"}, status=500)

    except Exception as e:
        log_error(
            user=request.user if request.user.is_authenticated else None,
            type_name=type(e).__name__,
            source="fetch_rakuten_item",
            err=e,
        )
        return JsonResponse({"error": str(e)}, status=500)
