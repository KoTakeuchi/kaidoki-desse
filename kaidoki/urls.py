# 実行ディレクトリ: I:\school\kaidoki-desse\kaidoki\urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from main import views

urlpatterns = [
    # --- トップページ（mainのlanding_pageへリダイレクト） ---
    path("", lambda request: redirect("main:landing_page"), name="root"),

    # --- 管理画面 ---
    path("admin/", admin.site.urls),

    # --- main配下（商品・カテゴリ・通知など） ---
    path("main/", include("main.urls")),

    # --- トップ直下のログイン・サインアップ ---
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.signup_view, name="signup"),

    # --- パスワードリセット ---
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="auth/password_reset.html"
        ),
        name="password_reset",
    ),
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
]

# --- メディアファイル設定 ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
