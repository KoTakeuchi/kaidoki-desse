// ============================================
// 機能概要: 通知設定ページの表示制御スクリプト
// ・メール通知ON/OFFで時刻設定フォームの表示切替
// ・アプリ内通知頻度による時刻設定フォームの表示切替
// 対応テンプレート: flag_setting.html
// ============================================
document.addEventListener("DOMContentLoaded", () => {
  const emailToggle = document.getElementById("id_enabled");
  const emailTime = document.getElementById("email-notify-time");
  const appFrequency = document.getElementById("id_app_notify_frequency");
  const appTime = document.getElementById("app-notify-time");

  if (!emailToggle || !emailTime || !appFrequency || !appTime) return;

  const updateVisibility = () => {
    emailTime.style.display = emailToggle.checked ? "flex" : "none";
    appTime.style.display = appFrequency.value === "daily" ? "flex" : "none";
  };

  emailToggle.addEventListener("change", updateVisibility);
  appFrequency.addEventListener("change", updateVisibility);
  updateVisibility();
});
