from django.contrib.auth import authenticate, login
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
from main.forms import CustomPasswordResetForm


# ----------------------------------------
# ロール別ログインビュー（関数ベース）
# ----------------------------------------
def role_based_login_view(request):
    """ログイン成功後の遷移先をユーザー権限で振り分け"""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("main:admin_dashboard")
        return redirect("main:product_list")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect("main:admin_dashboard")
            return redirect("main:product_list")
    else:
        form = AuthenticationForm()

    return render(request, "auth/login.html", {"form": form})


# ----------------------------------------
# ログイン後の保険的リダイレクト
# ----------------------------------------
@login_required
def after_login_redirect(request):
    """既存参照がある場合の保険"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect("main:admin_dashboard")
    return redirect("main:product_list")


# ----------------------------------------
# パスワード再設定ビュー（HTMLメール対応版）
# ----------------------------------------
def custom_password_reset_view(request):
    """
    Django標準 PasswordResetView を関数化＋HTMLメール対応。
    未登録メールは CustomPasswordResetForm でバリデーション。
    """
    if request.method == "POST":
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            users = User.objects.filter(email=email)

            if users.exists():
                for user in users:
                    # 件名テンプレート
                    subject = render_to_string(
                        "auth/password_reset_subject.txt"
                    ).strip()

                    # 本文テンプレート（HTML版）
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
                        "auth/password_reset_email.html", context
                    )

                    # テキスト版（保険）
                    text_message = (
                        f"{user.username} 様\n\n"
                        f"以下のリンクからパスワードを再設定してください：\n"
                        f"{context['protocol']}://{context['domain']}/reset/{context['uid']}/{context['token']}/\n\n"
                        "このメールに心当たりがない場合は破棄してください。"
                    )

                    # メール送信（HTML＋テキスト両対応）
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
