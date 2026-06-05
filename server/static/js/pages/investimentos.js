import { createModal } from "../components/modal.js";

function toBRL(value) {
    return Number(value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function renderSparkline(container, prices) {
    if (!prices || prices.length < 2) return;

    const W = container.clientWidth || 240;
    const H = 52;
    const PAD = 3;
    const innerH = H - PAD * 2;

    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = max - min || 1;

    const xs = prices.map((_, i) => (i / (prices.length - 1)) * W);
    const ys = prices.map(p => PAD + innerH - ((p - min) / range) * innerH);

    const d = xs.map((x, i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${ys[i].toFixed(1)}`).join(" ");

    const isUp = prices[prices.length - 1] >= prices[0];
    const stroke = isUp ? "var(--color-success)" : "var(--color-danger)";

    // Filled area under the line
    const areaClose = ` L${xs[xs.length - 1].toFixed(1)},${H} L${xs[0].toFixed(1)},${H} Z`;
    const fillColor = isUp ? "rgba(92,213,158,0.12)" : "rgba(240,115,115,0.12)";

    container.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"
        xmlns="http://www.w3.org/2000/svg" style="width:100%;height:${H}px;display:block">
        <path d="${d}${areaClose}" fill="${fillColor}" stroke="none"/>
        <path d="${d}" fill="none" stroke="${stroke}" stroke-width="1.8"
            stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
}

function renderAllSparklines() {
    document.querySelectorAll(".inv-asset-card[data-history]").forEach(card => {
        const container = card.querySelector(".inv-sparkline");
        if (!container) return;
        try {
            const prices = JSON.parse(card.dataset.history);
            renderSparkline(container, prices);
        } catch { /* ignore malformed data */ }
    });
}

function renderResumoChart(chartEl, legendEl, data) {
    const { labels, portfolios, total } = data;

    if (!labels || labels.length < 2) {
        chartEl.innerHTML = '<p class="resumo-empty">Invista em ativos para ver o historico da sua carteira.</p>';
        return;
    }

    const W = chartEl.clientWidth || 680;
    const H = 260;
    const ML = 68, MR = 20, MT = 14, MB = 34;
    const iW = W - ML - MR;
    const iH = H - MT - MB;
    const n = labels.length;

    const allVals = [...total, ...portfolios.flatMap(p => p.values)].filter(Number.isFinite);
    const rawMin = Math.min(...allVals);
    const rawMax = Math.max(...allVals);
    const pad = (rawMax - rawMin) * 0.1 || 1;
    const minV = rawMin - pad;
    const maxV = rawMax + pad;
    const span = maxV - minV;

    const gx = i => ML + (i / (n - 1)) * iW;
    const gy = v => MT + iH - ((v - minV) / span) * iH;
    const makePath = vals =>
        vals.map((v, i) => `${i === 0 ? "M" : "L"}${gx(i).toFixed(1)},${gy(v).toFixed(1)}`).join(" ");

    const fmtY = v => {
        if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
        if (v >= 1_000) return `${(v / 1000).toFixed(1)}k`;
        return v.toFixed(0);
    };

    const TICKS = 5;
    const yGrid = Array.from({ length: TICKS }, (_, i) => {
        const v = minV + (span / (TICKS - 1)) * i;
        const y = gy(v).toFixed(1);
        return `<line x1="${ML}" y1="${y}" x2="${ML + iW}" y2="${y}" stroke="rgba(255,255,255,0.055)" stroke-width="1"/>`;
    }).join("");

    const yLabels = Array.from({ length: TICKS }, (_, i) => {
        const v = minV + (span / (TICKS - 1)) * i;
        const y = gy(v).toFixed(1);
        return `<text x="${ML - 7}" y="${y}" text-anchor="end" dominant-baseline="middle" fill="rgba(200,220,240,0.4)" font-size="10" font-family="monospace">R$${fmtY(v)}</text>`;
    }).join("");

    const xStep = Math.ceil(n / 8);
    const xLabels = labels.map((lbl, i) => {
        if (i % xStep !== 0 && i !== n - 1) return "";
        return `<text x="${gx(i).toFixed(1)}" y="${H - 7}" text-anchor="middle" fill="rgba(200,220,240,0.4)" font-size="10">${lbl}</text>`;
    }).join("");

    // Visual portfolio paths — carry data-line for highlight control
    const portPaths = portfolios.map((p, i) =>
        `<path data-line="${i}" d="${makePath(p.values)}" fill="none" stroke="${p.color}" stroke-width="1.5" stroke-opacity="0.65" stroke-linecap="round" stroke-linejoin="round" style="transition:stroke-opacity .12s,stroke-width .12s"/>`
    ).join("");

    const totalD = makePath(total);
    const areaClose = ` L${gx(n - 1).toFixed(1)},${(MT + iH).toFixed(1)} L${gx(0).toFixed(1)},${(MT + iH).toFixed(1)} Z`;
    const totalLinePath = `<path data-line="total" d="${totalD}" fill="none" stroke="#7ecef4" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="transition:stroke-opacity .12s,stroke-width .12s"/>`;

    // Wide invisible hit-area paths — placed on top inside the clip group
    const hitPaths = [
        ...portfolios.map((p, i) =>
            `<path data-hit="${i}" d="${makePath(p.values)}" fill="none" stroke="white" stroke-width="20" stroke-opacity="0.01" style="cursor:pointer"/>`
        ),
        `<path data-hit="total" d="${totalD}" fill="none" stroke="white" stroke-width="20" stroke-opacity="0.01" style="cursor:pointer"/>`,
    ].join("");

    chartEl.innerHTML = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:${H}px;display:block">
        <defs>
            <linearGradient id="rg-area-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="rgba(100,180,240,0.28)"/>
                <stop offset="100%" stop-color="rgba(100,180,240,0.03)"/>
            </linearGradient>
            <clipPath id="rg-clip">
                <rect x="${ML}" y="${MT}" width="${iW}" height="${iH}"/>
            </clipPath>
        </defs>
        <g clip-path="url(#rg-clip)">
            ${yGrid}
            ${portPaths}
            <path d="${totalD}${areaClose}" fill="url(#rg-area-grad)" stroke="none"/>
            ${totalLinePath}
            ${hitPaths}
        </g>
        ${yLabels}
        ${xLabels}
        <line x1="${ML}" y1="${MT}" x2="${ML}" y2="${MT + iH}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
        <line x1="${ML}" y1="${MT + iH}" x2="${ML + iW}" y2="${MT + iH}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
    </svg>`;

    // ── Hover interactivity ───────────────────────────────────────
    chartEl.style.position = "relative";
    const tooltip = document.createElement("div");
    tooltip.className = "resumo-tooltip";
    tooltip.hidden = true;
    chartEl.appendChild(tooltip);

    const svg = chartEl.querySelector("svg");
    const allKeys = ["total", ...portfolios.map((_, i) => String(i))];
    const defOpacity = k => k === "total" ? "1" : "0.65";
    const defWidth   = k => k === "total" ? "2.4" : "1.5";
    const actWidth   = k => k === "total" ? "3.2" : "2.2";
    const getVisual  = k => svg.querySelector(`[data-line="${k}"]`);

    const highlight = (activeKey) => {
        allKeys.forEach(k => {
            const el = getVisual(k);
            if (!el) return;
            if (k === activeKey) {
                el.setAttribute("stroke-opacity", "1");
                el.setAttribute("stroke-width", actWidth(k));
            } else {
                el.setAttribute("stroke-opacity", "0.12");
                el.setAttribute("stroke-width", defWidth(k));
            }
        });
    };

    const clearHighlight = () => {
        allKeys.forEach(k => {
            const el = getVisual(k);
            if (!el) return;
            el.setAttribute("stroke-opacity", defOpacity(k));
            el.setAttribute("stroke-width", defWidth(k));
        });
        tooltip.hidden = true;
    };

    svg.querySelectorAll("[data-hit]").forEach(hitEl => {
        const key = hitEl.dataset.hit;
        const isTotal = key === "total";
        const lineInfo = isTotal
            ? { name: "Total da carteira", values: total }
            : { name: portfolios[+key].name, values: portfolios[+key].values };

        hitEl.addEventListener("mouseenter", () => highlight(key));
        hitEl.addEventListener("mouseleave", clearHighlight);
        hitEl.addEventListener("mousemove", (e) => {
            const svgRect = svg.getBoundingClientRect();
            const idx = Math.max(0, Math.min(n - 1, Math.round((e.clientX - svgRect.left - ML) / iW * (n - 1))));
            const value = lineInfo.values[idx] ?? 0;

            const wrapRect = chartEl.getBoundingClientRect();
            const tipX = Math.min(e.clientX - wrapRect.left + 14, chartEl.clientWidth - 160);
            const tipY = Math.max(e.clientY - wrapRect.top - 52, 4);

            tooltip.hidden = false;
            tooltip.innerHTML = `<strong>${lineInfo.name}</strong><span>R$ ${toBRL(value)}</span><em>${labels[idx] ?? ""}</em>`;
            tooltip.style.left = `${tipX}px`;
            tooltip.style.top = `${tipY}px`;
        });
    });

    // ── Legend ────────────────────────────────────────────────────
    legendEl.innerHTML = [
        `<span class="resumo-legend-item"><span class="resumo-legend-line resumo-legend-line--total"></span><span>Total da carteira</span></span>`,
        ...portfolios.map(p =>
            `<span class="resumo-legend-item"><span class="resumo-legend-line" style="background:${p.color}"></span><span>${p.name}</span></span>`
        ),
    ].join("");
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

    if (page.dataset.view === "resumo") {
        const rawJson = page.dataset.resumo;
        if (!rawJson) return;
        try {
            renderResumoChart(
                document.getElementById("resumo-chart"),
                document.getElementById("resumo-legend"),
                JSON.parse(rawJson),
            );
        } catch { /* ignore */ }
        return;
    }

    renderAllSparklines();

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
