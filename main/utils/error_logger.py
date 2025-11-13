# --- START: main/utils/error_logger.py ---

import traceback
import logging
from django.utils import timezone
from main.models import ErrorLog

# Django 標準ロガー
logger = logging.getLogger(__name__)


def log_error(user=None, type_name=None, source=None, err=None):
    """
    エラーログをDBと標準ログに記録する。
    user:     エラー発生時のユーザー（匿名可）
    type_name: 例外クラス名 (例: ValueError)
    source:   発生箇所（例: 'product_list', 'fetch_rakuten_item_data'）
    err:      実際の例外オブジェクト
    """

    try:
        # --- スタックトレース ---
        tb = "".join(traceback.format_exception(
            None, err, err.__traceback__)) if err else "(No traceback)"

        # --- 標準ログ出力 ---
        logger.error(f"[{source}] {type_name}: {err}\n{tb}")

        # --- DB保存（ErrorLogモデル） ---
        ErrorLog.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            type_name=type_name or "UnknownError",
            source=source or "unspecified",
            message=f"{err}\n\n{tb}",
            created_at=timezone.now(),
        )

    except Exception as e:
        # DBへの書き込みに失敗してもプロセスを止めない
        logger.critical(f"[log_error] Failed to log error: {e}")
