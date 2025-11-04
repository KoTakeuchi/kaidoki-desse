// 実行ディレクトリ: I:\school\kaidoki-desse\static\js\product_form.js

document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ JS読み込みOK: DOMContentLoaded発火");

    const urlInput = document.querySelector("#id_product_url");
    if (!urlInput) {
        console.warn("⚠️ id_product_url が見つかりません");
        return;
    }
    console.log("✅ id_product_url 要素検出:", urlInput);

    urlInput.addEventListener("blur", async () => {
        console.log("🔥 blurイベント発火");
        const url = urlInput.value.trim();
        console.log("入力URL:", url);
    });
});


document.addEventListener("DOMContentLoaded", () => {
    const urlInput = document.querySelector("#id_product_url");
    const nameInput = document.querySelector("#id_product_name");
    const shopInput = document.querySelector("#id_shop_name");
    const priceInput = document.querySelector("#id_initial_price");
    const previewImg = document.querySelector("#preview-image");
    const statusBox = document.querySelector("#api-status-message");

    if (!urlInput) return;

    const apiUrl = "/main/api/fetch_rakuten_item/";

    // ステータスメッセージを表示
    const setStatus = (text, isError = false) => {
        if (!statusBox) return;
        statusBox.textContent = text;
        statusBox.style.color = isError ? "#C35656" : "#198754";
    };

    // 安定した画像読み込み（存在確認付き）
    const updateImage = async (url) => {
        if (!previewImg) return;

        // キャッシュ防止クエリを付与
        const cacheBusted = `${url}?_t=${new Date().getTime()}`;

        try {
            const headCheck = await fetch(cacheBusted, { method: "HEAD" });
            if (headCheck.ok) {
                previewImg.src = cacheBusted;
            } else {
                // URLが存在しない or 400系 → no_imageにフォールバック
                previewImg.src = "/static/images/no_image.png";
            }
        } catch {
            // 通信エラー時もno_imageに切り替え
            previewImg.src = "/static/images/no_image.png";
        }

        previewImg.alt = "商品画像プレビュー";
        previewImg.style.opacity = "1";
    };

    urlInput.addEventListener("blur", async () => {
        const url = urlInput.value.trim();

        if (!url) {
            setStatus("商品URLを入力してください。", true);
            return;
        }
        if (!url.includes("rakuten.co.jp")) {
            setStatus("楽天市場の商品URLを入力してください。", true);
            return;
        }

        setStatus("商品情報を取得中です…");
        await updateImage("/static/images/no_image.png");
        nameInput.value = "";
        shopInput.value = "";
        priceInput.value = "";

        try {
            const response = await fetch(`${apiUrl}?url=${encodeURIComponent(url)}`);

            if (!response.ok) {
                setStatus(`通信エラー (${response.status})`, true);
                await updateImage("/static/images/no_image.png");
                return;
            }

            let data;
            try {
                data = await response.json();
            } catch {
                setStatus("サーバー応答が不正です。", true);
                await updateImage("/static/images/no_image.png");
                return;
            }

            if (data.error) {
                setStatus(data.error, true);
                await updateImage("/static/images/no_image.png");
                return;
            }

            if (!data.product_name && !data.shop_name) {
                setStatus("商品情報を取得できませんでした。", true);
                await updateImage("/static/images/no_image.png");
                return;
            }

            // --- 成功時 ---
            nameInput.value = data.product_name || "";
            shopInput.value = data.shop_name || "";
            priceInput.value = data.initial_price || "";

            // 画像URL検証付きで表示
            if (data.image_url) {
                await updateImage(data.image_url);
            } else {
                await updateImage("/static/images/no_image.png");
            }

            setStatus("✅ 商品情報を自動入力しました。");

        } catch (err) {
            console.error("fetch_rakuten_item error:", err);
            setStatus("通信エラーが発生しました。", true);
            await updateImage("/static/images/no_image.png");
        }
    });
});
