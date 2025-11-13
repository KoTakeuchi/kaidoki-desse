# 実行ディレクトリ: I:\school\kaidoki-desse\main\views_flag.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from main.models import UserNotificationSetting
from main.utils.error_logger import log_error


# ======================================================
# 通知設定ページ（GET表示＋AJAX保存対応）
# ======================================================
@login_required
def flag_setting(request):
    """
    通知設定ページ表示
    - GET: 設定画面を表示
    - POST: 通知設定を更新（AJAX）
    """
    try:
        # --- 設定の取得（存在しない場合は作成） ---
        setting, _ = UserNotificationSetting.objects.get_or_create(
            user=request.user)

        if request.method == "POST":
            # ----------------------------
            # POSTデータで更新
            # ----------------------------
            email_notify = request.POST.get("email_notify") == "true"
            price_notify = request.POST.get("price_notify") == "true"
            stock_notify = request.POST.get("stock_notify") == "true"

            setting.email_notify = email_notify
            setting.price_notify = price_notify
            setting.stock_notify = stock_notify
            setting.save()

            return JsonResponse({"success": True, "message": "通知設定を保存しました。"})

        # ----------------------------
        # GET: 通知設定画面を表示
        # ----------------------------
        context = {"setting": setting}
        return render(request, "main/flag_setting.html", context)

    except Exception as e:
        log_error(
            user=request.user,
            type_name=type(e).__name__,
            source="flag_setting",
            err=e,
        )
        if request.method == "POST":
            return JsonResponse({"error": str(e)}, status=500)
        raise


# ======================================================
# API: 通知設定の取得（AJAX用）
# ======================================================
@login_required
@require_http_methods(["GET"])
def api_get_flag_setting(request):
    """通知設定をJSONで返す"""
    try:
        setting, _ = UserNotificationSetting.objects.get_or_create(
            user=request.user)
        return JsonResponse({
            "email_notify": setting.email_notify,
            "price_notify": setting.price_notify,
            "stock_notify": setting.stock_notify,
        })
    except Exception as e:
        log_error(user=request.user, type_name=type(e).__name__,
                  source="api_get_flag_setting", err=e)
        return JsonResponse({"error": str(e)}, status=500)


# ======================================================
# API: 通知設定の更新（AJAX用）
# ======================================================
@login_required
@require_http_methods(["POST"])
def api_update_flag_setting(request):
    """通知設定を更新"""
    try:
        setting, _ = UserNotificationSetting.objects.get_or_create(
            user=request.user)
        setting.email_notify = request.POST.get("email_notify") == "true"
        setting.price_notify = request.POST.get("price_notify") == "true"
        setting.stock_notify = request.POST.get("stock_notify") == "true"
        setting.save()
        return JsonResponse({"success": True})
    except Exception as e:
        log_error(user=request.user, type_name=type(e).__name__,
                  source="api_update_flag_setting", err=e)
        return JsonResponse({"error": str(e)}, status=500)
