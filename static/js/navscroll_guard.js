/* ===============================
 * LPナビ修正版：ずれ補正 + コンテナ自動判定
 * =============================== */
(() => {
    const log = (...a) => { try { console.debug("[NavFix]", ...a); } catch (_) { } };

    // ---- 実際にスクロールしている要素を検出
    function detectScrollContainer() {
        const testY = 50;
        const els = [
            window,
            document.scrollingElement,
            document.documentElement,
            document.body,
            document.querySelector(".page-wrapper"),
            document.querySelector("main"),
        ].filter(Boolean);

        for (const el of els) {
            try {
                const before = (el === window)
                    ? window.scrollY
                    : el.scrollTop;
                if (el === window) window.scrollTo(0, testY);
                else el.scrollTop = testY;
                const moved = (el === window)
                    ? window.scrollY
                    : el.scrollTop;
                if (Math.abs(moved - before - testY) < 5) continue;
                // 戻す
                if (el === window) window.scrollTo(0, before);
                else el.scrollTop = before;
                log("Detected scroll container:", el);
                return el;
            } catch (_) { }
        }
        return window;
    }

    const scrollTarget = detectScrollContainer();

    // ---- スクロール命令
    function doScroll(y, smooth = true) {
        const opt = { top: y, behavior: smooth ? "smooth" : "auto" };
        try {
            if (scrollTarget === window) window.scrollTo(opt);
            else if (scrollTarget.scrollTo) scrollTarget.scrollTo(opt);
            else scrollTarget.scrollTop = y;
        } catch {
            try {
                if (scrollTarget === window) window.scrollTo(0, y);
                else scrollTarget.scrollTop = y;
            } catch { }
        }
    }

    // ---- 目標位置を正確に取得
    function calcTargetY(el) {
        const rect = el.getBoundingClientRect();
        const scrollY = window.scrollY ||
            document.scrollingElement.scrollTop ||
            document.documentElement.scrollTop ||
            0;
        const header = document.querySelector("header.header-bar");
        const headerH = header ? header.offsetHeight : 0;

        // 要素の実座標（transformの影響除去）
        const realY = rect.top + scrollY - headerH - 5; // 少し余裕を持たせる
        return Math.max(realY, 0);
    }

    // ---- スクロールを確定させる（リトライ補正付き）
    function forceScroll(y) {
        doScroll(y, true);
        setTimeout(() => doScroll(y, true), 50);
        setTimeout(() => doScroll(y, false), 180);
    }

    // ---- クリックイベント
    function onClick(ev) {
        const a = ev.currentTarget;
        const href = a.getAttribute("href");
        if (!href || !href.startsWith("#")) return;
        const target = document.querySelector(href);
        if (!target) return;

        ev.preventDefault();
        ev.stopPropagation();

        const y = calcTargetY(target);
        forceScroll(y);
        try { history.replaceState(null, "", href); } catch { }
    }

    // ---- 初期化
    function init() {
        const links = document.querySelectorAll(".header-nav a[href^='#'], .header-brand[href^='#']");
        links.forEach(a => {
            a.removeEventListener("click", onClick, true);
            a.addEventListener("click", onClick, true);
        });
        log("Nav initialized:", links.length, "links");
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, { once: true });
    } else {
        init();
    }
})();
