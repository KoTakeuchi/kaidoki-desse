// =============================
// 商品詳細ページ：価格 × 在庫推移グラフ描画
// =============================
document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.getElementById("priceChart");
    const jsonElem = document.getElementById("price-data-json");
    if (!canvas || !jsonElem) return;

    let priceData = [];
    try {
        const rawText = jsonElem.textContent.replace(/\n/g, "").trim();
        priceData = JSON.parse(rawText);
        if (typeof priceData === "string") priceData = JSON.parse(priceData);
    } catch {
        console.warn("価格データのパースに失敗しました。");
        return;
    }

    // 🔹 空データ対策
    if (!Array.isArray(priceData) || priceData.length === 0) {
        if (canvas.parentElement) {
            canvas.parentElement.insertAdjacentHTML(
                "beforebegin",
                "<p class='text-center text-muted mb-0 py-4'>価格履歴データがまだありません。</p>"
            );
            canvas.remove();
        }
        return;
    }

    // ...（既存のChart.js描画処理）...
});


// =============================
// データ整形
// =============================
const labels = priceData.map(p => p.date);
const prices = priceData.map(p => parseFloat(p.price));
const stocks = priceData.map(p => parseFloat(p.stock ?? p.stock_count ?? 0));

const threshold = parseFloat(canvas.dataset.threshold || "0") || 0;
const maxStock = Math.max(...stocks);
const suggestedMaxStock = maxStock > 0 ? maxStock + 1 : 1;

// =============================
// グラフが既に存在する場合は破棄（再描画対策）
// =============================
if (window.priceChartInstance) {
    window.priceChartInstance.destroy();
}

// =============================
// Chart.js グラフ生成
// =============================
const ctx = canvas.getContext("2d");
window.priceChartInstance = new Chart(ctx, {
    data: {
        labels,
        datasets: [
            // 🔸価格（折れ線）
            {
                label: "価格（円）",
                data: prices,
                yAxisID: "yPrice",
                type: "line",
                borderColor: "#C35656",
                backgroundColor: "transparent",
                borderWidth: 2.5,
                fill: false,
                tension: 0.25,
                pointRadius: 4,
                pointBackgroundColor: prices.map(v =>
                    v < threshold && threshold > 0 ? "#FF4B4B" : "#C35656"
                ),
                order: 1
            },
            // 🔹在庫（棒グラフ）
            {
                label: "在庫数（個）",
                data: stocks,
                yAxisID: "yStock",
                type: "bar",
                backgroundColor: "rgba(106, 144, 181, 0.6)",
                borderColor: "#6A90B5",
                borderWidth: 1,
                order: 2
            },
            // 🟡買い時ライン（しきい値）
            ...(threshold > 0
                ? [
                    {
                        label: "買い時価格",
                        data: Array(labels.length).fill(threshold),
                        yAxisID: "yPrice",
                        borderColor: "#F7CB6E",
                        borderDash: [5, 4],
                        borderWidth: 4,
                        type: "line",
                        fill: false,
                        pointRadius: 0,
                        order: 10,
                        segment: { borderDashOffset: 0 }
                    }
                ]
                : [])
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { title: { display: true, text: "日付" } },
            yPrice: {
                type: "linear",
                position: "left",
                title: { display: true, text: "価格（円）" },
                grid: { drawOnChartArea: true }
            },
            yStock: {
                type: "linear",
                position: "right",
                title: { display: true, text: "在庫数（個）" },
                grid: { drawOnChartArea: false },
                beginAtZero: true,
                ticks: {
                    precision: 0,
                    stepSize: 1,
                    callback: value => (Number.isInteger(value) ? value : "")
                },
                suggestedMax: suggestedMaxStock
            }
        },
        plugins: {
            legend: { position: "bottom" }
        }
    }
});
});
