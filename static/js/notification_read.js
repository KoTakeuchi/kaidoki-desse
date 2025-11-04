// =============================
// ✅ 通知既読処理（Ajax）＋未読バッジ更新
// =============================
document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".mark-read-btn");
    const badge = document.getElementById("unread-badge");

    if (!buttons.length) return;

    buttons.forEach((btn) => {
        btn.addEventListener("click", async (e) => {
            e.preventDefault();
            const url = btn.getAttribute("href");

            try {
                const res = await fetch(url, { method: "POST", headers: { "X-CSRFToken": getCSRFToken() } });
                const data = await res.json();

                if (data.status === "success") {
                    // ✅ 行をフェードアウトして既読表示
                    const listItem = btn.closest(".list-group-item");
                    if (listItem) {
                        listItem.classList.remove("bg-light", "border-danger");
                        listItem.style.opacity = "0.5";
                    }

                    // ✅ バッジを更新（減算処理）
                    updateUnreadBadge();
                }
            } catch (err) {
                console.error("既読処理エラー:", err);
            }
        });
    });

    // =============================
    // CSRFトークン取得（Django対応）
    // =============================
    function getCSRFToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : "";
    }

    // =============================
    // バッジ再取得関数
    // =============================
    async function updateUnreadBadge() {
        try {
            const res = await fetch("/main/unread_count_api/");
            if (!res.ok) throw new Error("HTTPエラー");
            const data = await res.json();
            const count = data.unread_count || 0;

            if (badge) {
                if (count > 0) {
                    badge.textContent = count;
                    badge.style.display = "inline-block";
                } else {
                    badge.style.display = "none";
                }
            }
        } catch (err) {
            console.error("未読バッジ更新エラー:", err);
        }
    }
});
