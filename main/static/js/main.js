// ===============================
// 商品一覧ページ用メインスクリプト（整理版）
// ===============================
document.addEventListener("DOMContentLoaded", function () {

  // ---------------------------------
  // 🟥 商品カードクリックで詳細ページへ遷移
  // ---------------------------------
  document.querySelectorAll(".product-card").forEach(card => {
    card.addEventListener("click", function (e) {
      // チェックボックスやリンク押下時は除外
      if (e.target.tagName.toLowerCase() === "input" || e.target.closest("a")) return;
      const href = this.getAttribute("data-href");
      if (href) window.location.href = href;
    });
  });


  // ---------------------------------
  // ✅ 一括削除関連
  // ---------------------------------
  const checkboxes = document.querySelectorAll(".card-select");
  const deleteBtn = document.getElementById("bulk-delete-btn");
  const deleteForm = document.getElementById("bulk-delete-form");

  // --- ボタン表示制御 ---
  const updateDeleteButton = () => {
    const checked = [...checkboxes].some(cb => cb.checked);
    deleteBtn.style.display = checked ? "inline-block" : "none";
  };

  checkboxes.forEach(cb => cb.addEventListener("change", updateDeleteButton));


  // ---------------------------------
  // 🟡 モーダル制御（削除確認）
  // ---------------------------------
  const deleteModal = document.getElementById("confirmDeleteModal");
  if (deleteModal) {
    deleteModal.addEventListener("show.bs.modal", () => {
      const selected = [...checkboxes].filter(cb => cb.checked).map(cb => cb.value);
      const form = document.getElementById("bulk-delete-form");

      // 既存hidden削除
      form.querySelectorAll('input[name="selected_products"][type="hidden"]').forEach(e => e.remove());

      // 新規hidden追加
      selected.forEach(id => {
        const hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = "selected_products";
        hidden.value = id;
        form.appendChild(hidden);
      });
    });
  }


  // ---------------------------------
  // 🔴 一括削除送信処理
  // ---------------------------------
  if (deleteForm) {
    deleteForm.addEventListener("submit", e => {
      e.preventDefault();

      const selected = [...checkboxes].filter(c => c.checked).map(c => c.value);
      if (!selected.length) return;

      // hidden要素再作成（安全対策）
      deleteForm.querySelectorAll('input[name="selected_products"][type="hidden"]').forEach(e => e.remove());
      selected.forEach(id => {
        const hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = "selected_products";
        hidden.value = id;
        deleteForm.appendChild(hidden);
      });

      deleteForm.submit();
    });
  }

});
