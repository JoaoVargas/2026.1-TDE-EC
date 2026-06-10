class BBFilterSelect extends HTMLElement {
    #trigger = null;
    #dropdown = null;
    #defaultLabel = "";
    #outsideClick = null;

    connectedCallback() {
        if (this.dataset.rendered === "true") return;

        this.#defaultLabel = this.getAttribute("label") || "Selecionar";

        const options = Array.from(this.querySelectorAll("option")).map(opt => ({
            value: opt.value,
            label: opt.textContent.trim(),
        }));

        this.#trigger = document.createElement("button");
        this.#trigger.type = "button";
        this.#trigger.className = "statement-filter";
        this.#setLabel(this.#defaultLabel);

        this.#dropdown = document.createElement("div");
        this.#dropdown.className = "filter-select-dropdown";
        this.#dropdown.hidden = true;

        options.forEach(({ value, label }) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "filter-select-option";
            btn.textContent = label;
            btn.addEventListener("click", () => {
                if (value) {
                    this.#setLabel(label);
                    this.#trigger.classList.add("is-active");
                } else {
                    this.#reset();
                }
                this.#dropdown.hidden = true;
                this.#emit(value || null);
            });
            this.#dropdown.appendChild(btn);
        });

        this.#trigger.addEventListener("click", e => {
            e.stopPropagation();
            this.#dropdown.hidden = !this.#dropdown.hidden;
        });

        this.#outsideClick = e => {
            if (!this.contains(e.target)) this.#dropdown.hidden = true;
        };
        document.addEventListener("click", this.#outsideClick);

        this.replaceChildren(this.#trigger, this.#dropdown);
        this.dataset.rendered = "true";
    }

    disconnectedCallback() {
        document.removeEventListener("click", this.#outsideClick);
    }

    clear() {
        this.#reset();
    }

    #reset() {
        this.#setLabel(this.#defaultLabel);
        this.#trigger?.classList.remove("is-active");
        if (this.#dropdown) this.#dropdown.hidden = true;
    }

    #setLabel(text) {
        this.#trigger.innerHTML = `${text} <span class="date-range-caret">▾</span>`;
    }

    #emit(value) {
        this.dispatchEvent(new CustomEvent("bb:filterselect", {
            bubbles: true,
            detail: { value, trigger: this.#trigger },
        }));
    }
}

if (!customElements.get("bb-filter-select")) {
    customElements.define("bb-filter-select", BBFilterSelect);
}
