from django.contrib import messages  # ✅ ← 正しいインポート
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from main.forms import CustomPasswordResetForm, CustomUserCreationForm


def login_view(request):
    """ログイン処理"""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "ログインしました。")
            return redirect("main:product_list")
        else:
            messages.error(request, "ログイン情報が正しくありません。")
    else:
        form = AuthenticationForm()

    return render(request, "auth/login.html", {"form": form})


def logout_view(request):
    """ログアウト処理"""
    logout(request)
    messages.info(request, "ログアウトしました。")
    return redirect("main:landing_page")  # ✅ URL名が正しいか再確認（例: main:loginでもOK）


def signup_view(request):
    """新規登録処理（メール必須版・エラーハンドリング改良）"""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "登録が完了しました。ようこそ、買い時でっせへ！")
            return redirect("main:product_list")
        else:
            messages.error(request, "入力内容に誤りがあります。ご確認ください。")
    else:
        form = CustomUserCreationForm()

    return render(request, "auth/signup.html", {"form": form})


@login_required
def after_login_redirect(request):
    """既存参照がある場合の保険"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect("admin_app:admin_dashboard")
    return redirect("main:product_list")


def role_based_login_view(request):
    """ログイン成功後の遷移先をユーザー権限で振り分け"""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("admin_app:admin_dashboard")
        return redirect("main:product_list")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect("admin_app:admin_dashboard")
            return redirect("main:product_list")
    else:
        form = AuthenticationForm()

    return render(request, "auth/login.html", {"form": form})


def custom_password_reset_view(request):
    """HTMLメール対応パスワード再設定ビュー"""
    if request.method == "POST":
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            users = User.objects.filter(email=email)

            if users.exists():
                for user in users:
                    subject = render_to_string(
                        "auth/password_reset_subject.txt").strip()
                    context = {
                        "email": user.email,
                        "domain": request.get_host(),
                        "site_name": "買い時でっせ",
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        "token": default_token_generator.make_token(user),
                        "protocol": "https" if request.is_secure() else "http",
                    }

                    html_message = render_to_string(
                        "auth/password_reset_email.html", context)
                    text_message = (
                        f"{user.username} 様\n\n"
                        f"以下のリンクからパスワードを再設定してください：\n"
                        f"{context['protocol']}://{context['domain']}/reset/{context['uid']}/{context['token']}/\n\n"
                        "このメールに心当たりがない場合は破棄してください。"
                    )

                    email_msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[user.email],
                    )
                    email_msg.attach_alternative(html_message, "text/html")
                    email_msg.send(fail_silently=False)

            return redirect("password_reset_done")

    else:
        form = CustomPasswordResetForm()

    return render(request, "auth/password_reset.html", {"form": form})
