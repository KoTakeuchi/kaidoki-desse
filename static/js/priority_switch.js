
// =============================================================
// 優先度スイッチ制御（高⇄普通）
// 対応テンプレート：product_form.html
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ priority_switch.js 読み込み完了");

    const switchInput = document.getElementById("prioritySwitch");
    const label = document.getElementById("priorityLabel");
    const hidden = document.getElementById("id_priority");
    const desc = document.getElementById("priorityDesc");

    if (!switchInput || !label || !hidden) {
        console.warn("⚠️ priority_switch.js: 要素が不足しています。");
        return;
    }

    // ---------------------------------------------------------
    // 表示更新関数
    // ---------------------------------------------------------
    const updatePriorityDisplay = (isHigh) => {
        label.textContent = isHigh ? "高" : "普通";
        hidden.value = isHigh ? "高" : "普通";

        label.classList.toggle("text-danger", isHigh);
        label.classList.toggle("text-secondary", !isHigh);

        if (desc) {
            desc.textContent = isHigh
                ? "2時間ごとに最新価格と在庫数を取得。アプリ通知・メール通知なし。"
                : "24時間ごとに最新価格と在庫数を取得。通知頻度が抑えられます。";
        }

        console.log(`🔁 優先度変更: ${hidden.value}`);
    };

    // ---------------------------------------------------------
    // 初期状態同期
    // ---------------------------------------------------------
    const initialValue = hidden.value?.trim();
    const isHigh = initialValue === "高";
    switchInput.checked = isHigh;
    updatePriorityDisplay(isHigh);

    // ---------------------------------------------------------
    // トグル変更イベント
    // ---------------------------------------------------------
    switchInput.addEventListener("change", () => {
        updatePriorityDisplay(switchInput.checked);
    });

    // ---------------------------------------------------------
    // 再描画対応（モーダルやAJAX再読み込み時）
    // ---------------------------------------------------------
    const observer = new MutationObserver(() => {
        if (document.body.contains(switchInput)) {
            updatePriorityDisplay(switchInput.checked);
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
});

