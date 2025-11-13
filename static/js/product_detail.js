document.addEventListener("DOMContentLoaded", function () {
    console.log('🚀 DOMContentLoaded - スクリプト開始');

    // ======================================================
    // Canvas要素の取得
    // ======================================================
    const ctx = document.getElementById("priceChart");
    if (!ctx) {
        console.error("❌ Canvasエレメントが見つかりません。");
        return;
    }
    console.log('✅ Canvas要素取得成功:', ctx);

    // ======================================================
    // JSON要素の取得
    // ======================================================
    const jsonEl = document.getElementById("price-data-json");
    if (!jsonEl) {
        console.error("❌ 価格データのJSONエレメントが見つかりません。");
        const errorContainer = document.querySelector('.chart-container');
        if (errorContainer) {
            errorContainer.innerHTML = "<p class='text-danger'>価格データが見つかりません。</p>";
        }
        return;
    }
    console.log('✅ JSON要素取得成功:', jsonEl);
    console.log('📝 JSON要素の内容（先頭100文字）:', jsonEl.textContent.substring(0, 100));

    // ======================================================
    // JSONパース
    // ======================================================
    let priceData;
    try {
        const jsonText = jsonEl.textContent.trim();
        console.log('📊 パース前のJSON文字列の長さ:', jsonText.length);
        priceData = JSON.parse(jsonText);
        console.log('✅ JSON解析成功');
        console.log('📊 priceDataの型:', typeof priceData);
        console.log('📊 priceDataの内容:', priceData);
    } catch (e) {
        console.error("❌ 価格データのJSON解析に失敗:", e);
        console.error("❌ エラー詳細:", e.message);
        const errorContainer = document.querySelector('.chart-container');
        if (errorContainer) {
            errorContainer.innerHTML = `<p class='text-danger'>価格データの読み込みに失敗しました。<br>エラー: ${e.message}</p>`;
        }
        return;
    }

    // ======================================================
    // データ型の検証
    // ======================================================
    console.log('🔍 データ検証開始');
    console.log('  - Array.isArray(priceData):', Array.isArray(priceData));
    console.log('  - typeof priceData:', typeof priceData);
    console.log('  - priceData.length:', priceData ? priceData.length : 'undefined');

    if (!Array.isArray(priceData)) {
        console.error("❌ 価格データが配列ではありません:", priceData);
        const errorContainer = document.querySelector('.chart-container');
        if (errorContainer) {
            errorContainer.innerHTML = `<p class='text-danger'>価格データが配列ではありません。<br>型: ${typeof priceData}</p>`;
        }
        return;
    }

    if (priceData.length === 0) {
        console.warn("⚠️ 価格データが空です");
        const errorContainer = document.querySelector('.chart-container');
        if (errorContainer) {
            errorContainer.innerHTML = "<p class='text-muted'>価格履歴がまだありません。</p>";
        }
        return;
    }

    console.log('✅ データ検証成功 - データ件数:', priceData.length);

    // ======================================================
    // グラフ用データの抽出
    // ======================================================
    const labels = priceData.map(d => d.date);
    const prices = priceData.map(d => parseFloat(d.price) || 0);
    const stocks = priceData.map(d => parseInt(d.stock) || 0);

    // threshold_valueを取得（最初のデータポイントから）
    const thresholdValue = priceData[0].threshold_value;
    const threshold = thresholdValue !== null && thresholdValue !== undefined
        ? parseFloat(thresholdValue)
        : null;

    console.log('📊 グラフデータ準備完了:');
    console.log('  - ラベル数:', labels.length);
    console.log('  - 価格データ（先頭5件）:', prices.slice(0, 5));
    console.log('  - 在庫データ（先頭5件）:', stocks.slice(0, 5));
    console.log('  - 閾値:', threshold);

    // ======================================================
    // Chart.js データセット構築
    // ======================================================
    const datasets = [
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
        }
    ];

    // 閾値ラインを追加（threshold が有効な場合のみ）
    if (threshold !== null && threshold > 0) {
        console.log('✅ 閾値ラインを追加:', threshold);
        datasets.push({
            type: "line",
            label: "買い時価格",
            data: Array(labels.length).fill(threshold),
            borderColor: "#F7CB6E",
            borderWidth: 2,
            borderDash: [6, 6],
            pointRadius: 0,
            yAxisID: "y",
            order: 3,
        });
    } else {
        console.log('ℹ️ 閾値が設定されていないため、閾値ラインは表示しません');
    }

    // ======================================================
    // Chart.js 描画実行
    // ======================================================
    try {
        console.log('🎨 Chart.js描画開始');
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: datasets,
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
                    legend: {
                        position: "bottom",
                        labels: {
                            font: { size: 12 },
                            padding: 15
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    },
                },
            },
        });
        console.log('✅ Chart.js描画完了');
    } catch (e) {
        console.error('❌ Chart.js描画エラー:', e);
        console.error('❌ エラー詳細:', e.message);
        const errorContainer = document.querySelector('.chart-container');
        if (errorContainer) {
            errorContainer.innerHTML = `<p class='text-danger'>グラフの描画に失敗しました。<br>エラー: ${e.message}</p>`;
        }
    }
});
