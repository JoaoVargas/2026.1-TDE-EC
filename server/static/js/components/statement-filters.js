function parseTxDateStr(dateStr) {
    const [day, month, year] = dateStr.split(" · ")[0].split("/");
    return `${year}-${month}-${day}`;
}

/**
 * @param {object}    opts
 * @param {string}    opts.navSelector   - selector for the filter <nav>
 * @param {string}    opts.listSelector  - selector for the items container
 * @param {string}    opts.countPillId   - id of the visible-count pill
 * @param {function}  [opts.extraTest]   - (item: Element) => bool, AND-ed with base filter
 * @returns {{ applyAll: () => void }}
 */
export function initStatementFilters({ navSelector, listSelector, countPillId, extraTest }) {
    const nav  = document.querySelector(navSelector);
    const list = document.querySelector(listSelector);
    const pill = document.getElementById(countPillId);
    if (!nav || !list) return { applyAll: () => {} };

    let activeFilter = "all";
    let dateFrom = null;
    let dateTo   = null;

    function updateCount() {
        if (!pill) return;
        const visible = Array.from(list.querySelectorAll("bb-statement-item"))
            .filter(el => el.style.display !== "none").length;
        pill.textContent = visible;
    }

    function applyAll() {
        const nowMonth = String(new Date().getMonth() + 1);
        list.querySelectorAll(".statement-item").forEach(item => {
            let visible = true;

            if (activeFilter === "in")              visible = item.dataset.type === "in";
            else if (activeFilter === "out")        visible = item.dataset.type === "out";
            else if (activeFilter === "month")      visible = item.dataset.month === nowMonth;
            else if (activeFilter.startsWith("type:")) visible = item.dataset.typeLabel === activeFilter.slice(5);
            else if (activeFilter === "period") {
                const d = item.dataset.date;
                if (d && (dateFrom || dateTo)) {
                    const txDate = parseTxDateStr(d);
                    if (dateFrom) visible = visible && txDate >= dateFrom;
                    if (dateTo)   visible = visible && txDate <= dateTo;
                }
            }

            if (visible && extraTest) visible = extraTest(item);

            const host = item.closest("bb-statement-item") || item;
            host.style.display = visible ? "" : "none";
        });
        updateCount();
    }

    function setActive(btn) {
        nav.querySelectorAll(".statement-filter").forEach(n => n.classList.remove("is-active"));
        nav.querySelectorAll("bb-filter-select").forEach(sel => {
            if (!sel.contains(btn)) sel.clear();
        });
        btn?.classList.add("is-active");
    }

    Array.from(nav.querySelectorAll(".statement-filter"))
        .filter(btn => !btn.closest("bb-date-range-picker") && !btn.closest("bb-filter-select"))
        .forEach(btn => {
            btn.addEventListener("click", () => {
                activeFilter = btn.dataset.filter || "all";
                dateFrom = null;
                dateTo = null;
                setActive(btn);
                applyAll();
            });
        });

    nav.addEventListener("bb:filterselect", e => {
        const { value, trigger } = e.detail;
        dateFrom = null;
        dateTo = null;
        if (value) {
            activeFilter = value;
            setActive(trigger);
        } else {
            activeFilter = "all";
            setActive(nav.querySelector('[data-filter="all"]'));
        }
        applyAll();
    });

    nav.querySelector("bb-date-range-picker")?.addEventListener("bb:daterange", e => {
        const { from, to, trigger } = e.detail;
        if (!from && !to) {
            activeFilter = "all";
            dateFrom = null;
            dateTo = null;
            setActive(nav.querySelector('[data-filter="all"]'));
        } else {
            activeFilter = "period";
            dateFrom = from;
            dateTo = to;
            setActive(trigger);
        }
        applyAll();
    });

    updateCount();
    return { applyAll };
}
