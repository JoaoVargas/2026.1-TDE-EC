import { createModal } from "../components/modal.js";

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
        const dot = document.createElement("span");
        dot.className = "legend-dot";
        dot.style.backgroundColor = item.color;

        const label = document.createElement("strong");
        label.textContent = item.label;

        const percentage = document.createElement("span");
        percentage.textContent = `${pct(item.value, total)}%`;

        const amount = document.createElement("em");
        amount.textContent = `R$ ${toBRL(item.value)}`;

        const row = document.createElement("div");
        row.className = "legend-row";
        row.append(dot, label, percentage, amount);
        legendList.appendChild(row);
    });

    assetBars.innerHTML = "";
    const maxAsset = Math.max(...assets.map((a) => a.value), 1);
    const colorMap = Object.fromEntries(classes.map((c) => [c.label, c.color]));
    assets.forEach((item) => {
        const color = colorMap[item.className] || "#6fd0ce";

        const pctSpan = document.createElement("span");
        pctSpan.textContent = `${pct(item.value, total)}%`;
        const labelEl = document.createElement("label");
        labelEl.append(item.name, pctSpan);

        const fill = document.createElement("div");
        fill.className = "bar-fill";
        fill.style.width = `${(item.value / maxAsset) * 100}%`;
        fill.style.backgroundColor = color;
        const track = document.createElement("div");
        track.className = "bar-track";
        track.appendChild(fill);

        const row = document.createElement("div");
        row.className = "bar-row";
        row.append(labelEl, track);
        assetBars.appendChild(row);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const page = document.querySelector(".investment-page");
    if (!page) return;

    if (page.dataset.view === "distribuicao") {
        const rawJson = page.dataset.portfolio;
        if (!rawJson) return;
        try { renderDistributionView(JSON.parse(rawJson)); } catch { /* ignore */ }
        return;
    }

    // ── Modal: Depositar ──────────────────────────────────────────
    const depositarModal = createModal("inv-depositar-backdrop");
    const depForm        = document.getElementById("inv-dep-form");
    const depInput       = document.getElementById("inv-dep-value");
    const depAmountCents = document.getElementById("inv-dep-amount-cents");
    const depShares      = document.getElementById("inv-dep-shares");

    let currentDepositPrice = 0;

    depInput?.addEventListener("input", () => {
        const val = parseFloat(depInput.value) || 0;
        depAmountCents.value = Math.round(val * 100);
        depShares.textContent = currentDepositPrice > 0
            ? (val / currentDepositPrice).toFixed(4)
            : "0";
    });

    document.querySelectorAll(".inv-depositar-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            currentDepositPrice = parseInt(btn.dataset.priceCents) / 100;
            depForm.action = `/investimentos/${btn.dataset.portfolioId}/depositar`;
            document.getElementById("inv-dep-name").textContent    = btn.dataset.name;
            document.getElementById("inv-dep-price").textContent   = `R$ ${toBRL(currentDepositPrice)}`;
            document.getElementById("inv-dep-balance").textContent = `R$ ${toBRL(parseInt(btn.dataset.balanceCents) / 100)}`;
            depInput.value       = "";
            depAmountCents.value = "0";
            depShares.textContent = "0";
            depositarModal.open({ trigger: btn, onOpen() { setTimeout(() => depInput.focus(), 0); } });
        });
    });

    // ── Modal: Retirar ────────────────────────────────────────────
    const retirarModal   = createModal("inv-retirar-backdrop");
    const retForm        = document.getElementById("inv-ret-form");
    const retInput       = document.getElementById("inv-ret-shares");
    const retValue       = document.getElementById("inv-ret-value");

    let currentRetirePrice = 0;

    retInput?.addEventListener("input", () => {
        const shares = parseFloat(retInput.value) || 0;
        retValue.textContent = `R$ ${toBRL(shares * currentRetirePrice)}`;
    });

    document.querySelectorAll(".inv-retirar-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            currentRetirePrice = parseFloat(btn.dataset.price);
            retForm.action = `/investimentos/${btn.dataset.portfolioId}/retirar`;
            document.getElementById("inv-ret-name").textContent   = btn.dataset.name;
            document.getElementById("inv-ret-amount").textContent = btn.dataset.amount;
            document.getElementById("inv-ret-price").textContent  = `R$ ${toBRL(currentRetirePrice)}`;
            retInput.value        = "";
            retValue.textContent  = "R$ 0,00";
            retirarModal.open({ trigger: btn, onOpen() { setTimeout(() => retInput.focus(), 0); } });
        });
    });
});
