# 実行ディレクトリ: I:\school\kaidoki-desse\main\management\commands\check_stock.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from main.models import Product, ErrorLog
from main import price_logic
import logging
import time

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "全ユーザーの全商品を楽天APIでチェックし、在庫状態を更新します。"

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(self.style.SUCCESS(
            f"[{start_time:%Y-%m-%d %H:%M:%S}] 在庫チェック開始"))

        total_products = Product.objects.count()
        total_users = User.objects.count()
        success_count, fail_count, skipped_count = 0, 0, 0

        for user in User.objects.all():
            self.stdout.write(self.style.HTTP_INFO(
                f"--- ユーザー: {user.username} ---"))
            products = Product.objects.filter(user=user)
            total_user_products = products.count()

            for idx, product in enumerate(products, start=1):
                try:
                    # 🔸 検索文字数チェック（英数字1文字の場合はスキップ）
                    if not product.product_name or len(product.product_name.strip()) < 2:
                        self.stdout.write(
                            f"({idx}/{total_user_products}) {product.product_name} → スキップ（検索語が短すぎ）"
                        )
                        skipped_count += 1
                        continue

                    api_data = price_logic.mock_fetch_rakuten_product_data(
                        product.product_name, user=user)
                    price_logic.update_stock_status(product, api_data)
                    success_count += 1
                    self.stdout.write(
                        f"({idx}/{total_user_products}) {product.product_name} 更新完了")
                    time.sleep(1)  # API呼び出し間隔（レート制限対策）

                except Exception as e:
                    fail_count += 1
                    msg = f"[BatchStockError] {product.id}: {e}"
                    logger.error(msg)
                    ErrorLog.objects.create(
                        user=user,
                        type="BatchStockError",
                        source="check_stock_command",
                        detail=str(e),
                    )

        end_time = timezone.now()
        elapsed = (end_time - start_time).total_seconds()

        summary = (
            f"\n[完了] 全{total_users}ユーザー / {total_products}商品 を処理\n"
            f"成功: {success_count} 件 / 失敗: {fail_count} 件 / スキップ: {skipped_count} 件\n"
            f"処理時間: {elapsed:.1f} 秒"
        )

        logger.info(summary)
        self.stdout.write(self.style.SUCCESS(summary))
