# 実行ディレクトリ: I:\school\kaidoki-desse\main\utils\pagination_helper.py
from django.core.paginator import Paginator


def paginate_queryset(request, queryset, per_page=20, context_name="page_obj"):
    """
    任意のクエリセットをページネーション処理する共通関数。
    戻り値: (page_obj, paginator)
    """
    try:
        per_page = int(request.GET.get("per_page", per_page))
    except (TypeError, ValueError):
        per_page = 20

    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj, paginator
