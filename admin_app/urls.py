from django.urls import path
from . import views_admin

app_name = "admin_app"

urlpatterns = [
    path("dashboard/", views_admin.admin_dashboard, name="admin_dashboard"),
    path("users/", views_admin.admin_user_list, name="admin_user_list"),
    path("products/", views_admin.admin_product_list, name="admin_product_list"),

    # 共通カテゴリ管理
    path("categories/", views_admin.admin_category, name="admin_category"),

    path("notifications/", views_admin.admin_notification_list,
         name="admin_notifications"),
    path("notifications/<int:log_id>/", views_admin.admin_notification_detail,
         name="admin_notification_detail"),
    path("error_logs/", views_admin.admin_error_logs, name="admin_error_logs"),
]
