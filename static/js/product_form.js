// 実行ディレクトリ: I:\school\kaidoki-desse\main\static\js\product_form.js

document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ JS読み込みOK: DOMContentLoaded発火");

    const urlInput = document.querySelector("#id_product_url");
    const nameInput = document.querySelector("#id_product_name");
    const shopInput = document.querySelector("#id_shop_name");
    const priceInput = document.querySelector("#id_initial_price");
    const previewImg = document.querySelector("#preview-image");
    const statusBox = document.querySelector("#api-status-message");

    if (!urlInput) {
        console.warn("⚠️ id_product_url が見つかりません。");
        return;
    }

    const apiUrl = "/main/api/fetch_rakuten_item/";
    const proxyUrlBase = "/main/api/proxy_image/?url=";

    // ✅ メッセージ表示（背景付きで復活）
    const setStatus = (text, type = "info") => {
        if (!statusBox) return;

        statusBox.textContent = text;
        statusBox.style.display = "block";

        statusBox.classList.remove("success", "error", "info");

        if (type === "success") {
            statusBox.classList.add("success");
        } else if (type === "error") {
            statusBox.classList.add("error");
        } else {
            statusBox.classList.add("info");
        }
    };

    // ✅ 画像更新
    const updateImage = (url) => {
        if (!previewImg) return;

        if (!url) {
            previewImg.src = "/static/images/no_image.png";
            return;
        }

        const isRakutenImg =
            url.includes("rakuten.co.jp") ||
            url.includes("rakuten.net") ||
            url.includes("thumbnail.image.rakuten");

        const finalUrl = isRakutenImg
            ? `${proxyUrlBase}${encodeURIComponent(url)}&_t=${Date.now()}`
            : `${url}?_t=${Date.now()}`;

        previewImg.src = finalUrl;
        previewImg.onerror = () => {
            previewImg.src = "/static/images/no_image.png";
        };
    };

    // ✅ API取得後に編集可能にする
    const applyEditableFields = () => {
        [nameInput, shopInput].forEach((input) => {
            if (!input) return;
            input.removeAttribute("readonly");
            input.classList.add("editable");
        });
    };

    // ✅ API呼び出し
    const fetchItemInfo = async () => {
        const rawUrl = urlInput.value.trim();

        if (!rawUrl) {
            setStatus("商品URLを入力してください。", "error");
            return;
        }

        const rakutenPattern = /^https?:\/\/([\w.-]+\.)?rakuten\.co\.jp\/.+/;
        if (!rakutenPattern.test(rawUrl)) {
            setStatus("楽天市場の商品URLを入力してください。", "error");
            return;
        }

        setStatus("🔄 商品情報を取得中です…", "info");
        updateImage("/static/images/no_image.png");

        try {
            const apiUrlWithParam = `${apiUrl}?url=${encodeURI(rawUrl)}`;
            console.log("📡 APIリクエスト:", apiUrlWithParam);

            const response = await fetch(apiUrlWithParam);

            if (!response.ok) {
                setStatus(`❌ 通信エラー（${response.status}）`, "error");
                return;
            }

            const data = await response.json();
            console.log("受信データ:", data);

            if (data.error) {
                setStatus(`⚠️ ${data.error}`, "error");
                return;
            }

            // ✅ 値セット
            if (nameInput) nameInput.value = data.product_name || data.itemName || "";
            if (shopInput) shopInput.value = data.shop_name || data.shopName || "";
            if (priceInput) priceInput.value = data.initial_price || data.price || data.itemPrice || "";

            updateImage(data.image_url || data.mediumImageUrls?.[0]?.imageUrl || "");

            // ✅ 編集可能化
            applyEditableFields();

            // ✅ 成功メッセージ
            setStatus("✅ 楽天API連係成功（商品情報を取得しました）", "success");
        } catch (err) {
            console.error("fetch_rakuten_item error:", err);
            setStatus("❌ 通信エラー（サーバー応答なし）", "error");
            updateImage("/static/images/no_image.png");
        }
    };

    // blur／Enterイベント登録
    urlInput.addEventListener("blur", fetchItemInfo);
    urlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            fetchItemInfo();
        }
    });
});
