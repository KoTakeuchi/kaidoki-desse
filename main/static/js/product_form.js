// static/js/product_form.js
document.addEventListener("DOMContentLoaded", () => {
    const urlInput = document.querySelector("#id_product_url");
    const nameInput = document.querySelector("#id_product_name");
    const shopInput = document.querySelector("#id_shop_name");
    const priceInput = document.querySelector("#id_initial_price");
    const previewImg = document.querySelector("#preview-image");
    const statusBox = document.querySelector("#api-status-message");

    if (!urlInput) return; // 新規登録画面以外では無視

    // ステータス表示用ヘルパー
    const setStatus = (text, isError = false) => {
        statusBox.textContent = text;
        statusBox.style.color = isError ? "#C35656" : "#198754"; // 赤 or 緑
    };

    // --- URL入力欄でフォーカスアウトしたとき自動取得 ---
    urlInput.addEventListener("blur", async () => {
        const url = urlInput.value.trim();
        if (!url || !url.includes("rakuten.co.jp")) {
            setStatus("楽天市場の商品URLを入力してください。", true);
            return;
        }

        setStatus("商品情報を取得中です…");

        try {
            const response = await fetch(`/api/fetch_rakuten_item/?url=${encodeURIComponent(url)}`);
            const data = await response.json();

            if (!response.ok) {
                setStatus(data.error || "商品情報の取得に失敗しました。", true);
                return;
            }

            // --- 成功時: 各フィールドへ反映 ---
            nameInput.value = data.product_name || "";
            shopInput.value = data.shop_name || "";
            priceInput.value = data.initial_price || "";
            previewImg.src = data.image_url || "/static/images/noimage.png";
            setStatus("✅ 商品情報を自動入力しました。");

        } catch (err) {
            console.error("fetch_rakuten_item error:", err);
            setStatus("通信エラーが発生しました。", true);
        }
    });
});
