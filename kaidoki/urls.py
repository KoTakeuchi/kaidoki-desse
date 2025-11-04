from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

# 自作ビュー
from main import views, views_auth  # ✅ main配下の2つを正しく読み込む
from django.contrib.auth import views as auth_views  # ✅ Django標準AuthViewsを別名で

# --- トップページ ---


def landing_page(request):
    """トップのランディングページ"""
    return render(request, "layout-landing.html")


urlpatterns = [
    # --- トップページ ---
    path("", landing_page, name="landing_page"),

    # --- ログイン／ログアウト／サインアップ ---
    path("login/", views_auth.role_based_login_view, name="login"),
    path("logout/", views_auth.logout_view, name="logout"),
    path("signup/", views_auth.signup_view, name="signup"),

    # --- パスワードリセット ---
    path("password_reset/", views_auth.custom_password_reset_view,
         name="password_reset"),
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

    # --- main配下（商品・カテゴリ・通知など） ---
    path("main/", include("main.urls")),  # ユーザー用

    # --- 管理者ページ（自作） ---
    path("admin_app/", include("admin_app.urls")),

    # --- Django標準管理画面 ---
    path("admin/", admin.site.urls),

    # --- REST APIルート ---
    path("api/", include("main.urls_api")),
]


# --- メディアファイル設定 ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

# --- 静的ファイル設定 ---
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATICFILES_DIRS[0])
