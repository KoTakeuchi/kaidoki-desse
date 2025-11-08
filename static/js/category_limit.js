
// =============================================================
// カテゴリ選択：共通・独自問わず最大2件まで選択可
// 対応テンプレート：product_form.html
// =============================================================
(() => {
    console.log("✅ category_limit.js (select-based unified max2) loaded");

    const select = document.getElementById("id_categories");
    if (!select) {
        console.warn("⚠️ id_categories が見つかりません。");
        return;
    }

    const MAX = 2;
    const noticeId = "category-limit-notice";

    // ---------------------------------------------------------
    // 警告メッセージ表示
    // ---------------------------------------------------------
    function showNotice(msg) {
        let box = document.getElementById(noticeId);
        if (!box) {
            box = document.createElement("div");
            box.id = noticeId;
            box.className = "alert alert-warning small mt-2 text-center";

            // select.after() が使えない環境に備えたフォールバック
            if (typeof select.after === "function") {
                select.after(box);
            } else {
                select.insertAdjacentElement("afterend", box);
            }
        }

        box.textContent = msg;
        box.style.display = "block";
    }

    // ---------------------------------------------------------
    // メッセージ非表示
    // ---------------------------------------------------------
    function hideNotice() {
        const box = document.getElementById(noticeId);
        if (box) box.style.display = "none";
    }

    // ---------------------------------------------------------
    // 選択制限処理
    // ---------------------------------------------------------
    select.addEventListener("change", () => {
        const selected = Array.from(select.selectedOptions);

        if (selected.length > MAX) {
            // ✅ 超過した最後の選択を自動解除
            const last = selected[selected.length - 1];
            if (last) last.selected = false;

            showNotice(`カテゴリは最大${MAX}件まで選択できます。`);

            // ⏱ 3秒後に自動で警告を非表示
            clearTimeout(select._hideTimer);
            select._hideTimer = setTimeout(hideNotice, 3000);
        } else {
            hideNotice();
        }

        console.log(`🟡 選択中カテゴリ数: ${selected.length}`);
    });
})();
