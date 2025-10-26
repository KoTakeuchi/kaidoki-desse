# 実行ディレクトリ: I:\school\kaidoki-desse\main\urls.py
from django.urls import path
from . import (
    views,
    views_profile,
    views_product,
    views_category,
    views_dashboard,
    views_admin_notifications,
)
from django.contrib.auth import views as auth_views

app_name = "main"

urlpatterns = [
    # --- ランディング ---
    path("", views.landing_page, name="landing_page"),

    # --- ユーザー関連 ---
    path("user/profile/", views_profile.profile_view, name="profile"),
    path("user/delete/", views_profile.account_delete_view, name="account_delete"),

    # --- 商品 ---
    path("index/", views_product.product_list, name="product_list"),
    path("product/<int:pk>/", views_product.product_detail, name="product_detail"),
    path("product/create/", views_product.product_create, name="product_create"),
    path("product/edit/<int:pk>/", views_product.product_edit, name="product_edit"),
    path("product/delete/<int:pk>/",
         views_product.product_delete, name="product_delete"),

    # --- 楽天API ---
    path("api/fetch_rakuten_item/", views_product.fetch_rakuten_info,
         name="fetch_rakuten_info"),
    # --- カテゴリ ---
    path("categories/", views_category.category_list, name="category_list"),
    path("categories/create/", views_category.category_create,
         name="category_create"),

    # --- 通知 ---
    path("notifications/list/",
         views_dashboard.notification_list, name="notifications"),
    path("notifications/unread_count/",
         views_dashboard.unread_count_api, name="unread_count_api"),
    path("notifications/<int:pk>/read/",
         views_dashboard.mark_notification_read, name="mark_notification_read"),
    path("notifications/<int:pk>/delete/",
         views_dashboard.delete_notification, name="delete_notification"),

    # --- 通知ログ（管理者） ---
    path("admin/notifications/", views_admin_notifications.notification_log_list,
         name="admin_notification_log"),
    path("admin/notifications/<int:log_id>/",
         views_admin_notifications.notification_log_detail, name="admin_notification_detail"),

    # --- エラーログ（管理者） ---
    path("admin/error_logs/", views_admin_notifications.error_logs, name="error_logs"),

    # --- ダッシュボード ---
    path("dashboard/<int:pk>/", views_dashboard.product_dashboard,
         name="product_dashboard"),
]
