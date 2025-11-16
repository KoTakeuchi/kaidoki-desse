// =============================
// 通知一覧（notifications.html）
// フィルタリングと一括既読処理
// =============================

// ✅ 重複実行を防ぐ
if (window.notificationListInitialized) {
    console.log('notification_list.js is already initialized');
} else {
    window.notificationListInitialized = true;

    document.addEventListener('DOMContentLoaded', () => {
        const filterSelect = document.getElementById('notificationFilter');
        const notificationItems = document.querySelectorAll('.notification-item');
        const markAllReadBtn = document.getElementById('markAllReadBtn');

        // ✅ 件数カウント
        let buyTimeCount = 0;
        let stockCount = 0;

        notificationItems.forEach(item => {
            const type = item.getAttribute('data-type');
            if (type === 'buy_time') buyTimeCount++;
            if (type === 'stock') stockCount++;
        });

        // ✅ セレクトボックスの件数を更新
        if (filterSelect) {
            filterSelect.options[1].text = `買い時通知 (${buyTimeCount})`;
            filterSelect.options[2].text = `在庫通知 (${stockCount})`;
        }

        // ✅ フィルタリング
        if (filterSelect) {
            filterSelect.addEventListener('change', () => {
                const selectedValue = filterSelect.value;

                notificationItems.forEach(item => {
                    const itemType = item.getAttribute('data-type');

                    if (selectedValue === 'all') {
                        item.style.display = '';
                    } else if (selectedValue === itemType) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        }

        // ✅ 一括既読ボタン
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', async () => {
                if (!confirm('すべての通知を既読にしますか？')) return;

                const notificationIds = Array.from(notificationItems).map(item => item.getAttribute('data-id'));

                try {
                    const response = await fetch('/main/api/notifications/mark-all-read/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken'),
                        },
                        body: JSON.stringify({ notification_ids: notificationIds }),
                    });

                    if (response.ok) {
                        location.reload();
                    } else {
                        alert('既読処理に失敗しました。');
                    }
                } catch (error) {
                    console.error(error);
                    alert('通信エラーが発生しました。');
                }
            });
        }

        // CSRF Token取得
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return '';
        }
    });
}
