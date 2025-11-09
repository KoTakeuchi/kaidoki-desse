// =============================================================
// カテゴリ選択（最盛期仕様）
// 共通・独自問わず最大2件まで選択可（pillボタン方式）
// 対応テンプレート：product_form.html
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ category_limit.js 読み込み完了");

    const tags = document.querySelectorAll(".cat-tag");
    const hiddenInput = document.querySelector("#selected_cats");
    const limitInfo = document.querySelector("#category-limit-info");

    const MAX_SELECT = 2;
    let selectedIds = [];

    // --- 選択状態をUIに反映 ---
    const updateUI = () => {
        tags.forEach(tag => {
            const id = tag.dataset.id;
            if (selectedIds.includes(id)) {
                tag.classList.add("active");
            } else {
                tag.classList.remove("active");
            }
        });
        hiddenInput.value = selectedIds.join(",");
    };

    // --- ボタン押下時処理 ---
    tags.forEach(tag => {
        tag.addEventListener("click", () => {
            const id = tag.dataset.id;

            if (selectedIds.includes(id)) {
                // 再クリック → 解除
                selectedIds = selectedIds.filter(x => x !== id);
            } else {
                // 新規選択
                if (selectedIds.length >= MAX_SELECT) {
                    // 一番古いものを外す（FIFO）
                    selectedIds.shift();
                }
                selectedIds.push(id);
            }

            limitInfo.textContent =
                selectedIds.length > MAX_SELECT
                    ? "カテゴリは最大2つまで選択できます。"
                    : "";

            updateUI();
        });
    });

    updateUI();
});
