
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

document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ flag_type.js 読み込み完了");

  const flagBtns = document.querySelectorAll(".flag-btn");
  const descBox = document.getElementById("flagDesc");
  const flagTypeHidden = document.getElementById("flagTypeHidden");

  const wrapRegular = document.getElementById("wrap_regular");
  const wrapThreshold = document.getElementById("wrap_threshold");
  const wrapPercent = document.getElementById("wrap_percent");

  const hideAll = () => {
    [wrapRegular, wrapThreshold, wrapPercent].forEach(el => {
      if (el) el.style.display = "none";
    });
  };

  const showWrap = (type) => {
    hideAll();
    if (type === "buy_price") wrapThreshold.style.display = "block";
    if (type === "percent_off") {
      wrapRegular.style.display = "block";
      wrapPercent.style.display = "block";
    }
  };

  flagBtns.forEach(btn => {
    btn.addEventListener("mouseenter", () => {
      descBox.textContent = btn.dataset.desc;
    });

    btn.addEventListener("mouseleave", () => {
      descBox.textContent = "ボタンにマウスを乗せると説明が表示されます。";
    });

    btn.addEventListener("click", () => {
      flagBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const type = btn.dataset.type;
      flagTypeHidden.value = type;
      showWrap(type);
    });
  });

  // 初期表示（フォーム値に合わせて）
  if (flagTypeHidden.value) showWrap(flagTypeHidden.value);
});
// =============================================================
// 通知条件切り替え（買い時価格・割引率・最安値）
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ flag_setting.js loaded");

  const buttons = document.querySelectorAll(".flag-btn");
  const hidden = document.getElementById("flagTypeHidden");

  const wrapThreshold = document.getElementById("wrap_threshold"); // 買い時価格入力欄
  const wrapPercent = document.getElementById("wrap_percent");     // 割引率セレクト欄
  const descBox = document.getElementById("flagDesc");

  if (!buttons.length || !hidden) {
    console.warn("⚠️ 通知条件ボタンまたは hidden が見つかりません。");
    return;
  }

  // 初期状態リセット
  const hideAll = () => {
    if (wrapThreshold) wrapThreshold.style.display = "none";
    if (wrapPercent) wrapPercent.style.display = "none";
  };

  // 種類別表示
  const showWrap = (type) => {
    hideAll();
    switch (type) {
      case "buy_price":
        if (wrapThreshold) wrapThreshold.style.display = "block";
        descBox.textContent = "指定価格以下になったとき通知します。最も基本的な通知方法です。";
        break;
      case "percent_off":
        if (wrapPercent) wrapPercent.style.display = "block";
        descBox.textContent = "登録時価格から指定％OFFになったとき通知します。セールやイベント検知に便利です。";
        break;
      case "lowest_price":
        descBox.textContent = "登録以来の最安値を更新したら通知します。価格履歴に基づいた通知です。";
        break;
      default:
        descBox.textContent = "ボタンにマウスを乗せると説明が表示されます。";
    }
  };

  // 初期表示（hiddenの値が存在する場合）
  if (hidden.value) showWrap(hidden.value);

  // クリックイベント登録
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const type = btn.dataset.type;

      // アクティブ切替
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      // hidden更新
      hidden.value = type;

      // 表示切替
      showWrap(type);
    });
  });
});
