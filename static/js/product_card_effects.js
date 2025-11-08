// --- START: main/static/js/product_card_effects.js ---
// =============================================================
// 商品一覧カードの動的エフェクト制御
// 対応テンプレート：product_list.html
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ product_card_effects.js 読み込み完了");

    const cards = document.querySelectorAll(".product-card");
    if (!cards.length) return;

    // ---------------------------------------------------------
    // ホバー時エフェクト
    // ---------------------------------------------------------
    cards.forEach((card) => {
        // ✅ 通常ホバー：軽く浮かせて影を強調
        card.addEventListener("mouseenter", () => {
            card.style.transition = "transform 0.2s ease, box-shadow 0.2s ease";
            card.style.transform = "translateY(-3px)";
            card.style.boxShadow = "0 6px 15px rgba(0,0,0,0.1)";
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform = "translateY(0)";
            card.style.boxShadow = "0 3px 6px rgba(0,0,0,0.05)";
        });

        // ✅ 買い時カード（flag_reached）を特別強調
        if (card.classList.contains("border-buytime")) {
            card.style.border = "2px solid #C35656";
            card.style.boxShadow = "0 0 10px rgba(195, 86, 86, 0.4)";
        }

        // ✅ 在庫なしカードを半透明化
        if (card.classList.contains("out-of-stock")) {
            card.style.opacity = "0.7";
            card.style.filter = "grayscale(40%)";
        }
    });

    // ---------------------------------------------------------
    // レスポンシブ対応（狭い画面ではホバー効果オフ）
    // ---------------------------------------------------------
    const mediaQuery = window.matchMedia("(max-width: 768px)");
    const toggleHoverEffect = (mq) => {
        cards.forEach((card) => {
            if (mq.matches) {
                card.style.transition = "none";
                card.style.transform = "none";
                card.style.boxShadow = "none";
            } else {
                card.style.transition = "";
                card.style.boxShadow = "";
            }
        });
    };

    mediaQuery.addEventListener("change", () => toggleHoverEffect(mediaQuery));
    toggleHoverEffect(mediaQuery);
});
// --- END: main/static/js/product_card_effects.js ---
