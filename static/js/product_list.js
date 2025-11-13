
// =============================================================
// 商品一覧ページ：一括削除・クリック遷移制御（最終整合版）
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ product_list.js 読み込み完了");

    const bulkDeleteBtn = document.getElementById("bulkDeleteBtn");
    const bulkDeleteForm = document.getElementById("bulk-delete-form");
    const deleteModal = document.getElementById("deleteModal");
    const checkboxes = document.querySelectorAll(".bulk-check");
    const cards = document.querySelectorAll(".product-card");

    // =========================================================
    // 商品カードクリック → 詳細ページ遷移
    // =========================================================
    cards.forEach((card) => {
        const url = card.dataset.url;
        if (!url) return;

        card.addEventListener("click", (e) => {
            // ✅ チェックボックス・リンク・ボタンはクリック無効化
            if (
                e.target.classList.contains("bulk-check") ||
                e.target.closest("a") ||
                e.target.tagName === "BUTTON"
            ) {
                return;
            }
            window.location.href = url;
        });
    });

    // =========================================================
    // 一括削除ボタンの表示制御
    // =========================================================
    const updateDeleteButton = () => {
        const checkedCount = document.querySelectorAll(".bulk-check:checked").length;
        if (checkedCount > 0) {
            bulkDeleteBtn.style.display = "inline-block";
            bulkDeleteBtn.textContent = `一括削除 (${checkedCount})`;
        } else {
            bulkDeleteBtn.style.display = "none";
        }
    };

    checkboxes.forEach((cb) => {
        cb.addEventListener("change", updateDeleteButton);
    });

    // =========================================================
    // モーダル表示時：選択件数を反映
    // =========================================================
    if (deleteModal) {
        deleteModal.addEventListener("show.bs.modal", () => {
            const checkedCount = document.querySelectorAll(".bulk-check:checked").length;
            const msg = deleteModal.querySelector(".modal-body");
            if (msg) msg.textContent = `選択した商品を削除しますか？（${checkedCount}件）`;
        });
    }

    // =========================================================
    // モーダル内「削除」ボタン押下 → 選択なし防止
    // =========================================================
    if (bulkDeleteForm) {
        bulkDeleteForm.addEventListener("submit", (e) => {
            const checked = document.querySelectorAll(".bulk-check:checked");
            if (checked.length === 0) {
                e.preventDefault();
                alert("削除する商品を選択してください。");
            }
        });
    }

    // =========================================================
    // ページ離脱前の確認（チェック残り警告）
    // =========================================================
    window.addEventListener("beforeunload", (e) => {
        const checkedCount = document.querySelectorAll(".bulk-check:checked").length;
        if (checkedCount > 0) {
            e.preventDefault();
            e.returnValue = "チェック済みの商品があります。ページを離れますか？";
        }
    });
});
// =========================================================
// 並び替えドロップダウンをクリックで切り替え
// =========================================================
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector(".sort-button");
    const menu = toggle?.nextElementSibling;
    if (toggle && menu) {
        toggle.addEventListener("click", (e) => {
            e.preventDefault();
            menu.classList.toggle("show");
        });
        document.addEventListener("click", (e) => {
            if (!toggle.contains(e.target) && !menu.contains(e.target)) {
                menu.classList.remove("show");
            }
        });
    }
});

// =========================================================
// 並び替えドロップダウンをBootstrap標準で制御
// =========================================================
document.addEventListener("DOMContentLoaded", () => {
    const sortDropdown = document.querySelector(".sort-dropdown");
    if (!sortDropdown) return;

    // BootstrapのDropdownインスタンスを自動初期化
    const dropdownTriggerList = [].slice.call(sortDropdown.querySelectorAll('[data-bs-toggle="dropdown"]'));
    dropdownTriggerList.map(function (dropdownTriggerEl) {
        return new bootstrap.Dropdown(dropdownTriggerEl);
    });
});

// =========================================================
// 絞り込み条件リセット回避
// =========================================================

document.addEventListener("DOMContentLoaded", function () {
    const sortOptions = document.querySelectorAll(".sort-option");
    const filterForm = document.querySelector(".filter-card");

    sortOptions.forEach(option => {
        option.addEventListener("click", () => {
            const sortValue = option.dataset.value;
            const hiddenInput = document.createElement("input");
            hiddenInput.type = "hidden";
            hiddenInput.name = "sort";
            hiddenInput.value = sortValue;

            // 既にsortがあれば削除してから追加
            const existing = filterForm.querySelector("input[name='sort']");
            if (existing) existing.remove();
            filterForm.appendChild(hiddenInput);

            filterForm.submit();
        });
    });
});
