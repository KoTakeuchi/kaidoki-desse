
from .models import Product
from .price_logic import update_stock_status
import requests, time

def update_all_stock_from_api():
    """全商品に対して在庫情報をAPI経由で更新"""
    products = Product.objects.all()
    for product in products:
        try:
            # 仮APIエンドポイント例
            api_url = f"https://api.rakuten.co.jp/item?url={product.product_url}"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                api_data = response.json()
                update_stock_status(product, api_data)
            time.sleep(0.5)  # API負荷対策
        except Exception as e:
            print(f"[Error] {product.product_name}: {e}")
