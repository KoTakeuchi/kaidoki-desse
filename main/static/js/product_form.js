// 実行ディレクトリ: I:\school\kaidoki-desse\main\static\js\product_form.js

document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ JS読み込みOK: DOMContentLoaded発火");

    const urlInput = document.querySelector("#id_product_url");
    const nameInput = document.querySelector("#id_product_name");
    const shopInput = document.querySelector("#id_shop_name");
    const priceInput = document.querySelector("#id_initial_price");
    const previewImg = document.querySelector("#preview-image") || document.querySelector("#product-image-preview");
    const statusBox = document.querySelector("#api-status-message");

    if (!urlInput) {
        console.warn("⚠️ id_product_url が見つかりません。");
        return;
    }

    const apiUrl = "/main/api/fetch_rakuten_item/";
    const proxyUrlBase = "/main/api/proxy_image/?url=";

    const setStatus = (text, isError = false) => {
        if (!statusBox) return;
        statusBox.textContent = text;
        statusBox.style.color = isError ? "#C35656" : "#198754";
    };

    const updateImage = (url) => {
        if (!previewImg) return;

        if (!url) {
            previewImg.src = "/static/images/no_image.png";
            return;
        }

        const isRakutenImg =
            url.includes("rakuten.co.jp") || url.includes("rakuten.net") || url.includes("thumbnail.image.rakuten");
        const finalUrl = isRakutenImg
            ? `${proxyUrlBase}${encodeURIComponent(url)}&_t=${Date.now()}`
            : `${url}?_t=${Date.now()}`;

        previewImg.src = finalUrl;
        previewImg.onerror = () => {
            previewImg.src = "/static/images/no_image.png";
        };
    };

    // --- 修正版: エンコード方式変更（encodeURI） ---
    const fetchItemInfo = async () => {
        const rawUrl = urlInput.value.trim();

        if (!rawUrl) {
            setStatus("商品URLを入力してください。", true);
            return;
        }

        const rakutenPattern = /^https?:\/\/([\w.-]+\.)?rakuten\.co\.jp\/.+/;
        if (!rakutenPattern.test(rawUrl)) {
            setStatus("楽天市場の商品URLを入力してください。", true);
            return;
        }

        setStatus("🔄 商品情報を取得中です…");
        updateImage("/static/images/no_image.png");
        nameInput.value = "";
        shopInput.value = "";
        priceInput.value = "";

        try {
            // ✅ encodeURI に変更（スラッシュはエンコードしない）
            const apiUrlWithParam = `${apiUrl}?url=${encodeURI(rawUrl)}`;
            console.log("📡 APIリクエスト:", apiUrlWithParam);

            const response = await fetch(apiUrlWithParam);

            if (!response.ok) {
                setStatus(`❌ 通信エラー（${response.status}）`, true);
                updateImage("/static/images/no_image.png");
                return;
            }

            const data = await response.json();
            console.log("受信データ:", data);

            if (data.error) {
                setStatus(`⚠️ ${data.error}`, true);
                updateImage("/static/images/no_image.png");
                return;
            }

            nameInput.value = data.product_name || data.itemName || "";
            shopInput.value = data.shop_name || data.shopName || "";
            priceInput.value = data.initial_price || data.price || data.itemPrice || "";
            updateImage(data.image_url || data.mediumImageUrls?.[0]?.imageUrl || "");

            setStatus("✅ 商品情報を取得しました。");
        } catch (err) {
            console.error("fetch_rakuten_item error:", err);
            setStatus("❌ 通信エラー（サーバー応答なし）", true);
            updateImage("/static/images/no_image.png");
        }
    };

    // --- blur時 ---
    urlInput.addEventListener("blur", fetchItemInfo);

    // --- Enterキーでも発火 ---
    urlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            fetchItemInfo();
        }
    });
});
