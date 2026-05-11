# main/views_profile.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib import messages
from main.forms import UserProfileForm, PasswordChangeCustomForm
from main.utils.error_logger import log_error


@login_required
def profile_view(request):
    """ユーザー情報編集ページ"""
    try:
        email_form = UserProfileForm(instance=request.user)
        password_form = PasswordChangeCustomForm(user=request.user)

        if request.method == "POST":
            action = request.POST.get("action")

            if action == "email":
                email_form = UserProfileForm(
                    request.POST, instance=request.user)
                if email_form.is_valid():
                    email_form.save()
                    messages.success(request, "メールアドレスを更新しました。")
                    return redirect("main:user_edit")
                else:
                    messages.error(request, "入力内容に誤りがあります。")

            elif action == "password":
                password_form = PasswordChangeCustomForm(
                    user=request.user, data=request.POST
                )
                if password_form.is_valid():
                    password_form.save()
                    update_session_auth_hash(request, password_form.user)
                    messages.success(request, "パスワードを変更しました。")
                    return redirect("main:user_edit")
                else:
                    messages.error(request, "パスワードの変更に失敗しました。")

        return render(request, "main/profile_edit.html", {
            "email_form": email_form,
            "password_form": password_form,
        })

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
