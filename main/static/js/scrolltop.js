(() => {
  console.log("🟡 scrolltop.js 読み込み確認済み [static/js/scrolltop.js]");

  const scrollTopBtn = document.getElementById("scrollTopBtn");
  if (!scrollTopBtn) {
    console.warn("⚠️ scrollTopBtn が見つかりません。");
    return;
  }

  // === スクロール要素を特定 ===
  let scrollContainer = window;

  const testScrollTargets = [
    document.scrollingElement,
    document.documentElement,
    document.body,
    document.querySelector("main"),
    document.querySelector(".page-wrapper"),
  ];

  for (const el of testScrollTargets) {
    if (!el) continue;
    const scrollHeight = el.scrollHeight;
    const clientHeight = el.clientHeight;
    if (scrollHeight > clientHeight + 50) {
      scrollContainer = el;
      break;
    }
  }

  const hero =
    document.querySelector("#section-intro") ||
    document.querySelector("#heroCarousel");

  const heroHeight = hero?.offsetHeight || window.innerHeight;
  const threshold = heroHeight * 1.5;

  console.log("✅ ScrollTop 初期化:", {
    heroHeight,
    threshold,
    container:
      scrollContainer === window
        ? "window"
        : scrollContainer.tagName || scrollContainer.className,
  });

  // === スクロール位置取得 ===
  const getScrollY = () => {
    if (scrollContainer === window) return window.scrollY;
    return scrollContainer.scrollTop || document.documentElement.scrollTop || 0;
  };

  // === スクロール監視 ===
  const handleScroll = () => {
    const scrollY = getScrollY();
    const show = scrollY > threshold;
    scrollTopBtn.classList.toggle("show", show);
    console.log("scrollY:", scrollY);
  };

  // === 主要ターゲットにイベントを付与 ===
  scrollContainer.addEventListener("scroll", handleScroll, { passive: true });
  document.addEventListener("scroll", handleScroll, { passive: true }); // fallback

  // 初回実行
  handleScroll();

  // === クリックで上に戻る ===
  scrollTopBtn.addEventListener("click", () => {
    if (scrollContainer === window) {
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      scrollContainer.scrollTo({ top: 0, behavior: "smooth" });
    }
  });
})();
