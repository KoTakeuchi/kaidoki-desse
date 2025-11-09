// =====================================================
// 楽天API連携 & 商品情報自動取得・画像プレビュー更新
// 対応テンプレート: product_form.html
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ fetch_rakuten.js 読み込み完了");

    const urlInput = document.querySelector("#id_product_url"); // 商品URL入力欄
    const nameInput = document.querySelector("#id_product_name"); // 商品名入力欄
    const shopInput = document.querySelector("#id_shop_name"); // ショップ名入力欄
    const priceInput = document.querySelector("#id_initial_price"); // 登録価格欄
    const messageBox = document.querySelector("#api-status-message"); // メッセージ表示欄
    const previewImage = document.querySelector("#preview-image"); // プレビュー画像

    if (!urlInput || !messageBox || !previewImage) {
        console.warn("❌ 必要なDOM要素が見つかりません。fetch_rakuten.js 中断。");
        return;
    }

    // =====================================================
    // 共通定義
    // =====================================================
    const API_ENDPOINT = "/main/api/fetch_rakuten_item/";
    const NO_IMAGE_PATH = "/static/images/no_image.png";
    const IMAGE_SIZE = 400;

    // 初期プレビュー設定
    previewImage.style.width = `${IMAGE_SIZE}px`;
    previewImage.style.height = `${IMAGE_SIZE}px`;
    previewImage.style.objectFit = "contain";
    previewImage.style.backgroundColor = "#fff";
    previewImage.style.border = "1px solid #ddd";
    previewImage.style.borderRadius = "6px";

    // =====================================================
    // メッセージ表示ユーティリティ
    // =====================================================
    const setMessage = (text, type = "info") => {
        messageBox.textContent = text;
        messageBox.className = "mt-2 small text-center fw-bold";

        switch (type) {
            case "success":
                messageBox.classList.add("text-success");
                break;
            case "error":
                messageBox.classList.add("text-danger");
                break;
            default:
                messageBox.classList.add("text-muted");
        }
    };

    // =====================================================
    // 入力欄を編集可能に変更
    // =====================================================
    const makeEditable = () => {
        [nameInput, shopInput, priceInput].forEach((input) => {
            if (!input) return;
            input.removeAttribute("readonly");
            input.classList.add("editable");
        });
    };

    // =====================================================
    // 画像プレビュー更新
    // =====================================================
    const updateImage = (url) => {
        if (!url) {
            previewImage.src = NO_IMAGE_PATH;
            return;
        }

        let imageUrl = url;
        if (!imageUrl.includes("_ex=")) {
            const hasQuery = imageUrl.includes("?");
            imageUrl += (hasQuery ? "&" : "?") + "_ex=400x400";
        }
        previewImage.src = imageUrl;
        previewImage.onerror = () => (previewImage.src = NO_IMAGE_PATH);
    };

    // =====================================================
    // 楽天API呼び出し処理
    // =====================================================
    const fetchRakutenItem = async () => {
        const rawUrl = urlInput.value.trim();
        if (!rawUrl) return;

        // 楽天URL以外を弾く
        const rakutenPattern = /^https?:\/\/([\w.-]+\.)?rakuten\.co\.jp\/.+/;
        if (!rakutenPattern.test(rawUrl)) {
            setMessage("楽天市場の商品URLを入力してください。", "error");
            updateImage(null);
            return;
        }

        // 通信開始
        setMessage("楽天API通信中...", "info");
        updateImage(null);

        try {
            const response = await fetch(`${API_ENDPOINT}?url=${encodeURIComponent(rawUrl)}`);
            const data = await response.json();

            if (response.ok && data.product_name) {
                // 値反映
                if (nameInput) nameInput.value = data.product_name || "";
                if (shopInput) shopInput.value = data.shop_name || "";
                if (priceInput) priceInput.value = data.initial_price || "";

                updateImage(data.image_url);
                makeEditable();
                setMessage("✅ 楽天API通信成功：商品情報を取得しました。", "success");
            } else {
                setMessage(data.error || "商品情報を取得できませんでした。", "error");
                updateImage(null);
            }
        } catch (err) {
            console.error("fetchRakutenItem error:", err);
            setMessage("❌ 通信エラー（サーバー応答なし）", "error");
            updateImage(null);
        }
    };

    // =====================================================
    // イベント登録（blur / Enter）
    // =====================================================
    urlInput.addEventListener("blur", fetchRakutenItem);
    urlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            fetchRakutenItem();
        }
    });
});
