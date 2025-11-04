# 実行ディレクトリ: I:\school\kaidoki-desse\main\utils\rakuten_api.py
import requests
from urllib.parse import urlparse
from main.utils.error_logger import log_error


def fetch_rakuten_item(url: str):
    """
    楽天商品URLから商品情報を取得
    - URL解析 → ショップコード・商品コード抽出
    - 楽天APIで検索
    - 商品名・価格・画像URLなどを返却
    """
    print(f"[View] Fetching Rakuten item for URL: {url}")
    try:
        parsed = urlparse(url)
        if not parsed.netloc.endswith("rakuten.co.jp"):
            raise ValueError("楽天市場のURLではありません")

        # --- URLからshopCode / itemCode抽出 ---
        # 例: https://item.rakuten.co.jp/darkangel/tp2308-3754v2/
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError("URL形式が不正です（shopCode, itemCode 解析不可）")

        shop_code = path_parts[1] if path_parts[0] == "item.rakuten.co.jp" else path_parts[0]
        item_code = path_parts[1]
        full_code = f"{shop_code}:{item_code}"

        print(f"[RakutenAPI] Try itemCode: {full_code}")

        # --- APIリクエスト ---
        endpoint = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"
        params = {
            "applicationId": "1016082687225252652",  # 公開用テストアプリID
            "itemCode": full_code,
            "format": "json",
            "hits": 1,
        }

        res = requests.get(endpoint, params=params)
        data = res.json()

        # --- API異常応答 ---
        if res.status_code != 200 or "Items" not in data or len(data["Items"]) == 0:
            print(f"[RakutenAPI] Response: {res.status_code}")
            print("[RakutenAPI] Fallback → keyword search")

            # --- Fallback: itemNameから検索 ---
            params_fallback = {
                "applicationId": "1016082687225252652",
                "keyword": item_code,
                "format": "json",
                "hits": 1,
            }
            res = requests.get(endpoint, params=params_fallback)
            data = res.json()

            if res.status_code != 200 or "Items" not in data or len(data["Items"]) == 0:
                print("[RakutenAPI] No items found, returning empty defaults")
                return {
                    "product_name": "",
                    "shop_name": "",
                    "regular_price": "",
                    "initial_price": "",
                    "image_url": "",
                }

        # --- 商品データ取得 ---
        item = data["Items"][0]["Item"]

        # --- 高画質画像を優先 ---
        image_url = (
            item.get("largeImageUrls", [{}])[0].get("imageUrl")
            or item.get("mediumImageUrls", [{}])[0].get("imageUrl")
        )

        # ✅ 強制的に高解像度に変換（CDNパラメータ上書き）
        if image_url and "_ex=" in image_url:
            image_url = (
                image_url.replace("_ex=300x300", "_ex=600x600")
                .replace("_ex=128x128", "_ex=600x600")
                .replace("_ex=200x200", "_ex=600x600")
            )

        # --- レスポンス整形 ---
        result = {
            "product_name": item.get("itemName", ""),
            "shop_name": f"{item.get('shopName', '')}（{item.get('shopCode', '')}）",
            "regular_price": item.get("itemPrice", ""),
            "initial_price": item.get("itemPrice", ""),
            "image_url": image_url,
        }

        print(f"[RakutenAPI] Success: {result['product_name'][:80]}...")
        print(f"[RakutenAPI] Image URL: {image_url}")

        return result

    except Exception as e:
        print(f"[RakutenAPI] ❌ Exception: {type(e).__name__} - {e}")
        log_error(
            user=None,
            type_name=type(e).__name__,
            source="fetch_rakuten_item",
            err=e,
        )
        return {
            "error": f"楽天APIで商品情報を取得できませんでした: {str(e)}",
            "product_name": "",
            "shop_name": "",
            "regular_price": "",
            "initial_price": "",
            "image_url": "",
        }
