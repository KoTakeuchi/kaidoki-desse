document.addEventListener("DOMContentLoaded", function () {

    if (typeof ChartZoom !== 'undefined') {
        Chart.register(ChartZoom);
    }

    const ctx = document.getElementById("priceChart");
    if (!ctx) { console.error("❌ Canvas要素が見つかりません"); return; }

    const jsonEl = document.getElementById("price-data-json");
    if (!jsonEl) { console.error("❌ JSON要素が見つかりません"); return; }

    const priorityEl = document.getElementById("product-priority");
    const priority = priorityEl ? JSON.parse(priorityEl.textContent) : "普通";

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

    function aggregateByDay(data) {
        const map = {};
        data.forEach(d => {
            const day = d.date.split(' ')[0];
            if (!map[day] || d.price < map[day].price) {
                map[day] = { ...d, date: day };
            }
        });
        return Object.values(map).sort((a, b) => a.date.localeCompare(b.date));
    }

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

    function filterByDays(data, days) {
        if (days === null) return data;
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - days);
        return data.filter(d => new Date(d.date.split(' ')[0]) >= cutoff);
    }

    function buildDisplayData(mode) {
        let data;
        if (mode === '7d') {
            const filtered = filterByDays(priceData, 7);
            data = priority === '高' ? filtered : aggregateByDay(filtered);
        } else if (mode === '30d') {
            data = aggregateByDay(filterByDays(priceData, 30));
        } else {
            data = aggregateByWeek(priceData);
        }
        return data.length > 0 ? data : priceData.slice(-1);
    }

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

    function buildChart(displayData) {
        const labels = displayData.map(d => d.date);
        const safeLabels = labels.length === 1 ? [...labels, labels[0]] : labels;
        const prices = displayData.map(d => parseFloat(d.price));
        const stocks = displayData.map(d => d.stock === 0 ? 0 : d.stock);
        const { yMin, yMax } = calcYRange(prices);

        const datasets = [
            {
                type: "line",
                label: "価格（円）",
                data: prices.length === 1 ? [...prices, prices[0]] : prices,
                borderColor: "#C35656",
                backgroundColor: "rgba(195, 86, 86, 0.1)",
                borderWidth: 2,
                tension: 0.3,
                yAxisID: "y",
                order: 2,
                pointStyle: stocks.map(s => s === 0 ? 'crossRot' : s === 1 ? 'triangle' : 'circle'),
                pointBackgroundColor: stocks.map((s, i) => {
                    if (threshold && prices[i] <= threshold) return '#FF3333';
                    return s === 0 ? '#ffffff' : s === 1 ? '#ffffff' : '#C35656';
                }),
                pointBorderColor: '#C35656',
                pointBorderWidth: 2,
                pointRadius: stocks.map(s => s === 0 ? 8 : s === 1 ? 8 : 5),
                pointHoverRadius: 10,
            },
        ];

        if (threshold !== null) {
            datasets.push({
                type: "line",
                label: "買い時価格",
                data: Array(safeLabels.length).fill(threshold),
                borderColor: "#F7CB6E",
                borderWidth: 3,
                borderDash: [8, 4],
                pointRadius: 0,
                tension: 0,
                yAxisID: "y",
                order: 1,
            });
        }

        return new Chart(ctx, {
            data: { labels: safeLabels, datasets },
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
                            font: { size: 13 },
                            callback: function (value, index) {
                                const dateStr = labels[index];
                                if (!dateStr) return '';
                                const datePart = dateStr.split(' ')[0];
                                const timePart = dateStr.split(' ')[1];
                                const [year, month, day] = datePart.split('-');
                                const hour = timePart ? timePart.slice(0, 2) : null;
                                const display = hour ? `${month}/${day} ${hour}時` : `${month}/${day}`;
                                if (index > 0) {
                                    const prevDateStr = labels[index - 1];
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
                },
                plugins: {
                    legend: { display: false },
                    // ✅ 追加：買い時価格ラベルを常時表示
                    annotation: threshold !== null ? {
                        annotations: {
                            thresholdLabel: {
                                type: 'line',
                                yMin: threshold,
                                yMax: threshold,
                                borderColor: 'transparent',
                                borderWidth: 0,
                                label: {
                                    display: true,
                                    content: `買い時 ¥${threshold.toLocaleString()}`,
                                    position: 'end',
                                    backgroundColor: 'rgba(247, 203, 110, 0.9)',
                                    color: '#7a5c00',
                                    font: { size: 11, weight: 'bold' },
                                    padding: 4,
                                    borderRadius: 4,
                                }
                            }
                        }
                    } : {},
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                label += context.parsed.y.toLocaleString() + '円';
                                return label;
                            },
                            afterLabel: function (context) {
                                if (context.dataset.label === '価格（円）') {
                                    const s = stocks[context.dataIndex];
                                    if (s === 0) return '在庫: 売り切れ';
                                    if (s === 1) return '在庫: わずか';
                                    return '在庫: あり';
                                }
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

    let currentMode = '30d';
    let chart = buildChart(buildDisplayData(currentMode));

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
