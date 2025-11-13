
// =============================================================
// 商品詳細ページ：買い時バナー＆状態制御
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ product_banner.js 読み込み完了");

    const banner = document.getElementById("kaidoki-banner");
    const chartElem = document.getElementById("priceChart");
    const priceDataElem = document.getElementById("price-data-json");

    // ---------------------------------------------------------
    // 初期チェック：バナーがなければ終了
    // ---------------------------------------------------------
    if (!banner) return;

    // ---------------------------------------------------------
    // データがなければバナーを非表示
    // ---------------------------------------------------------
    if (!priceDataElem) {
        banner.style.display = "none";
        return;
    }

    // ---------------------------------------------------------
    // JSONデータ解析
    // ---------------------------------------------------------
    let priceData = [];
    try {
        const raw = priceDataElem.textContent.trim().replace(/\n/g, "");
        priceData = JSON.parse(raw);
        if (typeof priceData === "string") priceData = JSON.parse(priceData);
    } catch {
        console.warn("⚠️ 価格データのJSONパースに失敗しました。");
        banner.style.display = "none";
        return;
    }

    if (!Array.isArray(priceData) || priceData.length === 0) {
        banner.style.display = "none";
        return;
    }

    // ---------------------------------------------------------
    // 最新価格としきい値で判定
    // ---------------------------------------------------------
    const latest = priceData[priceData.length - 1];
    const currentPrice = parseFloat(latest.price);
    const threshold = parseFloat(chartElem?.dataset.threshold || "0") || 0;

    if (threshold > 0 && currentPrice <= threshold) {
        // 🎯 買い時
        banner.classList.remove("alert-secondary");
        banner.classList.add("alert-success");
        banner.textContent = "🎯 買い時です！現在の価格が設定した閾値を下回っています。";
        banner.style.display = "block";
    } else {
        // 💤 通常（非買い時）
        banner.style.display = "none";
    }

    // ---------------------------------------------------------
    // 定期的に状態再チェック（価格変化を反映）
    // ---------------------------------------------------------
    setInterval(() => {
        const latestData = window.priceChartInstance?.data?.datasets?.[0]?.data;
        if (!latestData || latestData.length === 0) return;

        const nowPrice = latestData[latestData.length - 1];
        if (threshold > 0 && nowPrice <= threshold) {
            banner.style.display = "block";
            banner.textContent = "🎯 買い時です！";
        } else {
            banner.style.display = "none";
        }
    }, 15000); // 15秒ごとに更新確認
});

