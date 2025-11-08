
// =============================================================
// 通知設定ページ：フラグ設定の同期＆保存
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ flag_setting.js 読み込み完了");

  const form = document.getElementById("flagSettingForm");
  const statusBox = document.getElementById("flag-save-status");

  if (!form) {
    console.warn("⚠️ flagSettingForm が見つかりません。");
    return;
  }

  /**
   * ステータスメッセージ表示
   * @param {string} text
   * @param {"success"|"error"|"info"} type
   */
  const showStatus = (text, type = "info") => {
    if (!statusBox) return;

    statusBox.textContent = text;
    statusBox.className = "alert py-2 text-center mt-2";

    switch (type) {
      case "success":
        statusBox.classList.add("alert-success");
        break;
      case "error":
        statusBox.classList.add("alert-danger");
        break;
      default:
        statusBox.classList.add("alert-secondary");
    }
    statusBox.style.display = "block";

    // 3秒後に自動フェードアウト
    setTimeout(() => {
      statusBox.style.display = "none";
    }, 3000);
  };

  // =========================================================
  // フォーム送信イベント
  // =========================================================
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
    const url = form.action;

    showStatus("🔄 通知設定を保存中です…", "info");

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
        body: formData,
      });

      if (!response.ok) {
        showStatus(`❌ エラーが発生しました（${response.status}）`, "error");
        return;
      }

      const data = await response.json().catch(() => ({}));
      if (data.success) {
        showStatus("✅ 通知設定を保存しました。", "success");
      } else if (data.error) {
        showStatus(`⚠️ ${data.error}`, "error");
      } else {
        showStatus("✅ 設定を更新しました。", "success");
      }
    } catch (err) {
      console.error("通信エラー:", err);
      showStatus("❌ 通信に失敗しました。", "error");
    }
  });
});
