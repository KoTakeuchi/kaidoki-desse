// =============================
// 商品詳細ページ：買い時バナー演出
// =============================
document.addEventListener("DOMContentLoaded", () => {
    const banner = document.getElementById("kaidoki-banner");
    if (!banner) return;

    // 初期状態（CSS側に定義済み）
    banner.style.opacity = "0";
    banner.style.transform = "scale(0.95)";
    banner.style.transition = "opacity 0.8s ease-out, transform 0.8s ease-out";

    // フェードイン＋拡大演出
    setTimeout(() => {
        banner.style.opacity = "1";
        banner.style.transform = "scale(1)";
    }, 200);
});
