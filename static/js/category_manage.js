// =============================
// カテゴリ管理（追加・編集・削除 シンプル版）
// =============================

document.addEventListener("DOMContentLoaded", () => {
    const tableBody = document.querySelector(".category-table tbody");

    const createBtn = document.getElementById("confirmCreateBtn");
    const createInput = document.getElementById("createCategoryInput");

    const editBtn = document.getElementById("confirmEditBtn");
    const editInput = document.getElementById("editCategoryInput");

    const deleteModalEl = document.getElementById("deleteModal");
    const deleteBtn = document.getElementById("confirmDeleteBtn");

    const addButton = document.querySelector("[data-bs-target='#createModal']");

    let editId = null;
    let deleteId = null;

    // ---- CSRF ----
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(";").shift();
        return "";
    }

    // ---- 行番号振り直し ----
    function renumberCategoryRows() {
        tableBody.querySelectorAll("tr").forEach((tr, idx) => {
            const cell = tr.querySelector("td:first-child");
            if (cell) cell.textContent = idx + 1;
        });
    }

    // ---- 追加ボタン制御（最大5件） ----
    function updateAddButtonState() {
        if (!addButton) return;
        const rowCount = tableBody.querySelectorAll("tr").length;
        const disabled = rowCount >= 5;
        addButton.disabled = disabled;
        addButton.classList.toggle("disabled", disabled);
        addButton.style.opacity = disabled ? "0.6" : "1";
        addButton.style.pointerEvents = disabled ? "none" : "auto";
    }
    updateAddButtonState();
    new MutationObserver(updateAddButtonState).observe(tableBody, { childList: true });

    // ---- 未分類は編集・削除不可 ----
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
    disableUncategorizedButtons();

    // ---- 入力バリデーション（追加/編集） ----
    function setupLiveValidation(input, button) {
        if (!input || !button) return;
        input.addEventListener("input", () => {
            const v = input.value.trim();
            const len = [...v].length;
            if (len === 0 || len > 10) {
                input.classList.add("is-invalid");
                button.disabled = true;
            } else {
                input.classList.remove("is-invalid");
                button.disabled = false;
            }
        });
    }
    setupLiveValidation(createInput, createBtn);
    setupLiveValidation(editInput, editBtn);

    // ---- 編集モーダル開いたとき ----
    function attachEditEvents() {
        document.querySelectorAll("[data-bs-target='#editModal']").forEach(btn => {
            btn.addEventListener("click", () => {
                editId = btn.getAttribute("data-id");
                const name = btn.getAttribute("data-name") || "";
                if (editInput) editInput.value = name;
            });
        });
    }
    attachEditEvents();

    // ---- 削除モーダル開いたとき（idだけ保持） ----
    function attachDeleteEvents() {
        document.querySelectorAll("[data-bs-target='#deleteModal']").forEach(btn => {
            btn.addEventListener("click", () => {
                deleteId = btn.getAttribute("data-id");
            });
        });
    }
    attachDeleteEvents();

    // ---- カテゴリ追加 ----
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
                if (!data.success) return alert(data.error || "登録に失敗しました。");

                const newRow = document.createElement("tr");
                const currentRows = tableBody.querySelectorAll("tr").length + 1;

                newRow.setAttribute("data-id", data.id);
                newRow.innerHTML = `
                    <td>${currentRows}</td>
                    <td>${data.category_name}</td>
                    <td>
                      <span class="badge bg-light text-dark border border-secondary-subtle">0</span>
                    </td>
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
                          data-id="${data.id}"
                          data-name="${data.category_name}">
                          削除
                      </button>
                    </td>
                `;
                tableBody.appendChild(newRow);

                renumberCategoryRows();
                attachEditEvents();
                attachDeleteEvents();
                disableUncategorizedButtons();

                const createModalEl = document.getElementById("createModal");
                if (createModalEl) bootstrap.Modal.getInstance(createModalEl)?.hide();
                createInput.value = "";
            } catch (e) {
                console.error(e);
                alert("通信エラーが発生しました。");
            }
        });
    }

    // ---- カテゴリ編集 ----
    if (editBtn && editInput) {
        editBtn.addEventListener("click", async () => {
            const newName = editInput.value.trim();
            if (!newName) return alert("カテゴリ名を入力してください。");
            if ([...newName].length > 10) return alert("カテゴリ名は全角10文字以内で入力してください。");
            if (!editId) return;

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
                if (!data.success) return alert(data.error || "更新に失敗しました。");

                const row = document.querySelector(`tr[data-id='${editId}']`);
                if (row) {
                    row.querySelector("td:nth-child(2)").textContent = data.category_name;
                    const editButton = row.querySelector("[data-bs-target='#editModal']");
                    const deleteButton = row.querySelector("[data-bs-target='#deleteModal']");
                    if (editButton) editButton.setAttribute("data-name", data.category_name);
                    if (deleteButton) deleteButton.setAttribute("data-name", data.category_name);
                }

                const editModalEl = document.getElementById("editModal");
                if (editModalEl) bootstrap.Modal.getInstance(editModalEl)?.hide();
            } catch (e) {
                console.error(e);
                alert("通信エラーが発生しました。");
            }
        });
    }

    // ---- カテゴリ削除（入力確認なし） ----
    if (deleteBtn && deleteModalEl) {
        deleteBtn.addEventListener("click", async () => {
            if (!deleteId) return;

            try {
                const res = await fetch(`/main/api/categories/delete/${deleteId}/`, {
                    method: "POST",
                    headers: { "X-CSRFToken": getCookie("csrftoken") },
                });

                let data;
                try {
                    data = await res.json();
                } catch (e) {
                    const text = await res.text();
                    console.error("サーバーレスポンス(JSONでない):", text);
                    alert("サーバー側でエラーが発生しました。");
                    return;
                }

                if (!data.success) return alert(data.error || "削除に失敗しました。");

                const row = document.querySelector(`tr[data-id='${deleteId}']`);
                if (row) row.remove();
                renumberCategoryRows();

                bootstrap.Modal.getInstance(deleteModalEl)?.hide();
                deleteId = null;
            } catch (e) {
                console.error(e);
                alert("通信エラーが発生しました。");
            }
        });
    }
});
