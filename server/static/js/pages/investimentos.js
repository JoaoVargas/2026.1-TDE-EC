const classData = [
    { label: "Renda fixa", value: 9400, color: "#2eb8b8" },
    { label: "Renda variavel", value: 5100, color: "#22888c" },
    { label: "Criptomoedas", value: 2500, color: "#c8922a" },
];

const assetData = [
    { name: "Tesouro Prefixado", className: "Renda fixa", value: 5200 },
    { name: "Carro Novo", className: "Renda fixa", value: 4200 },
    { name: "XMLT", className: "Renda variavel", value: 2400 },
    { name: "XCORTI", className: "Renda variavel", value: 2700 },
    { name: "Bitcoin", className: "Criptomoedas", value: 1800 },
    { name: "Memecoin", className: "Criptomoedas", value: 700 },
];

const returnData = [
    { label: "Renda fixa", pct: 6.4, color: "#2eb8b8" },
    { label: "Renda variavel", pct: 11.7, color: "#22888c" },
    { label: "Criptomoedas", pct: 16.2, color: "#c8922a" },
];

function toBRL(value) {
    return value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function sumValues(items) {
    return items.reduce((acc, item) => acc + item.value, 0);
}

function pct(value, total) {
    if (!total) {
        return "0.0";
    }
    return ((value / total) * 100).toFixed(1);
}

function findStatValueNodeByLabel(labelText) {
    const cards = document.querySelectorAll(".investment-stat");
    for (const card of cards) {
        const label = card.querySelector(".investment-stat-label");
        if (label && label.textContent.trim().toLowerCase() === labelText.toLowerCase()) {
            const value = card.querySelector(".investment-stat-value");
            const sub = card.querySelector(".investment-stat-sub");
            return { value, sub };
        }
    }
    return { value: null, sub: null };
}

function hydrateSharedStats() {
    const total = sumValues(classData);
    const totalVal = document.getElementById("total-val");
    const totalChange = document.getElementById("total-change");

    if (totalVal) {
        totalVal.textContent = toBRL(total);
    }
    if (totalChange) {
        totalChange.textContent = total > 0 ? `+${((total / 17000) * 100).toFixed(1)}% carteira ativa` : "- Sem variacao";
    }

    const fixo = classData.find((item) => item.label === "Renda fixa")?.value || 0;
    const variavel = classData.find((item) => item.label === "Renda variavel")?.value || 0;

    const fixoById = document.getElementById("fixo-val");
    const fixoPctById = document.getElementById("fixo-pct");
    const variavelById = document.getElementById("variavel-val");
    const variavelPctById = document.getElementById("variavel-pct");

    if (fixoById) {
        fixoById.textContent = toBRL(fixo);
    }
    if (fixoPctById) {
        fixoPctById.textContent = `${pct(fixo, total)}% da carteira`;
    }
    if (variavelById) {
        variavelById.textContent = toBRL(variavel);
    }
    if (variavelPctById) {
        variavelPctById.textContent = `${pct(variavel, total)}% da carteira`;
    }

    if (!fixoById) {
        const fixoStat = findStatValueNodeByLabel("Renda fixa");
        if (fixoStat.value) {
            fixoStat.value.innerHTML = `<span class="currency">R$</span>${toBRL(fixo)}`;
        }
        if (fixoStat.sub) {
            fixoStat.sub.textContent = `${pct(fixo, total)}% da carteira`;
        }
    }

    if (!variavelById) {
        const variavelStat = findStatValueNodeByLabel("Renda variavel");
        if (variavelStat.value) {
            variavelStat.value.innerHTML = `<span class="currency">R$</span>${toBRL(variavel)}`;
        }
        if (variavelStat.sub) {
            variavelStat.sub.textContent = `${pct(variavel, total)}% da carteira`;
        }
    }
}

function renderDistributionView() {
    const donut = document.getElementById("dist-donut");
    const donutTotal = document.getElementById("donut-total");
    const legendList = document.getElementById("legend-list");
    const assetBars = document.getElementById("asset-bars");
    const returnBars = document.getElementById("return-bars");

    if (!donut || !donutTotal || !legendList || !assetBars || !returnBars) {
        return;
    }

    const total = sumValues(classData);
    donutTotal.textContent = `R$ ${toBRL(total)}`;

    let cursor = 0;
    const segments = classData.map((item) => {
        const start = cursor;
        const angle = total ? (item.value / total) * 360 : 0;
        cursor += angle;
        return `${item.color} ${start}deg ${cursor}deg`;
    });
    donut.style.background = `conic-gradient(${segments.join(",")})`;

    legendList.innerHTML = "";
    classData.forEach((item) => {
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
    const maxAsset = Math.max(...assetData.map((item) => item.value), 1);
    assetData.forEach((item) => {
        const classColor = classData.find((entry) => entry.label === item.className)?.color || "#6fd0ce";
        const row = document.createElement("div");
        row.className = "bar-row";
        row.innerHTML = `
            <label>${item.name}<span>${pct(item.value, total)}%</span></label>
            <div class="bar-track"><div class="bar-fill" style="width:${(item.value / maxAsset) * 100}%; background:${classColor};"></div></div>
        `;
        assetBars.appendChild(row);
    });

    returnBars.innerHTML = "";
    const maxReturn = Math.max(...returnData.map((item) => item.pct), 1);
    returnData.forEach((item) => {
        const row = document.createElement("div");
        row.className = "bar-row";
        row.innerHTML = `
            <label>${item.label}<span>${item.pct.toFixed(2)}%</span></label>
            <div class="bar-track"><div class="bar-fill" style="width:${(item.pct / maxReturn) * 100}%; background:${item.color};"></div></div>
        `;
        returnBars.appendChild(row);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const view = document.querySelector(".investment-page")?.dataset.view;
    if (!view) {
        return;
    }

    hydrateSharedStats();

    if (view === "distribuicao") {
        renderDistributionView();
    }
});
