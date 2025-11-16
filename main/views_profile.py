# main/views_profile.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from main.forms import UserProfileForm
from main.utils.error_logger import log_error


@login_required
def profile_view(request):
    """ユーザー情報編集ページ"""
    try:
        if request.method == "POST":
            form = UserProfileForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "ユーザー情報を更新しました。")
                return redirect("main:user_edit")
            else:
                messages.error(request, "入力内容に誤りがあります。")
        else:
            form = UserProfileForm(instance=request.user)

        return render(request, "main/profile_edit.html", {"form": form})

    except Exception as e:
        log_error(
            user=request.user,
            type_name=type(e).__name__,
            source="profile_view",
            err=e,
        )
        messages.error(request, "ユーザー情報の読み込み中にエラーが発生しました。")
        return redirect("main:product_list")


@login_required
def account_delete_view(request):
    """アカウント削除（論理削除）"""
    try:
        if request.method == "POST":
            user = request.user

            # ✅ 論理削除（is_active = False）
            user.is_active = False
            user.save(update_fields=["is_active"])

            messages.success(request, "アカウントを削除しました。ご利用ありがとうございました。")
            logout(request)
            return redirect("main:landing_page")

        return render(request, "main/account_delete_confirm.html")

    except Exception as e:
        log_error(
            user=request.user,
            type_name=type(e).__name__,
            source="account_delete_view",
            err=e,
        )
        messages.error(request, "アカウント削除中にエラーが発生しました。")
        return redirect("main:product_list")
