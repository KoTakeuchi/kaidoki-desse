document.addEventListener("DOMContentLoaded", function () {
    console.log("🚀 DOMContentLoaded - スクリプト開始");

    // ========================================
    // Canvas要素取得
    // ========================================
    const ctx = document.getElementById("priceChart");
    if (!ctx) {
        console.error("❌ Canvas要素が見つかりません");
        return;
    }
    console.log("✅ Canvas要素取得成功:", ctx);

    // ========================================
    // JSONデータ取得
    // ========================================
    const jsonEl = document.getElementById("price-data-json");
    if (!jsonEl) {
        console.error("❌ JSON要素が見つかりません");
        return;
    }

    // ========================================
    // JSONパース
    // ========================================
    let priceData;
    try {
        priceData = JSON.parse(jsonEl.textContent);
        console.log("✅ JSON解析成功");
    } catch (e) {
        console.error("❌ JSON解析エラー:", e);
        return;
    }

    if (!Array.isArray(priceData) || priceData.length === 0) {
        console.warn("⚠️ データが空です");
        return;
    }

    console.log("✅ データ検証成功 - データ件数:", priceData.length);

    // ========================================
    // グラフデータ準備
    // ========================================
    const labels = priceData.map(d => d.date);
    const prices = priceData.map(d => parseFloat(d.price));
    const stocks = priceData.map(d => d.stock === 0 ? 0 : d.stock);
    const threshold = priceData[0]?.threshold_value || null;

    // ✅ Y軸範囲の計算：買い時価格を下から40%の位置に
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);

    let yMin, yMax;

    if (threshold) {
        const priceRange = maxPrice - minPrice;
        const margin = Math.max(priceRange * 0.8, 500);

        const rangeBelow = margin / 0.6;
        const rangeAbove = margin / 0.4;

        yMin = threshold - rangeBelow;
        yMax = threshold + rangeAbove;

        if (yMin < 0) {
            yMin = 0;
            yMax = threshold * 2;
        }

        yMin = Math.floor(yMin / 500) * 500;
        yMax = Math.ceil(yMax / 500) * 500;
    } else {
        yMin = 0;
        yMax = Math.ceil(maxPrice * 1.2 / 500) * 500;
    }

    console.log("📊 Y軸範囲:", yMin, "～", yMax);
    console.log("📊 買い時価格:", threshold);

    // ========================================
    // データセット構築
    // ========================================
    const datasets = [
        {
            type: "bar",
            label: "在庫数",
            data: stocks,
            backgroundColor: "rgba(60, 169, 169, 0.5)",
            borderWidth: 0,
            yAxisID: "y2",
            order: 3,
        },
        {
            type: "line",
            label: "価格（円）",
            data: prices,
            borderColor: "#C35656",
            backgroundColor: "rgba(195, 86, 86, 0.1)",
            borderWidth: 2,
            tension: 0.3,
            yAxisID: "y",
            order: 2,
            pointBackgroundColor: prices.map(p =>
                threshold && p <= threshold ? '#FF3333' : '#C35656'
            ),
            pointRadius: prices.map(p =>
                threshold && p <= threshold ? 5 : 3
            ),
            pointHoverRadius: 7,
        },
    ];

    if (threshold !== null && threshold !== undefined) {
        datasets.push({
            type: "line",
            label: "買い時価格",
            data: Array(labels.length).fill(threshold),
            borderColor: "#F7CB6E",
            borderWidth: 3,
            borderDash: [8, 4],
            pointRadius: 0,
            yAxisID: "y",
            order: 1,
        });
    }

    // ========================================
    // Chart.js描画
    // ========================================
    console.log("🎨 Chart.js描画開始");

    // ✅ 最初は最新30日のみ表示
    const displayStart = Math.max(0, labels.length - 30);

    new Chart(ctx, {
        data: {
            labels: labels,
            datasets: datasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: "日付（← スクロールで過去表示）" },
                    // ✅ 最初は最新30日のみ
                    min: displayStart,
                    max: labels.length - 1,
                    ticks: {
                        maxRotation: 0,
                        autoSkip: true,  // ✅ 自動スキップに変更（30日分表示）
                        maxTicksLimit: 30,
                        font: { size: 9 },
                        callback: function (value, index) {
                            const dateStr = labels[value];  // ✅ value を使用
                            if (!dateStr) return '';

                            const [year, month, day] = dateStr.split('-');

                            // 最初の日付は年号付き
                            if (value === 0) {
                                return [year, `${month}-${day}`];
                            }

                            // 年が変わったときだけ年号表示
                            if (value > 0) {
                                const prevDateStr = labels[value - 1];
                                if (prevDateStr) {
                                    const prevYear = prevDateStr.split('-')[0];
                                    if (year !== prevYear) {
                                        return [year, `${month}-${day}`];
                                    }
                                }
                            }

                            // 通常は月と日を2行で表示
                            return [month, day];
                        }
                    },
                    grid: {
                        display: true,
                        drawOnChartArea: true,
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    title: { display: true, text: "価格（円）" },
                    min: yMin,
                    max: yMax,
                    position: "left",
                },
                y2: {
                    title: { display: true, text: "在庫数" },
                    beginAtZero: true,
                    position: "right",
                    grid: { drawOnChartArea: false },
                    ticks: {
                        callback: function (value) {
                            return Math.floor(value);
                        },
                        stepSize: 1,
                        autoSkip: true,
                    }
                },
            },
            plugins: {
                legend: { position: "bottom" },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.dataset.yAxisID === 'y2') {
                                label += Math.floor(context.parsed.y);
                            } else {
                                label += context.parsed.y.toLocaleString() + '円';
                            }
                            return label;
                        }
                    }
                },
                // ✅ 追加：Zoom/Pan機能
                zoom: {
                    pan: {
                        enabled: true,
                        mode: 'x',              // 横方向のみ
                        modifierKey: null,      // 修飾キー不要
                    },
                    zoom: {
                        wheel: {
                            enabled: true,      // マウスホイールでズーム
                        },
                        pinch: {
                            enabled: true,      // ピンチジェスチャー（タッチ）
                        },
                        mode: 'x',              // 横方向のみ
                    },
                    limits: {
                        x: {
                            min: 0,
                            max: labels.length - 1,
                        }
                    }
                }
            },
        },
    });

    console.log("✅ Chart.js描画完了");
    console.log("💡 操作方法：ドラッグで左右スクロール、マウスホイールでズーム");
});
