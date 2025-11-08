// =============================
// 🔔 未読通知バッジ自動更新
// =============================
document.addEventListener("DOMContentLoaded", () => {
    const badge = document.getElementById("unread-badge");
    if (!badge) return;

    async function updateUnreadCount() {
        try {
            const res = await fetch("/main/api/unread_count/");
            if (!res.ok) throw new Error("HTTPエラー: " + res.status);
            const data = await res.json();

            const count = data.unread_count || 0;
            if (count > 0) {
                badge.style.display = "inline-block";
                badge.textContent = count;
            } else {
                badge.style.display = "none";
            }
        } catch (err) {
            console.error("未読件数取得エラー:", err);
        }
    }

    // 初回実行 + 30秒ごとに更新
    updateUnreadCount();
    setInterval(updateUnreadCount, 30000);
});
