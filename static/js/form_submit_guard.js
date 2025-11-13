// --- START: main/static/js/form_submit_guard.js ---
(() => {
    console.log("✅ form_submit_guard.js loaded");

    const form = document.querySelector("form#product-form, form.product-form");
    if (!form) {
        console.warn("⚠️ フォーム要素が見つかりません。");
        return;
    }

    const submitBtn = form.querySelector("button[type='submit']");
    let isSubmitting = false;

    // --- フォーム送信ガード ---
    form.addEventListener("submit", (e) => {
        if (isSubmitting) {
            console.log("⚠️ 多重送信ブロック");
            e.preventDefault();
            return;
        }

        // --- 基本バリデーション ---
        const urlField = form.querySelector("#id_product_url");
        const nameField = form.querySelector("#id_product_name");
        const priceField = form.querySelector("#id_initial_price");

        if (!urlField?.value.trim()) {
            alert("商品URLを入力してください。");
            e.preventDefault();
            urlField.focus();
            return;
        }

        if (!nameField?.value.trim()) {
            alert("商品名を入力してください。");
            e.preventDefault();
            nameField.focus();
            return;
        }

        if (priceField && priceField.value && parseInt(priceField.value) < 0) {
            alert("価格は0以上を入力してください。");
            e.preventDefault();
            priceField.focus();
            return;
        }

        // --- 多重送信防止 ---
        isSubmitting = true;
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = "送信中…";
        }

        console.log("🚀 フォーム送信開始");
    });

    // --- ページ離脱時警告 ---
    let isDirty = false;
    form.addEventListener("input", () => {
        isDirty = true;
    });

    window.addEventListener("beforeunload", (e) => {
        if (isDirty && !isSubmitting) {
            e.preventDefault();
            e.returnValue = "変更が保存されていません。このページを離れますか？";
        }
    });
})();
// --- END: main/static/js/form_submit_guard.js ---
