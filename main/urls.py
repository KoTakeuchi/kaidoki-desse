# 実行ディレクトリ: I:\school\kaidoki-desse\main\urls.py
from django.urls import path

from main import views_api
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
    views_admin,
)
from django.contrib.auth import views as auth_views
from main.views_auth import custom_password_reset_view


app_name = "main"

urlpatterns = [
    # --- ランディング ---
    path("", views.landing_page, name="landing_page"),
    # ▼ログアウト追加
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="main:landing_page"),
        name="logout",
    ),


    # --- ユーザー関連 ---
    path("user/profile/", views_profile.profile_view, name="profile"),
    path("user/edit/", views_user.user_edit, name="user_edit"),
    path("user/delete/", views_profile.account_delete_view, name="account_delete"),


    # ...パスワード関連...
    # パスワード再設定フォーム（カスタムフォームを使う）
    path("password_reset/", custom_password_reset_view, name="password_reset"),
    # 標準のビューを利用する（テンプレートを用意済みと仮定）
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="auth/password_reset_done.html"
    ), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="auth/password_reset_confirm.html"
    ), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="auth/password_reset_complete.html"
    ), name="password_reset_complete"),
    path("after_login_redirect/", views_auth.after_login_redirect,
         name="after_login_redirect"),

    # --- 商品 ---
    path("index/", views_product.product_list, name="product_list"),
    path("product/<int:pk>/", views_product.product_detail, name="product_detail"),
    path("product/create/", views_product.product_create, name="product_create"),
    path("product/edit/<int:pk>/", views_product.product_edit, name="product_edit"),
    path("product/delete/<int:pk>/",
         views_product.product_delete, name="product_delete"),

    # --- 楽天API ---
    path("api/fetch_rakuten_item/", views_api.fetch_rakuten_item,
         name="fetch_rakuten_item"),
    path("api/proxy_image/", views_api.proxy_image, name="proxy_image"),
    path("api/categories/", views_category.api_category_list,
         name="api_category_list"),
    path("api/categories/create/", views_category.api_category_create,
         name="api_category_create"),
    # カテゴリ削除API
    path("api/categories/delete/<int:category_id>/",
         views_category.api_category_delete, name="api_category_delete"),
    # カテゴリ編集API
    path("api/categories/update/<int:category_id>/",
         views_category.api_category_update, name="api_category_update"),

    # --- カテゴリ ---
    path("categories/my/", views_category.category_my, name="category_my"),

    # --- 通知設定 ---
    path("flag_setting/", views_flag.flag_setting, name="flag_setting"),

    # --- 通知（一般ユーザー） ---
    path("notifications/", views_dashboard.notification_list, name="notifications"),
    path("notifications/<str:pk>/read/",
         views_dashboard.mark_notification_read, name="mark_notification_read"),
    path("unread_count_api/", views_dashboard.unread_count_api,
         name="unread_count_api"),

    # --- 通知ログ ---
    path("notifications/log/", views_dashboard.notification_log_list,
         name="notification_log"),




    # --- 管理者用 ---
    path("admin/dashboard/", views_admin.admin_dashboard, name="admin_dashboard"),
    path("admin/users/", views_admin.admin_user_list, name="admin_user_list"),
    path("admin/products/", views_admin.admin_product_list,
         name="admin_product_list"),
    path("admin/categories/", views_admin.admin_categories,
         name="admin_categories"),  # ← これを追加
    path("admin/notifications/", views_admin.admin_notification_list,
         name="admin_notifications"),
    path("admin/notifications/<int:log_id>/",
         views_admin.admin_notification_detail, name="admin_notification_detail"),
    path("admin/error_logs/", views_admin.admin_error_logs, name="admin_error_logs"),

]
