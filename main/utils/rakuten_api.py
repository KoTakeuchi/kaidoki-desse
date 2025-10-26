# ==============================================================
# ファイル名: rakuten_api.py
# 所在地: I:\school\kaidoki-desse\main\utils\rakuten_api.py
# 概要: 楽天APIから商品情報を取得してJSON形式で返す
# ==============================================================

import requests
from django.conf import settings


def fetch_rakuten_data(item_url: str):
    """
    楽天市場の商品URLから商品情報を取得する。
    戻り値は product_name / shop_name / itemPrice / image_url を含む辞書。
    """
    try:
        base_url = settings.RAKUTEN_BASE_URL
        app_id = settings.RAKUTEN_APP_ID

        # --- URLから itemCode 抽出 ---
        # 例: https://item.rakuten.co.jp/nissoplus/np-brl23e/
        import re
        m = re.search(r"rakuten\.co\.jp/([^/]+)/([^/?#]+)", item_url)
        if not m:
            return {"error": "URL形式が不正です。"}
        shop_code, item_code = m.groups()
        item_code_full = f"{shop_code}:{item_code}"

        print(
            f"[RakutenAPI] Primary Request: {base_url} {{'applicationId': '{app_id}', 'shopCode': '{shop_code}', 'itemCode': '{item_code_full}'}}")

        # --- ① itemCode指定で検索 ---
        params = {
            "applicationId": app_id,
            "shopCode": shop_code,
            "itemCode": item_code_full,
            "format": "json",
            "hits": 1,
        }
        r = requests.get(base_url, params=params)
        print(f"[RakutenAPI] Response: {r.status_code}")

        # --- 成功時 ---
        if r.status_code == 200:
            data = r.json()
            if data.get("Items"):
                item = data["Items"][0]["Item"]
                return {
                    "product_name": item.get("itemName"),
                    "shop_name": item.get("shopName"),
                    "itemPrice": item.get("itemPrice"),
                    "image_url": item.get("mediumImageUrls", [{}])[0].get("imageUrl"),
                }

        # --- ② itemCodeで取れなければ keyword 検索 ---
        print("[RakutenAPI] Fallback to keyword search")
        params = {
            "applicationId": app_id,
            "keyword": item_code,
            "format": "json",
            "hits": 1,
        }
        r2 = requests.get(base_url, params=params)
        if r2.status_code == 200:
            data = r2.json()
            if data.get("Items"):
                item = data["Items"][0]["Item"]
                return {
                    "product_name": item.get("itemName"),
                    "shop_name": item.get("shopName"),
                    "itemPrice": item.get("itemPrice"),
                    "image_url": item.get("mediumImageUrls", [{}])[0].get("imageUrl"),
                }

        return {"error": f"楽天APIから商品情報を取得できません（{r.status_code}）"}

    except Exception as e:
        print("[RakutenAPI] Exception:", e)
        return {"error": str(e)}
