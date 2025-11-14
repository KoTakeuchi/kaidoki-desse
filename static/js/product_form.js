// =============================================================
// 商品登録・編集フォーム：楽天API連携＋画像プレビュー更新
// 対応テンプレート：product_form.html
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ product_form.js 読み込み完了");

    // --- 要素取得 ---
    const urlInput = document.querySelector("#id_product_url");
    const nameInput = document.querySelector("#id_product_name");
    const shopInput = document.querySelector("#id_shop_name");
    const priceInput = document.querySelector("#id_initial_price");
    const previewImg = document.querySelector("#preview-image");
    const statusBox = document.querySelector("#api-status-message");
    const urlErrorBox = document.querySelector("#url-error-message");

    if (!urlInput) {
        console.warn("⚠️ id_product_url が見つかりません。");
        return;
    }

    const apiUrl = "/main/api/fetch_rakuten_item/";
    const proxyUrlBase = "/main/api/proxy_image/?url=";

    // ---------------------------------------------------------
    // ステータスメッセージ制御（修正版）
    // ---------------------------------------------------------
    const setStatus = (text, type = "info") => {
        if (!statusBox || !urlInput) {
            console.log("setStatus: statusBox or urlInput が見つからない", statusBox, urlInput);
            return;
        }

        console.log("setStatus 呼び出し:", type, "text:", text);

        // テキスト設定
        statusBox.textContent = text || "";
        statusBox.style.display = text ? "block" : "none";

        // クラス初期化
        statusBox.className = "";
        urlInput.classList.remove("url-success", "url-error");

        // 種別ごとにクラス付与
        switch (type) {
            case "success":
                statusBox.classList.add("api-success");
                urlInput.classList.add("url-success");
                break;
            case "error":
                statusBox.classList.add("api-error");
                urlInput.classList.add("url-error");
                break;
            default:
                statusBox.classList.add("api-info");
        }

        if (urlErrorBox) {
            urlInput.classList.remove("url-success");
            urlInput.classList.add("url-error");
            console.log("setStatus: Django 側 URL エラーあり → 強制 url-error");
        }

        console.log("setStatus 後の input.className:", urlInput.className);
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
    // 楽天API呼び出し（✔×の重複削除済み）
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

        setStatus("商品情報を取得中です…", "info");
        updateImage("/static/images/no_image.png");

        try {
            const response = await fetch(`${apiUrl}?url=${encodeURIComponent(rawUrl)}`);
            if (!response.ok) {
                setStatus(`通信エラー（${response.status}）`, "error");
                return;
            }

            const data = await response.json();
            console.log("📦 取得データ:", data);

            if (data.error) {
                setStatus(data.error, "error");
                return;
            }

            // 値反映
            if (nameInput) nameInput.value = data.product_name || data.itemName || "";
            if (shopInput) shopInput.value = data.shop_name || data.shopName || "";
            if (priceInput)
                priceInput.value = data.initial_price || data.price || data.itemPrice || "";


            // ✅ 画像URLをhiddenフィールドに保存（★追加）
            const hiddenImageField = document.getElementById("image_url");
            if (hiddenImageField) {
                hiddenImageField.value =
                    data.image_url || data.mediumImageUrls?.[0]?.imageUrl || "";
            }

            updateImage(data.image_url || data.mediumImageUrls?.[0]?.imageUrl || "");
            makeEditable();

            setStatus("楽天API連携成功（商品情報を取得しました）", "success");
        } catch (err) {
            console.error("fetch_rakuten_item error:", err);
            setStatus("通信エラー（サーバー応答なし）", "error");
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

// =============================================================
// 優先度トグル：ON→高 / OFF→普通
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector("#prioritySwitch");
    const label = document.querySelector("#priorityLabel");
    const desc = document.querySelector("#priorityDesc");
    const hidden = document.querySelector("#id_priority");

    if (!toggle || !label || !desc || !hidden) return;

    toggle.addEventListener("change", () => {
        if (toggle.checked) {
            label.textContent = "高";
            desc.textContent = "2時間ごとに最新価格を取得。通知頻度が高めです。";
            hidden.value = "高";
        } else {
            label.textContent = "普通";
            desc.textContent = "24時間ごとに最新価格を取得。アプリ通知・メール通知なし。";
            hidden.value = "普通";
        }
    });
});

// =============================================================
// 通知条件：クリック時に対応する入力欄を表示（簡易安定版）
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
    const flagButtons = document.querySelectorAll(".flag-btn");
    const wrapThreshold = document.getElementById("wrap_threshold");
    const wrapPercent = document.getElementById("wrap_percent");
    const flagTypeHidden = document.getElementById("flagTypeHidden");

    if (!flagButtons.length || !flagTypeHidden) return;

    const hideAll = () => {
        if (wrapThreshold) wrapThreshold.style.display = "none";
        if (wrapPercent) wrapPercent.style.display = "none";
    };

    const showByType = (type) => {
        hideAll();
        if (type === "buy_price" && wrapThreshold) {
            wrapThreshold.style.display = "block";
        } else if (type === "percent_off" && wrapPercent) {
            wrapPercent.style.display = "block";
        }
    };

    flagButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const type = btn.dataset.type;
            flagButtons.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            flagTypeHidden.value = type;
            showByType(type);
        });
    });

    // 初期反映
    showByType(flagTypeHidden.value);
});
