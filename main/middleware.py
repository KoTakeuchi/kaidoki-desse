from django.template.loader import render_to_string
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from main.models import ErrorLog
import traceback


class ErrorLoggingMiddleware:
    """Django5対応：例外を捕捉してDB保存＋メール送信"""

    def __init__(self, get_response):
        self.get_response = get_response
        print("[ErrorLoggingMiddleware] 初期化完了")

    def __call__(self, request):
        # Django にリクエストを渡すだけ（例外処理は process_exception に委譲）
        print("[ErrorLoggingMiddleware] 呼び出し開始")
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """view 実行中に発生した例外を捕捉"""
        print("[ErrorLoggingMiddleware] process_exception 発火")

        detail = traceback.format_exc()
        try:
            # ユーザー情報
            user = (
                request.user.username
                if getattr(request, "user", None) and request.user.is_authenticated
                else "未ログイン"
            )

            # DB登録
            ErrorLog.objects.create(
                user=None if user == "未ログイン" else request.user,
                type=type(exception).__name__,
                source=request.path,
                detail=detail,
                occurred_at=now(),
            )

            # メール本文
            context = {
                "type": type(exception).__name__,
                "url": request.build_absolute_uri(),
                "user": user,
                "time": now().strftime("%Y-%m-%d %H:%M:%S"),
                "detail": detail,
            }
            message = render_to_string(
                "emails/error_notification.txt", context)

            # メール送信
            send_mail(
                subject=f"[Kaidoki-Desse] エラー発生通知: {context['type']}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )

            print(f"[ErrorLoggingMiddleware] 管理者メール送信完了 ({context['type']})")

        except Exception as log_error:
            print(f"[ErrorLoggingMiddleware] 保存または送信失敗: {log_error}")

        # Django標準の500レスポンス処理を続行
        return None
