// --- START: main/static/js/threshold_helper.js ---
(() => {
    console.log("✅ threshold_helper.js loaded");

    const thresholdInput = document.getElementById("id_threshold_price");
    const regularInput = document.getElementById("id_regular_price");
    const initialInput = document.getElementById("id_initial_price");
    const hintBox = document.getElementById("thresholdHint");

    if (!thresholdInput || !hintBox) {
        console.warn("⚠️ threshold_helper.js: 必要要素が見つかりません。");
        return;
    }

    /**
     * 表示更新処理
     */
    const updateHint = () => {
        const regular = parseFloat(regularInput?.value || 0);
        const current = parseFloat(initialInput?.value || 0);
        const threshold = parseFloat(thresholdInput.value || 0);

        if (!regular || !current) {
            hintBox.textContent = "定価と登録価格を入力すると目安を表示します。";
            hintBox.className = "text-muted small";
            return;
        }

        // 割引率計算
        const discount = 100 - Math.round((threshold / regular) * 100);
        const diff = regular - threshold;

        if (!threshold) {
            hintBox.textContent = `目安: 現在 ${current.toLocaleString()}円 / 定価 ${regular.toLocaleString()}円`;
            hintBox.className = "text-muted small";
        } else if (threshold >= regular) {
            hintBox.textContent = "買い時価格は定価より低く設定してください。";
            hintBox.className = "text-danger small";
        } else {
            hintBox.textContent = `定価比 -${discount}%（約${diff.toLocaleString()}円引き）`;
            hintBox.className = "text-success small";
        }
    };

    // イベント登録
    [thresholdInput, regularInput, initialInput].forEach((el) => {
        if (el) el.addEventListener("input", updateHint);
    });

    // 初期化
    updateHint();
})();
// --- END: main/static/js/threshold_helper.js ---
