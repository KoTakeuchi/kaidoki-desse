
// =============================================================
// カテゴリ選択肢整理：未分類を除外
// 対応テンプレート：product_form.html
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ category_cleaner.js 読み込み完了");

    const select = document.getElementById("id_categories");
    if (!select) {
        console.warn("⚠️ id_categories が見つかりません。");
        return;
    }

    // ---------------------------------------------------------
    // 未分類カテゴリを除外（ユーザーが選べないようにする）
    // ---------------------------------------------------------
    const options = Array.from(select.options);
    let removedCount = 0;

    options.forEach((opt) => {
        const text = opt.textContent?.trim() || "";
        if (text.includes("未分類")) {
            opt.remove();
            removedCount++;
        }
    });

    if (removedCount > 0) {
        console.log(`🧹 未分類カテゴリを ${removedCount} 件 除外しました。`);
    }

    // ---------------------------------------------------------
    // 選択状態を初期化（削除された項目が残っていた場合に備える）
    // ---------------------------------------------------------
    const selectedValues = Array.from(select.selectedOptions).map(opt => opt.value);
    selectedValues.forEach((v) => {
        if (!select.querySelector(`option[value="${v}"]`)) {
            console.warn(`⚠️ 不明なカテゴリID ${v} を解除しました。`);
        }
    });
});

