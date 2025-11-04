from django.shortcuts import render, redirect
# ----------------------------------------
# トップページ / LP
# ----------------------------------------


def landing_page(request):
    """未ログイン時のトップページ"""
    if request.user.is_authenticated:
        return redirect("main:product_list")
    # ▼ テンプレート名を正しく（layout-landing.html）
    return render(request, "layout-landing.html")

# ----------------------------------------
# ログイン / ログアウト / サインアップ
# ----------------------------------------
