# 実行ディレクトリ: I:\school\kaidoki-desse\main\utils\rakuten_api.py
import re
import requests
from django.conf import settings


def fetch_rakuten_item(rakuten_url):
    """
    楽天商品URLから商品情報を取得
    - itemCode検索が失敗したら keyword検索に自動フォールバック
    - 定価は説明文から抽出（見つからなければ販売価格を使用）
    """
    try:
        # URLからshopCodeとitemCode抽出
        match = re.search(
            r"item\.rakuten\.co\.jp/([^/]+)/([^/?#]+)", rakuten_url)
        if not match:
            return {"error": "楽天市場の商品URL形式ではありません。"}
        shop_code, item_code = match.groups()

        app_id = getattr(settings, "RAKUTEN_APP_ID", None)
        if not app_id:
            return {"error": "RAKUTEN_APP_ID が設定されていません。"}

        endpoint = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"

        # --- ① itemCode検索 ---
        params_primary = {
            "applicationId": app_id,
            "shopCode": shop_code,
            "itemCode": f"{shop_code}:{item_code}",
            "format": "json",
            "hits": 1,
        }
        print("[RakutenAPI] Primary Request:", endpoint, params_primary)
        res = requests.get(endpoint, params=params_primary, timeout=5)
        print("[RakutenAPI] Response:", res.status_code)

        # --- ② itemCode検索が400なら keyword検索に切り替え ---
        if res.status_code != 200:
            print("[RakutenAPI] Fallback to keyword search")
            params_keyword = {
                "applicationId": app_id,
                "keyword": item_code,
                "format": "json",
                "hits": 1,
            }
            res = requests.get(endpoint, params=params_keyword, timeout=5)
            print("[RakutenAPI] Keyword Response:", res.status_code)

        if res.status_code != 200:
            return {"error": f"楽天APIエラー: ステータスコード {res.status_code}"}

        data = res.json()
        if not data.get("Items"):
            return {"error": "商品情報が見つかりませんでした。"}

        item = data["Items"][0]["Item"]

        # --- 各項目抽出 ---
        product_name = item.get("itemName", "")
        shop_name = item.get("shopName", "")
        initial_price = item.get("itemPrice", None)
        image_url = item.get("mediumImageUrls", [{}])[0].get("imageUrl", "")

        # --- 定価（説明文から抽出） ---
        caption = (item.get("catchcopy", "") or "") + \
            " " + (item.get("itemCaption", "") or "")
        match_price = re.search(r"(定価|希望小売価格|通常価格)[^\d]*(\d{3,6})円?", caption)
        regular_price = int(match_price.group(
            2)) if match_price else initial_price

        return {
            "product_name": product_name,
            "shop_name": shop_name,
            "regular_price": regular_price,
            "initial_price": initial_price,
            "image_url": image_url,
        }

    except Exception as e:
        print("[RakutenAPI] Error:", e)
        return {"error": f"API通信エラー: {str(e)}"}
