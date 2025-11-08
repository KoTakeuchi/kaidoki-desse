# --- START: main/urls.py ---
from django.urls import path
from django.contrib.auth import views as auth_views
from main.views_auth import custom_password_reset_view

from . import (
    views,
    views_flag,
    views_profile,
    views_user,
    views_auth,
    views_api,
    views_product,
    views_category,
    views_dashboard,
)

app_name = "main"

urlpatterns = [
    # ============================================================
    # ランディング・ログアウト
    # ============================================================
    path("", views.landing_page, name="landing_page"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="main:landing_page"),
        name="logout",
    ),

    # ============================================================
    # ユーザー関連
    # ============================================================
    path("user/profile/", views_profile.profile_view, name="profile"),
    path("user/edit/", views_user.user_edit, name="user_edit"),
    path("user/delete/", views_profile.account_delete_view, name="account_delete"),

    # ============================================================
    # 認証・パスワード関連
    # ============================================================
    path("password_reset/", custom_password_reset_view, name="password_reset"),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="auth/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "after_login_redirect/",
        views_auth.after_login_redirect,
        name="after_login_redirect",
    ),

    # ============================================================
    # 商品関連
    # ============================================================
    path("product/list/", views_product.product_list, name="product_list"),
    path("product/detail/<int:pk>/",
         views_product.product_detail, name="product_detail"),
    path("product/create/", views_product.product_create, name="product_create"),
    path("product/edit/<int:pk>/", views_product.product_edit, name="product_edit"),
    path("product/delete/<int:pk>/",
         views_product.product_delete, name="product_delete"),

    # ============================================================
    # 楽天API関連
    # ============================================================
    path("api/fetch_rakuten_item/", views_api.fetch_rakuten_item,
         name="fetch_rakuten_item"),
    path("api/proxy_image/", views_api.proxy_image, name="proxy_image"),

    # ============================================================
    # カテゴリAPI関連
    # ============================================================
    path("api/categories/", views_category.api_category_list,
         name="api_category_list"),
    path("api/categories/create/", views_category.api_category_create,
         name="api_category_create"),
    path("api/categories/delete/<int:category_id>/",
         views_category.api_category_delete, name="api_category_delete"),
    path("api/categories/update/<int:category_id>/",
         views_category.api_category_update, name="api_category_update"),

    # ============================================================
    # カテゴリ管理画面
    # ============================================================
    path("categories/my/", views_category.category_my, name="category_my"),

    # ============================================================
    # 通知設定・通知関連（Dashboard統合版）
    # ============================================================
    path("flag_setting/", views_flag.flag_setting, name="flag_setting"),

    # --- 通知（一般ユーザー） ---
    path("notifications/", views_dashboard.notification_history, name="notifications"),
    path("notifications/read/<int:pk>/",
         views_dashboard.mark_notification_read, name="notification_read"),

    # --- 通知ログ ---
    path("notifications/log/", views_dashboard.notification_history,
         name="notification_log"),

    # --- ダッシュボード ---
    path("dashboard/", views_dashboard.dashboard_view, name="dashboard"),
    # --- 未読通知件 ---
    path("api/unread_count/", views_dashboard.unread_notification_count,
         name="unread_count"),


]
# --- END: main/urls.py ---
