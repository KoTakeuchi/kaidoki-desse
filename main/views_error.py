# 実行ディレクトリ: I:\school\kaidoki-desse
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from main.models import ErrorLog

# ✅ 管理者チェック


def is_admin(user):
    return user.is_superuser  # 管理者（admin）専用

# ----------------------------------------
# エラーログ一覧（管理者専用）
# ----------------------------------------


@user_passes_test(is_admin)
@login_required
def error_logs(request):
    logs = ErrorLog.objects.select_related("user").order_by("-occurred_at")
    paginator = Paginator(logs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "main/error_list.html", {"logs": page_obj})
