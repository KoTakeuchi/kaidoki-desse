// ============================================
// 機能概要: 商品一覧ページの動作用スクリプト
// ・チェックボックス選択による一括削除ボタン表示制御
// ・商品カードクリックで詳細ページ遷移
// 対応テンプレート: product_list.html
// ============================================

document.addEventListener("DOMContentLoaded", () => {
    const checkboxes = document.querySelectorAll(".bulk-check");
    const bulkBtn = document.getElementById("bulkDeleteBtn");

    function updateButtonVisibility() {
        const anyChecked = Array.from(checkboxes).some(chk => chk.checked);
        if (bulkBtn) bulkBtn.style.display = anyChecked ? "inline-block" : "none";
    }

    checkboxes.forEach(chk => chk.addEventListener("change", updateButtonVisibility));

    document.querySelectorAll(".product-card").forEach(card => {
        card.addEventListener("click", e => {
            if (e.target.closest(".form-check-input") || e.target.closest(".btn")) return;
            const url = card.getAttribute("data-url");
            if (url) window.location.href = url;
        });
    });
});
