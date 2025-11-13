

# def unread_count(request):
#     if not request.user.is_authenticated:
#         return {}
#     count = Notification.objects.filter(
#         user=request.user, is_read=False).count()
#     return {"unread_count": count}


def common_context(request):
    """全テンプレート共通のコンテキスト"""
    return {
        # 'unread_notifications': Notification.objects.filter(is_read=False).count(),
        'unread_notifications': 0  # 仮置き
    }
