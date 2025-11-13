from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views_api  # ✅ views_api を明示的に import

from .views_api import (
    HealthCheck,
    ProductViewSet,
    NotificationEventViewSet,
    ProductPriceHistoryView,
    UserNotificationSettingView,
    CategoryViewSet,
)

# === DRFルーター定義 ===
router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"notifications", NotificationEventViewSet,
                basename="notification")
router.register(r"categories", CategoryViewSet, basename="category")

# === URL定義 ===
urlpatterns = [
    path("", include(router.urls)),

    # --- ヘルスチェック ---
    path("health/", HealthCheck.as_view(), name="api-health"),

    # --- 商品価格履歴 ---
    path(
        "products/<int:product_id>/price-history/",
        ProductPriceHistoryView.as_view(),
        name="product-price-history",
    ),

    # --- ユーザー通知設定 ---
    path(
        "user/settings/",
        UserNotificationSettingView.as_view(),
        name="user-settings",
    ),

    # --- 楽天API ---
    path(
        "fetch_rakuten_item/",
        views_api.fetch_rakuten_item,  # ✅ 修正済み参照
        name="fetch_rakuten_item",
    ),
]

# === JWT認証 ===
urlpatterns += [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
