document.addEventListener("DOMContentLoaded", function () {
    const methodSelect = document.getElementById("method-select");
    const typeSelect = document.getElementById("type-select");
    const typeWrapper = typeSelect ? typeSelect.closest("div") : null;

    if (!methodSelect || !typeSelect) return;

    // 通知種別の候補データ（アプリのみ）
    const typeOptions = {
        app: [
            { value: "threshold_hit", label: "買い時価格" },
            { value: "discount_over", label: "割引率" },
            { value: "lowest_price", label: "最安値" },
            { value: "stock_few", label: "在庫わずか" },
            { value: "stock_restore", label: "在庫復活" },
            { value: "stock_none", label: "売り切れ" },
        ]
    };

    // 通知方法変更時の処理
    methodSelect.addEventListener("change", function () {
        const selectedMethod = methodSelect.value;
        typeSelect.innerHTML = "";

        if (!selectedMethod) {
            const opt = document.createElement("option");
            opt.textContent = "通知方法を先に選択";
            opt.value = "";
            typeSelect.appendChild(opt);
            typeSelect.disabled = true;
            if (typeWrapper) typeWrapper.style.visibility = "hidden";
            return;
        }

        // ✅ メールの場合は通知種別を非表示
        if (selectedMethod === "email") {
            typeSelect.disabled = true;
            if (typeWrapper) typeWrapper.style.visibility = "hidden";
            return;
        }

        // アプリの場合は通知種別を表示
        if (typeWrapper) typeWrapper.style.visibility = "visible";
        const options = typeOptions[selectedMethod] || [];
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
        if (typeWrapper) typeWrapper.style.visibility = "hidden";
    } else {
        methodSelect.dispatchEvent(new Event("change"));
        const selectedType = document.querySelector('[name="type"]').getAttribute("value") || "";
        if (selectedType) typeSelect.value = selectedType;
    }
});
