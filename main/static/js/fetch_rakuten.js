// ================================
// 楽天API連携 & サムネイル表示処理
// ================================

document.addEventListener("DOMContentLoaded", () => {
    const urlInput = document.querySelector("#id_product_url"); // 商品URL入力欄
    const messageBox = document.querySelector("#api-status-message"); // メッセージ表示欄
    const previewImage = document.querySelector("#preview-image"); // 画像プレビュー欄

    if (!urlInput || !messageBox || !previewImage) return;

    // 画像のリサイズ後の共通サイズ（固定表示サイズ）
    const IMAGE_SIZE = 400; // 1:1 正方形で統一

    // 余白白背景 + contain 表示を適用（初期ロード時にも適用）
    previewImage.style.width = `${IMAGE_SIZE}px`;
    previewImage.style.height = `${IMAGE_SIZE}px`;
    previewImage.style.objectFit = "contain";
    previewImage.style.backgroundColor = "#fff";
    previewImage.style.border = "1px solid #ddd";
    previewImage.style.borderRadius = "6px";

    // --- 入力欄からフォーカスが外れた時にAPI通信 ---
    urlInput.addEventListener("blur", async () => {
        const url = urlInput.value.trim();
        if (!url) return;

        // 通信中メッセージ
        messageBox.textContent = "楽天API通信中...";
        messageBox.className = "alert alert-info mt-2";

        try {
            const response = await fetch(`/main/api/fetch_rakuten_item/?url=${encodeURIComponent(url)}`);
            const data = await response.json();

            // --- 通信成功 & データ取得成功 ---
            if (response.ok && data.image_url) {
                // ✅ 画像URLのリサイズ版（楽天CDN仕様 _ex=400x400 を付与）
                let imageUrl = data.image_url;
                if (!imageUrl.includes("_ex=")) {
                    const hasQuery = imageUrl.includes("?");
                    imageUrl += (hasQuery ? "&" : "?") + "_ex=400x400";
                }

                previewImage.src = imageUrl;

                messageBox.textContent = "楽天API通信成功：商品情報を取得しました。";
                messageBox.className = "alert alert-success mt-2"; // 緑背景
            }
            // --- 通信成功だが商品情報なし or 不正 ---
            else {
                previewImage.src = "/static/images/noimage.png";
                messageBox.textContent = data.error || "商品情報を取得できませんでした。";
                messageBox.className = "alert alert-danger mt-2"; // 赤背景
            }
        } catch (error) {
            // --- 通信失敗時 ---
            previewImage.src = "/static/images/noimage.png";
            messageBox.textContent = "楽天API通信中にエラーが発生しました。";
            messageBox.className = "alert alert-danger mt-2";
        }
    });
});
