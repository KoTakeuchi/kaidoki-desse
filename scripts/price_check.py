from main.models import Product, PriceHistory
from decimal import Decimal

print("=== 買い時チェック ログ出力 ===")

products = Product.objects.all()
print(f"登録商品数: {len(products)} 件")

for idx, p in enumerate(products, start=1):
    print(f"\n[{idx}] 商品名: {p.product_name}")

    # 修正点：order_by('-checked_at') に変更
    latest_price_record = PriceHistory.objects.filter(product=p).order_by('-checked_at').first()
    if not latest_price_record:
        print("  ⚠ 価格履歴なし → スキップ")
        continue

    current_price = latest_price_record.price
    threshold_price = p.threshold_price
    stock = latest_price_record.stock_count  # 修正点：stock_count に変更

    print(f"  現在価格: {current_price}円")
    print(f"  買い時価格: {threshold_price}円")
    print(f"  在庫: {stock}")

    if threshold_price is None:
        print("  ⚠ 閾値未設定 → 判定スキップ")
        continue

    if Decimal(current_price) <= Decimal(threshold_price):
        print("  ✅ 買い時条件を満たしました！")
    else:
        print("  ❌ 条件未達。買い時ではありません。")

print("\n=== チェック完了 ===")
