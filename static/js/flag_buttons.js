// --- START: main/static/js/flag_buttons.js ---
(() => {
    console.log("✅ flag_buttons.js loaded");

    const buttons = document.querySelectorAll(".flag-btn");
    const descBox = document.getElementById("flagDesc");
    const hidden = document.getElementById("flagTypeHidden");

    const wrapRegular = document.getElementById("wrap_regular");
    const wrapThreshold = document.getElementById("wrap_threshold");
    const wrapPercent = document.getElementById("wrap_percent");

    if (!buttons.length || !hidden) {
        console.warn("⚠️ flag_buttons.js: 必要要素が見つかりません。");
        return;
    }

    // --- 表示更新 ---
    const updateDisplay = (type) => {
        // アクティブ切替
        buttons.forEach((btn) =>
            btn.classList.toggle("active", btn.dataset.type === type)
        );

        // hidden 更新
        hidden.value = type;

        // 各入力ブロック切替
        if (wrapRegular) wrapRegular.style.display = type === "percent_off" ? "block" : "none";
        if (wrapThreshold) wrapThreshold.style.display = type === "buy_price" ? "block" : "none";
        if (wrapPercent) wrapPercent.style.display = type === "percent_off" ? "block" : "none";

        // 説明更新
        const activeBtn = Array.from(buttons).find(b => b.dataset.type === type);
        if (activeBtn && descBox) {
            descBox.textContent = activeBtn.dataset.desc || "";
        }
    };

    // --- 初期表示 ---
    updateDisplay(hidden.value || "buy_price");

    // --- クリックイベント登録 ---
    buttons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const type = btn.dataset.type;
            updateDisplay(type);
        });

        // ホバーで説明を一時更新
        btn.addEventListener("mouseenter", () => {
            if (descBox) descBox.textContent = btn.dataset.desc || "";
        });
        btn.addEventListener("mouseleave", () => {
            const activeBtn = document.querySelector(".flag-btn.active");
            if (activeBtn && descBox)
                descBox.textContent = activeBtn.dataset.desc || "";
        });
    });
})();
// --- END: main/static/js/flag_buttons.js ---
