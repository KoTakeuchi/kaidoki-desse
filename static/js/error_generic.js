// ============================================
// 機能概要: システムエラー画面の基本挙動制御
// ・ページ読み込み時に軽いフェードイン
// ・「ページ上部へ戻る」ボタン動作を共通化
// 対応テンプレート: error_generic.html
// ============================================

document.addEventListener("DOMContentLoaded", () => {
    // フェードインアニメーション
    document.body.style.opacity = 0;
    document.body.style.transition = "opacity 0.5s ease";
    requestAnimationFrame(() => {
        document.body.style.opacity = 1;
    });

    // 上に戻るボタン（base.html共通要素）
    const scrollBtn = document.getElementById("scrollTopBtn");
    if (scrollBtn) {
        window.addEventListener("scroll", () => {
            scrollBtn.style.display = window.scrollY > 200 ? "block" : "none";
        });
        scrollBtn.addEventListener("click", () => {
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }
});
