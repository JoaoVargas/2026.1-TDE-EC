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

// ── Modal: Depositar ─────────────────────────────────
function openDepositarModal(portfolioId, name, priceCents, balanceCents) {
    const backdrop = document.getElementById("inv-depositar-backdrop");
    const form = document.getElementById("inv-dep-form");
    if (!backdrop || !form) return;

    form.action = `/investimentos/${portfolioId}/depositar`;
    document.getElementById("inv-dep-name").textContent = name;
    document.getElementById("inv-dep-price").textContent = `R$ ${toBRL(priceCents / 100)}`;
    document.getElementById("inv-dep-balance").textContent = `R$ ${toBRL(balanceCents / 100)}`;
    document.getElementById("inv-dep-value").value = "";
    document.getElementById("inv-dep-amount-cents").value = "0";
    document.getElementById("inv-dep-shares").textContent = "0";
    backdrop.hidden = false;

    const priceVal = priceCents / 100;
    const input = document.getElementById("inv-dep-value");
    input.addEventListener("input", () => {
        const val = parseFloat(input.value) || 0;
        const cents = Math.round(val * 100);
        document.getElementById("inv-dep-amount-cents").value = cents;
        const shares = priceVal > 0 ? val / priceVal : 0;
        document.getElementById("inv-dep-shares").textContent = shares.toFixed(4);
    });
    setTimeout(() => input.focus(), 0);
}

function closeDepositarModal() {
    const backdrop = document.getElementById("inv-depositar-backdrop");
    if (backdrop) backdrop.hidden = true;
}

// ── Modal: Retirar ───────────────────────────────────
function openRetirarModal(portfolioId, name, amount, price) {
    const backdrop = document.getElementById("inv-retirar-backdrop");
    const form = document.getElementById("inv-ret-form");
    if (!backdrop || !form) return;

    form.action = `/investimentos/${portfolioId}/retirar`;
    document.getElementById("inv-ret-name").textContent = name;
    document.getElementById("inv-ret-amount").textContent = `${amount}`;
    document.getElementById("inv-ret-price").textContent = `R$ ${toBRL(price)}`;
    document.getElementById("inv-ret-shares").value = "";
    document.getElementById("inv-ret-value").textContent = "R$ 0,00";
    backdrop.hidden = false;

    const priceVal = parseFloat(price);
    const sharesInput = document.getElementById("inv-ret-shares");
    sharesInput.addEventListener("input", () => {
        const shares = parseFloat(sharesInput.value) || 0;
        document.getElementById("inv-ret-value").textContent = `R$ ${toBRL(shares * priceVal)}`;
    });
    setTimeout(() => sharesInput.focus(), 0);
}

function closeRetirarModal() {
    const backdrop = document.getElementById("inv-retirar-backdrop");
    if (backdrop) backdrop.hidden = true;
}

document.addEventListener("DOMContentLoaded", () => {
    const page = document.querySelector(".investment-page");
    if (!page) return;

    const view = page.dataset.view;
    if (view === "distribuicao") {
        const rawJson = page.dataset.portfolio;
        if (!rawJson) return;
        let data;
        try { data = JSON.parse(rawJson); } catch { return; }
        renderDistributionView(data);
        return;
    }

    // Botões depositar
    document.querySelectorAll(".inv-depositar-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            openDepositarModal(
                btn.dataset.portfolioId,
                btn.dataset.name,
                parseInt(btn.dataset.priceCents),
                parseInt(btn.dataset.balanceCents),
            );
        });
    });

    // Botões retirar
    document.querySelectorAll(".inv-retirar-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            openRetirarModal(
                btn.dataset.portfolioId,
                btn.dataset.name,
                btn.dataset.amount,
                btn.dataset.price,
            );
        });
    });

    // Fechar modais
    ["inv-dep-close", "inv-dep-cancel"].forEach((id) => {
        document.getElementById(id)?.addEventListener("click", closeDepositarModal);
    });
    ["inv-ret-close", "inv-ret-cancel"].forEach((id) => {
        document.getElementById(id)?.addEventListener("click", closeRetirarModal);
    });

    document.getElementById("inv-depositar-backdrop")?.addEventListener("click", (e) => {
        if (e.target === e.currentTarget) closeDepositarModal();
    });
    document.getElementById("inv-retirar-backdrop")?.addEventListener("click", (e) => {
        if (e.target === e.currentTarget) closeRetirarModal();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key !== "Escape") return;
        closeDepositarModal();
        closeRetirarModal();
    });
});
