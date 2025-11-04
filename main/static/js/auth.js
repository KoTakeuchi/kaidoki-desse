document.addEventListener("DOMContentLoaded", function () {
    // ===== 共通関数：パスワード表示切替 =====
    function toggleVisibility(btn) {
        // inputを自動検出（同じpassword-wrapper内）
        const input = btn.closest(".password-wrapper")?.querySelector("input");
        if (!input) return;

        const isPassword = input.type === "password";
        input.type = isPassword ? "text" : "password";

        // アイコン切替
        const icon = btn.querySelector("i");
        if (icon) {
            icon.classList.toggle("fa-eye", isPassword);
            icon.classList.toggle("fa-eye-slash", !isPassword);
        }
    }

    // ===== 全フォーム共通：クリックイベント =====
    document.querySelectorAll(".toggle-password").forEach(function (btn) {
        btn.addEventListener("click", function (ev) {
            ev.preventDefault();
            toggleVisibility(btn);
        });
    });
});
