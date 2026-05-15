document.addEventListener("DOMContentLoaded", function () {

    // zoom プラグイン登録
    if (typeof ChartZoom !== 'undefined') {
        Chart.register(ChartZoom);
    }

    // ========================================
    // 要素取得
    // ========================================
    const ctx = document.getElementById("priceChart");
    if (!ctx) { console.error("❌ Canvas要素が見つかりません"); return; }

    const jsonEl = document.getElementById("price-data-json");
    if (!jsonEl) { console.error("❌ JSON要素が見つかりません"); return; }

    const priorityEl = document.getElementById("product-priority");
    const priority = priorityEl ? JSON.parse(priorityEl.textContent) : "普通";

    // ========================================
    // JSONパース
    // ========================================
    let priceData;
    try {
        priceData = JSON.parse(jsonEl.textContent);
    } catch (e) {
        console.error("❌ JSON解析エラー:", e);
        return;
    }

    if (!Array.isArray(priceData) || priceData.length === 0) {
        console.warn("⚠️ データが空です");
        return;
    }

    const threshold = priceData[0]?.threshold_value || null;

    // ========================================
    // データ集約関数
    // ========================================

    // 日次集約（最安値）
    function aggregateByDay(data) {
        const map = {};
        data.forEach(d => {
            const day = d.date.split(' ')[0]; // YYYY-MM-DD
            if (!map[day] || d.price < map[day].price) {
                map[day] = { ...d, date: day };
            }
        });
        return Object.values(map).sort((a, b) => a.date.localeCompare(b.date));
    }

    // 週次集約（最安値）
    function aggregateByWeek(data) {
        const map = {};
        data.forEach(d => {
            const date = new Date(d.date.split(' ')[0]);
            const day = date.getDay();
            const diff = date.getDate() - day + (day === 0 ? -6 : 1);
            const monday = new Date(date.setDate(diff));
            const key = monday.toISOString().split('T')[0];
            if (!map[key] || d.price < map[key].price) {
                map[key] = { ...d, date: key };
            }
        });
        return Object.values(map).sort((a, b) => a.date.localeCompare(b.date));
    }

    // 期間フィルタ
    function filterByDays(data, days) {
        if (days === null) return data;
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - days);
        return data.filter(d => new Date(d.date.split(' ')[0]) >= cutoff);
    }

    // ========================================
    // 表示データ生成（期間＋粒度を連動）
    // ========================================
    function buildDisplayData(mode) {
        // mode: '7d' | '30d' | 'all'
        let data;

        if (mode === '7d') {
            const filtered = filterByDays(priceData, 7);
            if (priority === '高') {
                // 優先度高：2時間毎・全件
                data = filtered;
            } else {
                // 優先度普通：1日1件
                data = aggregateByDay(filtered);
            }
        } else if (mode === '30d') {
            // 共通：日次・最安値
            data = aggregateByDay(filterByDays(priceData, 30));
        } else {
            // 全期間：週次・最安値
            data = aggregateByWeek(priceData);
        }

        return data.length > 0 ? data : priceData.slice(-1);
    }

    // ========================================
    // Y軸範囲計算
    // ========================================
    function calcYRange(prices) {
        const allValues = threshold ? [...prices, threshold] : prices;
        const dataMin = Math.min(...allValues);
        const dataMax = Math.max(...allValues);
        const margin = Math.max((dataMax - dataMin) * 0.2, 500);
        return {
            yMin: Math.max(0, Math.floor((dataMin - margin) / 500) * 500),
            yMax: Math.ceil((dataMax + margin) / 500) * 500,
        };
    }

    // ========================================
    // グラフ初期化
    // ========================================
    function buildChart(displayData) {
        const labels = displayData.map(d => d.date);
        const prices = displayData.map(d => parseFloat(d.price));
        const stocks = displayData.map(d => d.stock === 0 ? 0 : d.stock);
        const { yMin, yMax } = calcYRange(prices);
        const y2Max = 3;

        const datasets = [
            // 修正後
            {
                type: "line",
                label: "在庫状況",
                data: stocks.map(s => s === 0 ? 0 : s === 1 ? 1 : 3),
                pointStyle: stocks.map(s => s === 0 ? 'crossRot' : s === 1 ? 'triangle' : 'circle'),
                pointBackgroundColor: stocks.map(s => s === 0 ? 'rgba(200,50,50,0.8)' : s === 1 ? 'rgba(255,165,0,0.8)' : 'rgba(100,180,100,0.8)'),
                pointBorderColor: stocks.map(s => s === 0 ? '#c83232' : s === 1 ? '#ffa500' : '#64b464'),
                pointRadius: 8,
                pointHoverRadius: 10,
                borderWidth: 0,
                showLine: false,
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

        if (threshold !== null) {
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

        return new Chart(ctx, {
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: "日付" },
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 30,
                            font: { size: 9 },
                            callback: function (value) {
                                const dateStr = labels[value];
                                if (!dateStr) return '';
                                const datePart = dateStr.split(' ')[0];
                                const timePart = dateStr.split(' ')[1];
                                const [year, month, day] = datePart.split('-');
                                const hour = timePart ? timePart.slice(0, 2) : null;
                                const display = hour ? `${month}/${day} ${hour}時` : `${month}/${day}`;
                                if (value > 0) {
                                    const prevDateStr = labels[value - 1];
                                    if (prevDateStr) {
                                        const prevYear = prevDateStr.split('-')[0];
                                        if (year !== prevYear) {
                                            return [`${year.slice(2)}年`, display];
                                        }
                                    }
                                }
                                return display;
                            }
                        },
                        grid: { color: 'rgba(0, 0, 0, 0.05)' }
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
                        max: y2Max,
                        position: "right",
                        grid: { drawOnChartArea: false },
                        // 修正後（y2のticks）
                        ticks: {
                            callback: v => {
                                if (v === 0) return '売切';
                                if (v === 1) return 'わずか';
                                if (v === 3) return '在庫あり';
                                return '';
                            },
                            stepSize: 1,
                        }
                    },
                },
                plugins: {
                    legend: { position: "bottom" },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                // 修正後
                                if (context.dataset.yAxisID === 'y2') {
                                    const val = Math.floor(context.parsed.y);
                                    if (val === 0) label += '売り切れ';
                                    else if (val === 1) label += 'わずか';
                                    else label += '在庫あり';
                                } else {
                                    label += context.parsed.y.toLocaleString() + '円';
                                }
                                return label;
                            }
                        }
                    },
                    zoom: {
                        pan: { enabled: true, mode: 'x', modifierKey: null },
                        zoom: {
                            wheel: { enabled: true },
                            pinch: { enabled: true },
                            mode: 'x',
                        },
                        limits: { x: { min: 0, max: labels.length - 1 } }
                    }
                },
            },
        });
    }

    // ========================================
    // 初期表示（直近30日）
    // ========================================
    let currentMode = '30d';
    let chart = buildChart(buildDisplayData(currentMode));

    // ========================================
    // ボタン切替
    // ========================================
    document.querySelectorAll('.chart-range-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.chart-range-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentMode = this.dataset.range;
            chart.destroy();
            chart = buildChart(buildDisplayData(currentMode));
        });
    });
});
