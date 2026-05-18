# main/management/commands/update_prices.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import Product, PriceHistory
from main.utils.rakuten_api import fetch_rakuten_item
from main.utils.flag_checker import update_flag_status
# 変更後
from main.utils.notify_events import create_restock_event, create_stock_few_event, create_stock_none_event
import time


class Command(BaseCommand):
    """
    ✅ 楽天APIから実際の価格・在庫を取得して更新
    実行例: python manage.py update_prices
    実行例（優先度指定）: python manage.py update_prices --priority=高
    """

    help = "楽天APIから最新価格・在庫を取得してDBに保存"

    def add_arguments(self, parser):
        parser.add_argument(
            "--priority",
            type=str,
            default="all",
            choices=["高", "普通", "all"],
            help="更新対象の優先度（高/普通/all）",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🔄 価格更新バッチを開始します..."))

        priority = options["priority"]

        # 対象商品を取得
        queryset = Product.objects.filter(is_deleted=False)
        if priority != "all":
            queryset = queryset.filter(priority=priority)

        total_count = queryset.count()
        self.stdout.write(f"📊 対象商品数: {total_count}件")

        if total_count == 0:
            self.stdout.write(self.style.WARNING("⚠️ 更新対象の商品がありません"))
            return

        success_count = 0
        error_count = 0

        for index, product in enumerate(queryset, 1):
            try:
                self.stdout.write(
                    f"\n[{index}/{total_count}] {product.product_name}")

                # ✅ テストデータをスキップ
                if "example.com" in product.product_url or "test" in product.product_url.lower():
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠️ テストデータのためスキップ"))
                    continue

                # ✅ レート制限対策（2秒待機）
                if index > 1:
                    time.sleep(2)

                # 楽天APIから取得
                data = fetch_rakuten_item(product.product_url)

                if data.get("error"):
                    self.stdout.write(self.style.ERROR(
                        f"  ❌ API取得失敗: {data['error']}"))
                    error_count += 1
                    continue

                # 価格・在庫の取得
                new_price = data.get("initial_price", 0)
                new_stock = self._parse_stock(data.get("stock_status", "在庫あり"))

                if not new_price or new_price == 0:
                    self.stdout.write(self.style.WARNING(
                        f"  ⚠️ 価格情報が取得できませんでした"))
                    error_count += 1
                    continue

                # 前回の在庫状態を取得
                previous_history = PriceHistory.objects.filter(
                    product=product).order_by("-checked_at").first()
                previous_stock = previous_history.stock_count if previous_history else 0

                # PriceHistoryに保存
                PriceHistory.objects.create(
                    product=product,
                    price=new_price,
                    stock_count=new_stock,
                    checked_at=timezone.now()
                )

                # 最新価格・在庫を更新
                product.latest_price = new_price
                product.latest_stock_count = new_stock
                product.is_in_stock = new_stock > 0
                product.save(update_fields=[
                             "latest_price", "latest_stock_count", "is_in_stock"])

                # 買い時フラグ更新
                update_flag_status(product)

                # ✅ 在庫変化通知（優先度「高」のみ）
                if product.priority == "高":
                    # 在庫なし → 在庫あり（復活）
                    if previous_stock == 0 and new_stock > 0:
                        create_restock_event(product, product.user)
                        self.stdout.write(self.style.SUCCESS(f"  🔔 在庫復活通知"))

                    # 在庫あり → 在庫わずか
                    elif previous_stock > 1 and new_stock == 1:
                        create_stock_few_event(product, product.user)
                        self.stdout.write(self.style.SUCCESS(f"  🔔 在庫わずか通知"))

                    # 在庫あり/わずか → 在庫なし
                    elif previous_stock > 0 and new_stock == 0:
                        create_stock_none_event(product, product.user)
                        self.stdout.write(self.style.SUCCESS(f"  🔔 売り切れ通知"))

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ 更新完了: ¥{new_price:,} / 在庫 {new_stock}個")
                )
                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ エラー: {e}"))
                error_count += 1

        # 結果サマリー
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"✅ 成功: {success_count}件"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"❌ エラー: {error_count}件"))
        self.stdout.write("="*50)

    # 修正後
    def _parse_stock(self, stock_status):
        stock_status = str(stock_status)
        if "売り切れ" in stock_status or "在庫なし" in stock_status or "0" == stock_status:
            return 0
        elif "わずか" in stock_status or "残り少" in stock_status:
            return 1
        else:
            return 3
