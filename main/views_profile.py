from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import ProfileForm


@login_required
def profile_view(request):
    """プロフィール表示・編集ページ"""
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "プロフィールを更新しました。")
            return redirect("main:profile")
        else:
            messages.error(request, "入力内容に誤りがあります。")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "user/profile.html", {"form": form})


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
