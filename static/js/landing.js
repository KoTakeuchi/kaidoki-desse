// ================================
// ヘッダー高さをCSS変数へ反映（scroll-padding-top対応）
// Heroの中央崩れ防止も同時に処理
// ================================
(function () {
  const header = document.querySelector('header.header-bar');
  const hero = document.getElementById('heroCarousel');
  if (!header) return;

  const updateHeaderHeight = () => {
    const h = header.getBoundingClientRect().height || 64;
    document.documentElement.style.setProperty('--header-h', `${h}px`);
  };

  updateHeaderHeight();
  window.addEventListener('resize', updateHeaderHeight, { passive: true });
})();

// ================================
// Heroカルーセル（JS制御のみ・方向制御を一元化）
// 仕様：
// 自動／右（Next） → dir-next（現: 右へ / 次: 左→右）
// 左（Prev）       → dir-prev（現: 左へ / 次: 右→左）
// ================================
(function () {
  const el = document.getElementById('heroCarousel');
  if (!el || !window.bootstrap) return;

  // 2重初期化防止
  const existing = bootstrap.Carousel.getInstance(el);
  if (existing) existing.dispose();

  const carousel = new bootstrap.Carousel(el, {
    interval: 7000,
    ride: 'carousel',
    touch: true,
    pause: false,
    wrap: true,
    keyboard: true
  });

  // 方向クラスの付け替えだけを責務にする
  const setDir = (dir) => {
    el.classList.remove('dir-next', 'dir-prev');
    el.classList.add(dir);
  };

  // クリック時：Bootstrapのイベント判定に任せるので、ここでは意図の方向だけセット
  const btnPrev = el.querySelector('.carousel-control-prev');
  const btnNext = el.querySelector('.carousel-control-next');

  if (btnPrev) btnPrev.addEventListener('click', () => setDir('dir-prev'));
  if (btnNext) btnNext.addEventListener('click', () => setDir('dir-next'));

  // 最終確定は slide イベントで行う（自動・スワイプ・キーボードも網羅）
  el.addEventListener('slide.bs.carousel', (e) => {
    // Bootstrap v5: e.direction === 'left' → 次へ（Next）
    //               e.direction === 'right'→ 前へ（Prev）
    if (e.direction === 'left') {
      // 次へ（自動や右ボタンもここに来る）：dir-next
      setDir('dir-next');
    } else {
      // 前へ（左ボタンや右→左スワイプ）：dir-prev
      setDir('dir-prev');
    }
  });
})();
