# --- main/views_notifications.py ---
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def unread_count_api(request):
    """未読通知件数を返すAPI（仮実装）"""
    # 通知モデルが未実装の場合は固定値を返す
    return JsonResponse({"unread_count": 0})
