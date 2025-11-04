// ============================
// 🔔 ヘッダー通知件数の自動更新
// ============================
document.addEventListener("DOMContentLoaded", () => {
    const badgeElem = document.getElementById("unread-count-badge");
    if (!badgeElem) return;

    async function fetchUnreadCount() {
        try {
            const res = await fetch("/notifications/unread_count/");
            if (!res.ok) throw new Error("Fetch error");
            const data = await res.json();

            const count = data.unread_count || 0;
            if (count > 0) {
                badgeElem.textContent = count;
                badgeElem.classList.remove("d-none");
            } else {
                badgeElem.classList.add("d-none");
            }
        } catch (err) {
            console.error("未読件数の取得に失敗:", err);
        }
    }

    // 初回実行
    fetchUnreadCount();

    // 60秒ごとに自動更新
    setInterval(fetchUnreadCount, 60000);
});
