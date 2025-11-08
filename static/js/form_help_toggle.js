
// =============================================================
// フォームヘルプ表示トグル制御（全項目一括）
// 対応テンプレート：product_form.html
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ form_help_toggle.js 読み込み完了");

    // ---------------------------------------------------------
    // ボタン生成（「ヘルプを表示／非表示」）
    // ---------------------------------------------------------
    const form = document.querySelector("form");
    if (!form) return;

    const toggleBtn = document.createElement("button");
    toggleBtn.type = "button";
    toggleBtn.textContent = "ヘルプを表示";
    toggleBtn.className = "btn btn-outline-secondary btn-sm mb-3";
    form.prepend(toggleBtn);

    // ---------------------------------------------------------
    // 対象ヘルプテキストの抽出
    // ---------------------------------------------------------
    const helpTexts = form.querySelectorAll(".form-text, small.text-muted");

    if (!helpTexts.length) {
        console.log("ℹ️ ヘルプテキスト要素が存在しません。");
        return;
    }

    // 初期状態は非表示
    helpTexts.forEach((el) => {
        el.style.display = "none";
    });

    // ---------------------------------------------------------
    // 開閉制御
    // ---------------------------------------------------------
    let visible = false;
    toggleBtn.addEventListener("click", () => {
        visible = !visible;

        helpTexts.forEach((el) => {
            el.style.display = visible ? "block" : "none";
        });

        toggleBtn.textContent = visible ? "ヘルプを非表示" : "ヘルプを表示";
        toggleBtn.classList.toggle("btn-outline-secondary", !visible);
        toggleBtn.classList.toggle("btn-outline-danger", visible);

        console.log(`🪄 フォームヘルプ: ${visible ? "表示" : "非表示"}`);
    });
});
