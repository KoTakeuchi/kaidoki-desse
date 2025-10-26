# 実行ディレクトリ: I:\school\kaidoki-desse\main\utils\error_logger.py
from main.models import ErrorLog


def log_error(user, type_name, source, err):
    """
    アプリ全体で共通利用するエラーロガー。
    例外内容を ErrorLog テーブルに記録する。

    Parameters
    ----------
    user : User or None
        ログイン中のユーザー（未ログインの場合は None）。
    type_name : str
        例外の種類（例: ValueError, TypeError）。
    source : str
        エラー発生元の識別子（関数名や処理名など）。
    err : Exception
        発生した例外オブジェクト。
    """
    try:
        ErrorLog.objects.create(
            user=user,                # 未ログインなら None を許可（null=True）
            type_name=type_name,
            source=source,
            message=str(err),
        )
    except Exception as e:
        # ログ記録自体の失敗は無視して出力だけ行う
        print(f"⚠️ [log_error] DB書き込みに失敗: {e}")
        print(f"　┗ 元の例外: {type_name} @ {source} - {err}")
