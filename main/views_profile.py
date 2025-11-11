from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileForm


@login_required
def profile_view(request):
    """ユーザー情報編集"""
    user = request.user

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "ユーザー情報を更新しました。")
            return redirect("main:user_edit")
        else:
            messages.error(request, "入力内容に誤りがあります。")
    else:
        # ✅ instance=user を指定して初期値をセット
        form = ProfileForm(instance=user)

    return render(request, "user/user_edit.html", {"form": form})


@login_required
def account_delete_view(request):
    """アカウント削除（退会処理）"""
    if request.method == "POST":
        user = request.user
        username = user.username
        user.delete()
        messages.warning(request, f"アカウント「{username}」を削除しました。")
        return redirect("main:landing")

    return render(request, "user/account_delete.html")
