// =============================
// 🔔 未読通知バッジ自動更新
// =============================
document.addEventListener("DOMContentLoaded", () => {
    const badge = document.getElementById("unread-badge");

    if (!badge) {
        console.warn("⚠️ unread-badge 要素が見つかりません");
        return;
    }

    async function updateUnreadCount() {
        try {
            console.log("📡 未読件数を取得中...");
            const res = await fetch("/main/api/unread_count/");

            if (!res.ok) {
                throw new Error("HTTPエラー: " + res.status);
            }

            const data = await res.json();
            console.log("✅ API Response:", data);

            const count = data.unread_count || 0;
            console.log("📊 未読件数:", count);

            if (count > 0) {
                badge.style.display = "inline-block";
                badge.textContent = count;
                console.log("✅ バッジ更新完了:", count);
            } else {
                badge.style.display = "none";
                console.log("ℹ️ 未読なし - バッジ非表示");
            }
        } catch (err) {
            console.error("❌ 未読件数取得エラー:", err);
        }
    }

    // 初回実行 + 30秒ごとに更新
    updateUnreadCount();
    setInterval(updateUnreadCount, 30000);
});
