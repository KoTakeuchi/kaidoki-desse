export function fadeIn(element, duration = 500) {
  element.style.opacity = 0;
  element.style.transition = `opacity ${duration}ms ease-out`;
  requestAnimationFrame(() => {
    element.style.opacity = 1;
  });
}

export function updateUnreadCount() {
  fetch("/notifications/unread_count/")
    .then(r => r.json())
    .then(d => {
      const badge = document.querySelector("#unread-badge");
      if (!badge) return;
      badge.textContent = d.unread_count;
      badge.style.display = d.unread_count > 0 ? "inline-block" : "none";
    });
}
