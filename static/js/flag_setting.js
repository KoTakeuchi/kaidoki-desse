// static/js/flag_setting.js
document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ flag_setting.js loaded");

  // ============================
  // メール通知のON/OFF切替
  // ============================
  const enabledCheckbox = document.getElementById("id_enabled");
  const emailNotifyTime = document.getElementById("email-notify-time");

  if (enabledCheckbox && emailNotifyTime) {
    const toggleEmailTime = () => {
      emailNotifyTime.style.display = enabledCheckbox.checked ? "block" : "none";
    };
    toggleEmailTime();
    enabledCheckbox.addEventListener("change", toggleEmailTime);
  }
});
