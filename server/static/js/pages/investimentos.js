function toBRL(value) {
    return Number(value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function pct(value, total) {
    if (!total) return "0.0";
    return ((value / total) * 100).toFixed(1);
}

function renderDistributionView(data) {
    const donut = document.getElementById("dist-donut");
    const donutTotal = document.getElementById("donut-total");
    const legendList = document.getElementById("legend-list");
    const assetBars = document.getElementById("asset-bars");

    if (!donut || !donutTotal || !legendList || !assetBars) return;

    const { classes = [], assets = [], total = 0 } = data;

    donutTotal.textContent = `R$ ${toBRL(total)}`;

    if (classes.length) {
        let cursor = 0;
        const segments = classes.map((item) => {
            const start = cursor;
            const angle = total ? (item.value / total) * 360 : 0;
            cursor += angle;
            return `${item.color} ${start}deg ${cursor}deg`;
        });
        donut.style.background = `conic-gradient(${segments.join(",")})`;
    }

    legendList.innerHTML = "";
    classes.forEach((item) => {
        const row = document.createElement("div");
        row.className = "legend-row";
        row.innerHTML = `
            <span class="legend-dot" style="background:${item.color};"></span>
            <strong>${item.label}</strong>
            <span>${pct(item.value, total)}%</span>
            <em>R$ ${toBRL(item.value)}</em>
        `;
        legendList.appendChild(row);
    });

    assetBars.innerHTML = "";
    const maxAsset = Math.max(...assets.map((a) => a.value), 1);
    const colorMap = Object.fromEntries(classes.map((c) => [c.label, c.color]));
    assets.forEach((item) => {
        const color = colorMap[item.className] || "#6fd0ce";
        const row = document.createElement("div");
        row.className = "bar-row";
        row.innerHTML = `
            <label>${item.name}<span>${pct(item.value, total)}%</span></label>
            <div class="bar-track"><div class="bar-fill" style="width:${(item.value / maxAsset) * 100}%; background:${color};"></div></div>
        `;
        assetBars.appendChild(row);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const page = document.querySelector(".investment-page");
    if (!page) return;

    const view = page.dataset.view;
    if (view !== "distribuicao") return;

    const rawJson = page.dataset.portfolio;
    if (!rawJson) return;

    let data;
    try {
        data = JSON.parse(rawJson);
    } catch {
        return;
    }

    renderDistributionView(data);
});
