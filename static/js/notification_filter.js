document.addEventListener("DOMContentLoaded", function () {
    const methodSelect = document.getElementById("method-select");
    const typeSelect = document.getElementById("type-select");

    if (!methodSelect || !typeSelect) return;

    // 通知種別の候補データ
    const typeOptions = {
        email: [
            { value: "mail_buy_timing", label: "買い時お知らせ" },
            { value: "mail_stock", label: "在庫お知らせ" }
        ],
        app: [
            { value: "threshold_hit", label: "買い時価格" },
            { value: "discount_over", label: "割引率" },
            { value: "lowest_price", label: "最安値" },
            { value: "stock_few", label: "在庫少" },
            { value: "stock_restore", label: "在庫復活" }
        ]
    };

    // 通知方法変更時の処理
    methodSelect.addEventListener("change", function () {
        const selectedMethod = methodSelect.value;
        typeSelect.innerHTML = ""; // 一旦クリア

        if (!selectedMethod) {
            const opt = document.createElement("option");
            opt.textContent = "通知方法を先に選択";
            opt.value = "";
            typeSelect.appendChild(opt);
            typeSelect.disabled = true;
            return;
        }

        // 有効化＆オプション生成
        const options = typeOptions[selectedMethod];
        const defaultOpt = document.createElement("option");
        defaultOpt.textContent = "全て";
        defaultOpt.value = "";
        typeSelect.appendChild(defaultOpt);

        options.forEach(o => {
            const opt = document.createElement("option");
            opt.value = o.value;
            opt.textContent = o.label;
            typeSelect.appendChild(opt);
        });

        typeSelect.disabled = false;
    });

    // ページ初期化時：状態復元
    const selectedMethod = methodSelect.value;
    if (!selectedMethod) {
        typeSelect.disabled = true;
        typeSelect.innerHTML = '<option value="">通知方法を先に選択</option>';
    } else {
        methodSelect.dispatchEvent(new Event("change"));
        const selectedType = document.querySelector('[name="type"]').getAttribute("value") || "";
        if (selectedType) typeSelect.value = selectedType;
    }
});
