
// =============================================================
// 商品登録・編集フォーム：楽天API連携＋画像プレビュー更新
// 対応テンプレート：product_form.html
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ product_form.js 読み込み完了");

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

    // ---------------------------------------------------------
    // ステータスメッセージ表示
    // ---------------------------------------------------------
    const setStatus = (text, type = "info") => {
        if (!statusBox) return;

        statusBox.textContent = text;
        statusBox.style.display = "block";
        statusBox.className = ""; // 既存クラス全消去
        statusBox.classList.add("mt-2", "small", "text-center");

        switch (type) {
            case "success":
                statusBox.classList.add("text-success", "fw-bold");
                break;
            case "error":
                statusBox.classList.add("text-danger", "fw-bold");
                break;
            default:
                statusBox.classList.add("text-muted");
        }
    };

    // ---------------------------------------------------------
    // 画像更新
    // ---------------------------------------------------------
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

    // ---------------------------------------------------------
    // API取得後にフィールドを編集可に変更
    // ---------------------------------------------------------
    const makeEditable = () => {
        [nameInput, shopInput].forEach((input) => {
            if (!input) return;
            input.removeAttribute("readonly");
            input.classList.add("editable");
        });
    };

    // ---------------------------------------------------------
    // 楽天API呼び出し
    // ---------------------------------------------------------
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
            const response = await fetch(`${apiUrl}?url=${encodeURIComponent(rawUrl)}`);
            if (!response.ok) {
                setStatus(`❌ 通信エラー（${response.status}）`, "error");
                return;
            }

            const data = await response.json();
            console.log("📦 取得データ:", data);

            if (data.error) {
                setStatus(`⚠️ ${data.error}`, "error");
                return;
            }

            // 値反映
            if (nameInput) nameInput.value = data.product_name || data.itemName || "";
            if (shopInput) shopInput.value = data.shop_name || data.shopName || "";
            if (priceInput)
                priceInput.value = data.initial_price || data.price || data.itemPrice || "";

            updateImage(data.image_url || data.mediumImageUrls?.[0]?.imageUrl || "");
            makeEditable();

            setStatus("✅ 楽天API連携成功（商品情報を取得しました）", "success");
        } catch (err) {
            console.error("fetch_rakuten_item error:", err);
            setStatus("❌ 通信エラー（サーバー応答なし）", "error");
            updateImage("/static/images/no_image.png");
        }
    };

    // ---------------------------------------------------------
    // イベント登録（blur・Enter）
    // ---------------------------------------------------------
    urlInput.addEventListener("blur", fetchItemInfo);
    urlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            fetchItemInfo();
        }
    });
});

