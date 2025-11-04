// 実行ディレクトリ: <Djangoプロジェクト>/static/js/smooth-scroll.js
(() => {
    const header = document.querySelector('header.header-bar');

    // 同一ページ内アンカーだけを対象（ナビ内リンクに限定）
    document.addEventListener('click', (e) => {
        const a = e.target.closest('.header-nav a[href^="#"]');
        if (!a) return;

        const hash = a.getAttribute('href');
        const id = hash.slice(1);
        const target = document.getElementById(id);
        if (!target) return;

        // Ctrl/Meta クリックなどは通常遷移
        if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;

        e.preventDefault();

        // 動的ヘッダー高（既存のスクリプトが更新している実測値）
        const headerH = header ? header.getBoundingClientRect().height : 0;

        // 目標スクロール位置（ページ基準）
        const y = window.pageYOffset + target.getBoundingClientRect().top - headerH;

        // ブラウザ標準のスムースを優先
        try {
            window.scrollTo({ top: y, behavior: 'smooth' });
        } catch {
            // 古いブラウザ用の最小ポリフィル（リクエストアニメ）
            const start = window.pageYOffset;
            const dist = y - start;
            const dur = 450;
            let t0 = null;
            const ease = (t) => t < .5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
            const step = (ts) => {
                if (!t0) t0 = ts;
                const p = Math.min(1, (ts - t0) / dur);
                window.scrollTo(0, start + dist * ease(p));
                if (p < 1) requestAnimationFrame(step);
            };
            requestAnimationFrame(step);
        }

        // URLの # を更新（履歴は積まない）
        history.replaceState(null, '', hash);
    }, { passive: false });
})();
