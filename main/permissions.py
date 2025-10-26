# main/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnlyCategory(BasePermission):
    """
    カテゴリ用の権限:
      - GET/HEAD/OPTIONS は誰でも可（認証は別途設定）
      - 書き込み系は「独自カテゴリ & 所有者のみ」許可
      - 共通カテゴリ（is_global=True, user=None）は READ ONLY
    """
    def has_object_permission(self, request, view, obj):
        # 読み取りは常にOK（認証はView側でIsAuthenticatedを併用）
        if request.method in SAFE_METHODS:
            return True

        # 共通カテゴリは書き込み不可
        if getattr(obj, "is_global", False):
            return False

        # 独自カテゴリは所有者のみ書き込み可
        return getattr(obj, "user_id", None) == getattr(request.user, "id", None)
