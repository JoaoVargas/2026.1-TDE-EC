function applyFilter(filter) {
    const items = document.querySelectorAll(".statement-item");
    const nowMonth = String(new Date().getMonth() + 1);

    items.forEach((item) => {
        const type = item.dataset.type;
        const month = item.dataset.month;

        let visible = true;
        if (filter === "in") {
            visible = type === "in";
        } else if (filter === "out") {
            visible = type === "out";
        } else if (filter === "month") {
            visible = month === nowMonth;
        }

        item.style.display = visible ? "" : "none";
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const filters = document.querySelectorAll(".statement-filter");
    filters.forEach((button) => {
        button.addEventListener("click", () => {
            filters.forEach((node) => node.classList.remove("is-active"));
            button.classList.add("is-active");
            applyFilter(button.dataset.filter || "all");
        });
    });
});
