document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("priceChart");
    if (!ctx) {
        console.error("Canvasエレメントが見つかりません。");
        return;
    }

    const jsonEl = document.getElementById("price-data-json");
    if (!jsonEl) {
        console.error("価格データのJSONエレメントが見つかりません。");
        return;
    }

    let priceData;
    try {
        priceData = JSON.parse(jsonEl.textContent);
        console.log('価格データ:', priceData);  // データ構造を確認
    } catch (e) {
        console.error("価格データのJSON解析に失敗:", e);
        document.getElementById("priceChart").innerHTML = "<p>価格データの読み込みに失敗しました。</p>";
        return;
    }

    // price_data配列を正しく取得する処理
    if (!Array.isArray(priceData)) {
        console.error("価格データが配列ではありません:", priceData);
        document.getElementById("priceChart").innerHTML = "<p>価格データが配列ではありません。</p>";
        return;
    }

    // labels, prices, stocks, thresholdの取得
    const labels = priceData.map(d => d.date);
    const prices = priceData.map(d => parseFloat(d.price));  // 数値型に変換
    const stocks = priceData.map(d => (d.stock === 0 ? 0 : d.stock));  // 0に変換
    const threshold = priceData[0].threshold_price || Infinity; // 価格データ内の最初の項目の閾値を取得

    console.log('ラベル:', labels);  // ラベルを確認
    console.log('価格データ:', prices);  // 価格データを確認
    console.log('在庫データ:', stocks);  // 在庫データを確認

    // Chart.js の設定
    const chartData = {
        labels: labels,
        datasets: [
            {
                label: "価格",
                data: prices,
                borderColor: "#FF5733", // 価格のラインカラー
                fill: false
            },
            {
                label: "在庫",
                data: stocks,
                borderColor: "#33FF57", // 在庫のラインカラー
                fill: false
            }
        ]
    };

    const chartOptions = {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };

    // グラフ描画処理
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
});
