# --- START(1/3): main/views_api.py ---
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from urllib.parse import urlparse
from django.conf import settings
import requests
import re
import time
from main.utils.error_logger import log_error


# ======================================================
# 楽天商品情報取得API
# ======================================================
@require_GET
def fetch_rakuten_item(request):
    """楽天APIを利用して商品情報を取得"""
    url = request.GET.get("url")
    if not url:
        return JsonResponse({"error": "URLが指定されていません。"}, status=400)

    try:
        parsed = urlparse(url)
        if "rakuten.co.jp" not in parsed.netloc:
            return JsonResponse({"error": "楽天市場の商品URLを指定してください。"}, status=400)

        app_id = getattr(settings, "RAKUTEN_APP_ID", None)
        if not app_id:
            return JsonResponse({"error": "RAKUTEN_APP_ID が未設定です。"}, status=500)

        # --- URL解析 ---
        path = parsed.path.strip("/")
        path = re.sub(r"/+", "/", path)
        parts = path.split("/")
        if len(parts) < 2:
            return JsonResponse({"error": f"URL形式が不正です: {path}"}, status=400)

        shop_code, item_code = parts[-2], parts[-1]
        item_code = re.sub(r"[\?#/].*$", "", item_code).strip()
        endpoint = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"
# --- START(2/3): main/views_api.py ---
        # --- 第一候補: itemCode検索 ---
        params = {
            "applicationId": app_id,
            "hits": 1,
            "itemCode": f"{shop_code}:{item_code}",
        }
        print(f"🟢 Try itemCode with shop prefix: {params}")

        # --- リトライ制御付きリクエスト ---
        for retry in range(3):
            res = requests.get(endpoint, params=params, timeout=5)
            if res.status_code == 429:
                print(f"⚠️ 429 Too Many Requests → {retry+1}回目リトライ待機中")
                time.sleep(1.5)
                continue
            break

        # --- 第二候補: shopCode + keyword検索 ---
        if res.status_code == 400 or not res.ok:
            print("🔄 Fallback to keyword + shopCode search")
            params = {
                "applicationId": app_id,
                "hits": 1,
                "shopCode": shop_code,
                "keyword": item_code,
            }
            for retry in range(3):
                res = requests.get(endpoint, params=params, timeout=5)
                if res.status_code == 429:
                    print(f"⚠️ 429 Too Many Requests → {retry+1}回目リトライ待機中")
                    time.sleep(1.5)
                    continue
                break

        res.raise_for_status()
        data = res.json()

        if not data.get("Items"):
            return JsonResponse({"error": "商品が見つかりませんでした。"}, status=404)

        item = data["Items"][0]["Item"]

        # ✅ price → initial_price に統一
        result = {
            "product_name": item.get("itemName") or "",
            "shop_name": item.get("shopName") or "",
            "initial_price": item.get("itemPrice") or item.get("ItemPrice") or 0,
            "image_url": item.get("mediumImageUrls", [{}])[0].get("imageUrl") or "",
            "product_url": item.get("itemUrl") or "",
        }

        return JsonResponse(result)

# --- START(3/3): main/views_api.py ---
    except requests.RequestException as e:
        log_error(
            user=request.user if request.user.is_authenticated else None,
            type_name=type(e).__name__,
            source="fetch_rakuten_item",
            err=e,
        )
        return JsonResponse({"error": f"API通信エラー: {e}"}, status=500)

    except Exception as e:
        import traceback
        print("🔥 fetch_rakuten_item エラー詳細:")
        traceback.print_exc()
        log_error(
            user=request.user if request.user.is_authenticated else None,
            type_name=type(e).__name__,
            source="fetch_rakuten_item",
            err=e,
        )
        return JsonResponse({"error": str(e)}, status=500)


# ======================================================
# proxy_image（外部画像プロキシ）
# ======================================================
@require_GET
def proxy_image(request):
    """外部画像を安全に中継して返す"""
    try:
        img_url = request.GET.get("url")
        if not img_url:
            return JsonResponse({"error": "URLが指定されていません。"}, status=400)

        headers = {"User-Agent": "Mozilla/5.0 (compatible; KaidokiDesse/1.0)"}
        resp = requests.get(img_url, headers=headers, timeout=6)

        if resp.status_code != 200:
            return JsonResponse(
                {"error": f"画像取得に失敗しました（status={resp.status_code}）"},
                status=resp.status_code,
            )

        content_type = resp.headers.get("Content-Type", "image/jpeg")
        return HttpResponse(resp.content, content_type=content_type)

    except Exception as e:
        log_error(
            user=request.user if request.user.is_authenticated else None,
            type_name=type(e).__name__,
            source="proxy_image",
            err=e,
        )
        return JsonResponse({"error": "画像取得中にエラーが発生しました。"}, status=500)
# --- END(3/3): main/views_api.py ---
