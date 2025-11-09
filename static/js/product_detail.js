document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("priceChart");
    if (!ctx) {
        console.error("Canvasエレメントが見つかりません。");
    } else {
        const jsonEl = document.getElementById("price-data-json");
        if (!jsonEl) {
            console.error("価格データのJSONエレメントが見つかりません。");
        } else {
            let priceData;
            try {
                priceData = JSON.parse(jsonEl.textContent);
            } catch (e) {
                console.error("価格データのJSON解析に失敗:", e);
                priceData = [];
            }

            if (!Array.isArray(priceData) || priceData.length === 0) {
                console.error("価格データが無効です。データが空であるか、形式が不正です。", priceData);
                document.getElementById("priceChart").innerHTML = "<p>価格データの読み込みに失敗しました。</p>";
            } else {
                let isValidData = true;

                for (let i = 0; i < priceData.length; i++) {
                    if (typeof priceData[i].price !== 'number' || typeof priceData[i].stock !== 'number') {
                        console.error(`無効なデータ形式: `, priceData[i]);
                        isValidData = false;
                        break;
                    }
                }

                if (isValidData) {
                    const labels = priceData.map(d => d.date);
                    const prices = priceData.map(d => d.price);
                    const stocks = priceData.map(d => (d.stock === 0 ? 0 : d.stock));  // 0に変換

                    const threshold = typeof window.thresholdValue === "number" ? window.thresholdValue : Infinity; // デフォルトを設定

                    new Chart(ctx, {
                        type: "bar",
                        data: {
                            labels: labels,
                            datasets: [
                                {
                                    type: "bar",
                                    label: "在庫数",
                                    data: stocks,
                                    backgroundColor: "#3ca9a9",
                                    borderWidth: 0,
                                    yAxisID: "y2",
                                    order: 1,
                                },
                                {
                                    type: "line",
                                    label: "価格（円）",
                                    data: prices,
                                    borderColor: "#C35656",
                                    backgroundColor: "rgba(195,86,86,0.2)",
                                    borderWidth: 2,
                                    tension: 0.3,
                                    yAxisID: "y",
                                    order: 2,
                                },
                                {
                                    type: "line",
                                    label: "閾値ライン",
                                    data: Array(labels.length).fill(threshold),
                                    borderColor: "#F7CB6E",
                                    borderWidth: 2,
                                    borderDash: [6, 6],
                                    pointRadius: 0,
                                    yAxisID: "y",
                                    order: 3,
                                },
                            ],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                x: {
                                    title: { display: true, text: "日付" },
                                    ticks: { maxTicksLimit: 10 },
                                },
                                y: {
                                    title: { display: true, text: "価格（円）" },
                                    beginAtZero: true,
                                    position: "left",
                                },
                                y2: {
                                    title: { display: true, text: "在庫数" },
                                    beginAtZero: true,
                                    position: "right",
                                    grid: { drawOnChartArea: false },
                                },
                            },
                            plugins: {
                                legend: { position: "bottom" },
                                zoom: {
                                    zoom: {
                                        wheel: { enabled: true },
                                        pinch: { enabled: true },
                                        mode: "x",
                                    },
                                    pan: {
                                        enabled: true,
                                        mode: "x",
                                    },
                                },
                            },
                        },
                        plugins: [ChartZoom],
                    });
                } else {
                    document.getElementById("priceChart").innerHTML = "<p>価格データの形式に問題があります。</p>";
                }
            }
        }
    }
});
