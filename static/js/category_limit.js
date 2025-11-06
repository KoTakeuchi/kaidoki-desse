(() => {
    console.log("✅ category_limit.js (simplified max2) loaded");

    function bindCategoryButtons(root = document) {
        const hidden = root.querySelector("#id_categories_hidden");
        const btns = root.querySelectorAll("label.category-btn");

        if (!btns.length) return;

        btns.forEach((btn) => {
            // 二重登録防止
            if (btn.dataset.bound === "1") return;
            btn.dataset.bound = "1";

            const checkbox = btn.querySelector("input[type='checkbox']");
            if (!checkbox) return;

            btn.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopImmediatePropagation();

                const willActivate = !btn.classList.contains("active");
                btn.classList.toggle("active", willActivate);
                checkbox.checked = willActivate;
                console.log("toggled:", btn.textContent.trim(), "→", willActivate);

                // ✅ 共通・独自問わず最大2件まで
                const activeBtns = Array.from(document.querySelectorAll(".category-btn.active"));
                if (activeBtns.length > 2) {
                    const first = activeBtns[0];
                    first.classList.remove("active");
                    const firstCheckbox = first.querySelector("input[type='checkbox']");
                    if (firstCheckbox) firstCheckbox.checked = false;
                    console.log("🔁 auto-removed (keep max 2):", first.textContent.trim());
                }

                // ✅ hiddenフィールド更新
                const selected = Array.from(document.querySelectorAll(".category-btn.active input"))
                    .map((c) => c.value)
                    .join(",");
                if (hidden) hidden.value = selected;
            });
        });
    }

    // 初期登録
    bindCategoryButtons();

    // ✅ MutationObserver（再描画検知対応）
    const observer = new MutationObserver((mutations) => {
        for (const m of mutations) {
            if (m.addedNodes.length) {
                bindCategoryButtons(document);
            }
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
})();
