// =============================
// カテゴリ管理（追加・編集・削除統合版）
// =============================
document.addEventListener("DOMContentLoaded", () => {
    const tableBody = document.querySelector(".category-table tbody");
    if (!tableBody) return;

    const createBtn = document.getElementById("confirmCreateBtn");
    const createInput = document.getElementById("createCategoryInput");
    const editBtn = document.getElementById("confirmEditBtn");
    const editInput = document.getElementById("editCategoryInput");
    const deleteBtn = document.getElementById("confirmDeleteBtn");

    let targetId = null;
    let editId = null;

    // =============================
    // 🟢 共通関数（CSRF + 番号再計算）
    // =============================
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function renumberCategoryRows() {
        const rows = tableBody.querySelectorAll("tr");
        rows.forEach((row, index) => {
            const noCell = row.querySelector("td:first-child");
            if (noCell) noCell.textContent = index + 1;
        });
    }

    // =============================
    // 🔁 ボタンイベント再登録（新行にも反映）
    // =============================
    function attachModalEvents() {
        document.querySelectorAll("[data-bs-target='#editModal']").forEach((btn) => {
            btn.onclick = () => {
                editId = btn.getAttribute("data-id");
                const currentName = btn.getAttribute("data-name");
                if (editInput) editInput.value = currentName || "";
            };
        });

        document.querySelectorAll("[data-bs-target='#deleteModal']").forEach((btn) => {
            btn.onclick = () => {
                targetId = btn.getAttribute("data-id");
            };
        });
    }

    // =============================
    // 🧩 カテゴリ上限制御（最大5件）
    // =============================
    const addButton = document.querySelector("[data-bs-target='#createModal']");

    function updateAddButtonState() {
        const rowCount = tableBody.querySelectorAll("tr").length;
        if (addButton) {
            const disabled = rowCount >= 5;
            addButton.disabled = disabled;
            addButton.classList.toggle("disabled", disabled);
            addButton.style.opacity = disabled ? "0.6" : "1";
            addButton.style.pointerEvents = disabled ? "none" : "auto";
        }
    }

    updateAddButtonState();
    const observer = new MutationObserver(updateAddButtonState);
    observer.observe(tableBody, { childList: true });

    // =============================
    // 🟥 カテゴリ追加
    // =============================
    if (createBtn && createInput) {
        createBtn.addEventListener("click", async () => {
            const name = createInput.value.trim();
            if (!name) return alert("カテゴリ名を入力してください。");
            if ([...name].length > 10) return alert("カテゴリ名は全角10文字以内で入力してください。");

            try {
                const res = await fetch("/main/api/categories/create/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "X-CSRFToken": getCookie("csrftoken"),
                    },
                    body: new URLSearchParams({ category_name: name }),
                });

                const data = await res.json();

                if (data.success) {
                    const newRow = document.createElement("tr");
                    const currentRows = tableBody.querySelectorAll("tr").length + 1;

                    newRow.innerHTML = `
                        <td>${currentRows}</td>
                        <td>${data.category_name}</td>
                        <td><span class="badge bg-light text-dark border border-secondary-subtle">0</span></td>
                        <td>
                            <button class="btn btn-outline-secondary btn-sm me-1 rounded-pill"
                                data-bs-toggle="modal"
                                data-bs-target="#editModal"
                                data-id="${data.id}"
                                data-name="${data.category_name}">
                                編集
                            </button>
                            <button class="btn btn-outline-danger btn-sm rounded-pill"
                                data-bs-toggle="modal"
                                data-bs-target="#deleteModal"
                                data-id="${data.id}">
                                削除
                            </button>
                        </td>
                    `;
                    tableBody.appendChild(newRow);
                    renumberCategoryRows();
                    attachModalEvents(); // 新規行にもイベント再登録
                    disableUncategorizedButtons(); // ← 🟢 追加：未分類対策の即時適用

                    bootstrap.Modal.getInstance(document.getElementById("createModal")).hide();
                    createInput.value = "";
                } else {
                    alert(data.error || "登録に失敗しました。");
                }
            } catch {
                alert("通信エラーが発生しました。");
            }
        });
    }

    // =============================
    // 🟦 カテゴリ編集
    // =============================
    attachModalEvents();

    if (editBtn) {
        editBtn.addEventListener("click", async () => {
            const newName = editInput?.value.trim();
            if (!newName) return alert("カテゴリ名を入力してください。");
            if ([...newName].length > 10) return alert("カテゴリ名は全角10文字以内で入力してください。");

            try {
                const res = await fetch(`/main/api/categories/update/${editId}/`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "X-CSRFToken": getCookie("csrftoken"),
                    },
                    body: new URLSearchParams({ category_name: newName }),
                });

                const data = await res.json();

                if (data.success) {
                    const row = document.querySelector(`[data-id='${editId}']`)?.closest("tr");
                    if (row) {
                        row.querySelector("td:nth-child(2)").textContent = data.category_name;
                        const editButton = row.querySelector("[data-bs-target='#editModal']");
                        if (editButton) editButton.setAttribute("data-name", data.category_name);
                    }
                    bootstrap.Modal.getInstance(document.getElementById("editModal")).hide();
                } else {
                    alert(data.error || "更新に失敗しました。");
                }
            } catch {
                alert("通信エラーが発生しました。");
            }
        });
    }

    // =============================
    // 🟥 カテゴリ削除
    // =============================
    if (deleteBtn) {
        deleteBtn.addEventListener("click", async () => {
            if (!targetId) return;

            try {
                const res = await fetch(`/main/api/categories/delete/${targetId}/`, {
                    method: "POST",
                    headers: { "X-CSRFToken": getCookie("csrftoken") },
                });

                const data = await res.json();

                if (data.success) {
                    const row = document.querySelector(`[data-id='${targetId}']`)?.closest("tr");
                    if (row) row.remove();
                    renumberCategoryRows();
                    bootstrap.Modal.getInstance(document.getElementById("deleteModal")).hide();
                } else {
                    alert(data.error || "削除に失敗しました。");
                }
            } catch {
                alert("通信エラーが発生しました。");
            }
        });
    }
    // =============================
    // 🟥 カテゴリ削除（確認強化版）
    // =============================
    const deleteInput = document.getElementById("deleteConfirmInput");

    document.querySelectorAll("[data-bs-target='#deleteModal']").forEach((btn) => {
        btn.addEventListener("click", () => {
            targetId = btn.getAttribute("data-id");
            const nameCell = btn.closest("tr")?.querySelector("td:nth-child(2)");
            const catName = nameCell ? nameCell.textContent.trim() : "";

            if (deleteInput) {
                deleteInput.value = "";
                deleteInput.placeholder = `「${catName}」と入力`;
                deleteBtn.disabled = true;

                // 入力監視（正しいカテゴリ名でのみ削除可能）
                deleteInput.oninput = () => {
                    deleteBtn.disabled = deleteInput.value.trim() !== catName;
                };
            }
        });
    });
    // =============================
    // ✨ 入力バリデーション（リアルタイム）
    // =============================
    function setupLiveValidation(inputElement, confirmButton) {
        if (!inputElement || !confirmButton) return;

        inputElement.addEventListener("input", () => {
            const value = inputElement.value.trim();
            const length = [...value].length;

            // 入力なし or 10文字超 → 警告
            if (length === 0 || length > 10) {
                inputElement.classList.add("is-invalid");
                confirmButton.disabled = true;
            } else {
                inputElement.classList.remove("is-invalid");
                confirmButton.disabled = false;
            }
        });
    }

    // 🟢 適用対象：追加・編集モーダル
    setupLiveValidation(createInput, createBtn);
    setupLiveValidation(editInput, editBtn);

    // =============================
    // 🧩 未分類カテゴリの編集・削除ボタンを無効化
    // =============================
    function disableUncategorizedButtons() {
        document.querySelectorAll(".category-table tbody tr").forEach(row => {
            const nameCell = row.querySelector("td:nth-child(2)");
            if (nameCell && nameCell.textContent.trim() === "未分類") {
                row.querySelectorAll("button").forEach(btn => {
                    btn.disabled = true;
                    btn.classList.add("disabled");
                    btn.style.opacity = "0.6";
                    btn.style.pointerEvents = "none";
                });
            }
        });
    }

    disableUncategorizedButtons(); // 初期ロード時も実行
});
