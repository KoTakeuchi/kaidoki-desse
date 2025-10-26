# 実行ディレクトリ: D:\school\kaidoki-desse
# ファイル: main\views_test.py

from django.http import JsonResponse

def raise_test_error(request):
    # わざとエラーを発生させる
    1 / 0
    return JsonResponse({"status": "ok"})
