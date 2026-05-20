// date string format from server: "DD/MM/YYYY · HH:MM" → "YYYY-MM-DD"
function parseTxDateStr(dateStr) {
    const [day, month, year] = dateStr.split(" · ")[0].split("/");
    return `${year}-${month}-${day}`;
}

function updateCount() {
    const pill = document.getElementById("statement-count");
    if (!pill) return;
    const visible = Array.from(document.querySelectorAll("bb-statement-item")).filter(
        (el) => el.style.display !== "none"
    ).length;
    pill.textContent = visible;
}

function applyFilter(filter, dateFrom, dateTo) {
    const items = document.querySelectorAll(".statement-item");
    const nowMonth = String(new Date().getMonth() + 1);

    items.forEach((item) => {
        const type = item.dataset.type;
        const month = item.dataset.month;
        const dateStr = item.dataset.date;

        let visible = true;
        if (filter === "in") {
            visible = type === "in";
        } else if (filter === "out") {
            visible = type === "out";
        } else if (filter === "month") {
            visible = month === nowMonth;
        } else if (filter === "period") {
            if (dateStr && (dateFrom || dateTo)) {
                const txDate = parseTxDateStr(dateStr);
                if (dateFrom) visible = visible && txDate >= dateFrom;
                if (dateTo) visible = visible && txDate <= dateTo;
            }
        }

        const host = item.closest("bb-statement-item") || item;
        host.style.display = visible ? "" : "none";
    });
    updateCount();
}

function setActiveFilter(activeBtn) {
    document.querySelectorAll(".statement-filter").forEach((n) => n.classList.remove("is-active"));
    activeBtn?.classList.add("is-active");
}

document.addEventListener("DOMContentLoaded", () => {
    updateCount();
    const regularFilters = Array.from(document.querySelectorAll(".statement-filter")).filter(
        (btn) => !btn.closest("bb-date-range-picker")
    );

    regularFilters.forEach((button) => {
        button.addEventListener("click", () => {
            setActiveFilter(button);
            applyFilter(button.dataset.filter || "all", null, null);
        });
    });

    document.querySelector("bb-date-range-picker")?.addEventListener("bb:daterange", (e) => {
        const { from, to, trigger } = e.detail;
        if (!from && !to) {
            const allBtn = document.querySelector('[data-filter="all"]');
            setActiveFilter(allBtn);
            applyFilter("all", null, null);
        } else {
            setActiveFilter(trigger);
            applyFilter("period", from, to);
        }
    });
});
