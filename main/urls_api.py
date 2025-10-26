from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_api import (
    HealthCheck, ProductViewSet, NotificationEventViewSet, ProductPriceHistoryView,
    UserNotificationSettingView, CategoryViewSet,
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'notifications', NotificationEventViewSet,
                basename='notification')
router.register(r'categories', CategoryViewSet, basename='category')  # ✅ 追加

urlpatterns = [
    path('', include(router.urls)),

    path('health/', HealthCheck.as_view(), name='api-health'),
    path('products/<int:product_id>/price-history/', ProductPriceHistoryView.as_view(),
         name='product-price-history'),
    path('user/settings/', UserNotificationSettingView.as_view(),
         name='user-settings'),
]


urlpatterns += [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
