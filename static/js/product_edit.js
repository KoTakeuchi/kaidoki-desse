console.log("product_edit.js loaded (edit)");

document.addEventListener("DOMContentLoaded", () => {
    // ==========================
    // カテゴリ制御
    // ==========================
    const catTags = document.querySelectorAll(".cat-tag");
    const hiddenInput = document.getElementById("selectedCats");

    if (catTags.length && hiddenInput) {
        let selected = hiddenInput.value
            ? hiddenInput.value.split(",").map(v => parseInt(v, 10)).filter(v => !Number.isNaN(v))
            : [];

        if (selected.length > 2) {
            const keep = selected.slice(-2);
            catTags.forEach(tag => {
                const id = parseInt(tag.dataset.catId, 10);
                if (!keep.includes(id)) tag.classList.remove("active");
            });
            selected = keep;
            hiddenInput.value = selected.join(",");
        }

        const updateHidden = () => {
            hiddenInput.value = selected.join(",");
            console.log("selectedCats:", hiddenInput.value);
        };

        catTags.forEach(tag => {
            tag.addEventListener("click", () => {
                const catId = parseInt(tag.dataset.catId, 10);
                if (Number.isNaN(catId)) return;

                const isActive = tag.classList.contains("active");

                if (isActive) {
                    tag.classList.remove("active");
                    selected = selected.filter(id => id !== catId);
                    updateHidden();
                    return;
                }

                if (selected.length >= 2) {
                    const oldestId = selected[0];
                    selected = selected.slice(1);
                    const oldestTag = document.querySelector(`.cat-tag[data-cat-id="${oldestId}"]`);
                    if (oldestTag) oldestTag.classList.remove("active");
                }

                tag.classList.add("active");
                selected.push(catId);
                updateHidden();
            });
        });
    }

    // ==========================
    // 優先度トグル制御
    // ==========================
    const prioritySwitch = document.getElementById("prioritySwitch");
    const priorityLabel = document.getElementById("priorityLabel");
    const priorityDesc = document.getElementById("priorityDesc");
    const priorityHidden = document.getElementById("id_priority");

    if (prioritySwitch && priorityLabel && priorityDesc && priorityHidden) {
        prioritySwitch.addEventListener("change", () => {
            if (prioritySwitch.checked) {
                priorityLabel.textContent = "高";
                priorityDesc.textContent = "2時間ごとに最新価格と在庫数を取得。通知頻度が高めです。";
                priorityHidden.value = "高";
            } else {
                priorityLabel.textContent = "普通";
                priorityDesc.textContent = "24時間ごとに最新価格と在庫数を取得。アプリ通知・メール通知なし。";
                priorityHidden.value = "普通";
            }
        });
    }
});
