import { initStatementFilters } from "../components/statement-filters.js";

document.addEventListener("DOMContentLoaded", () => {
    let searchText = "";
    const { applyAll } = initStatementFilters({
        navSelector:  "#statement-filters",
        listSelector: "#statement-list",
        countPillId:  "statement-count",
        extraTest: (item) => !searchText || (item.dataset.title || "").includes(searchText),
    });

    const searchInput = document.getElementById("extrato-search");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            searchText = searchInput.value.trim().toLowerCase();
            applyAll();
        });
    }
});
