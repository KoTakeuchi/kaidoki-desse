# ==============================================================
# ファイル名: error_logger.py
# 所在地: I:\school\kaidoki-desse\main\utils\error_logger.py
# 概要: 例外発生時に ErrorLog モデルへ安全に記録するユーティリティ
# ==============================================================

from django.utils import timezone
from main.models import ErrorLog


def log_error(user=None, type_name=None, source=None, err=None):
    """
    エラーログをデータベースに安全に記録する関数。
    未ログイン時でもクラッシュせず、print出力でフォールバックする。

    Parameters
    ----------
    user : User | None
        発生時のユーザーオブジェクト（未ログイン時はNone）
    type_name : str | None
        例外タイプ（例: ValueError）
    source : str | None
        発生箇所（例: 'product_list'）
    err : Exception | None
        実際の例外オブジェクト
    """

    try:
        # ErrorLogモデルに記録
        ErrorLog.objects.create(
            user=user,
            type_name=type_name or (
                type(err).__name__ if err else "UnknownError"),
            source=source or "unknown",
            message=str(err) if err else "(no message)",
            created_at=timezone.now(),
        )

        print(
            f"[ErrorLoggingMiddleware] ログ保存完了: "
            f"{type_name or type(err).__name__} / {source}"
        )

    except Exception as e:
        # DBに書き込めない場合も安全に出力
        print("[ErrorLoggingMiddleware] 保存または送信失敗:", e)
        print(f"[ErrorLoggingMiddleware] 元エラー: {err}")
