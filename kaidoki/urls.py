from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from main import views
from main.views_auth import role_based_login_view, custom_password_reset_view
from django.contrib.auth import views as auth_views


# --- トップページ ---
def landing_page(request):
    """トップのランディングページ"""
    return render(request, "layout-landing.html")


urlpatterns = [
    # --- トップページ ---
    path("", landing_page, name="landing_page"),

    # --- 新規登録 ---
    path("signup/", views.signup_view, name="signup"),

    # --- 管理画面 ---
    path("admin/", admin.site.urls),

    # --- main配下（商品・カテゴリ・通知など） ---
    path("main/", include("main.urls")),

    # --- REST APIルート（商品・カテゴリ・楽天API など） ---
    path("api/", include("main.urls_api")),  # ✅ これを追加

    # --- ログイン ---
    path("login/", role_based_login_view, name="login"),

    # --- ログアウト ---
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="landing_page"),
        name="logout",
    ),

    # --- パスワードリセット ---
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
]


# --- メディアファイル設定 ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

# --- 静的ファイル設定（★追加）---
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATICFILES_DIRS[0])
