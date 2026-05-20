class BBDateRangePicker extends HTMLElement {
    #trigger = null;
    #picker = null;
    #inputFrom = null;
    #inputTo = null;
    #outsideClick = null;

    connectedCallback() {
        if (this.dataset.rendered === "true") return;

        const label = this.getAttribute("label") || "Período";

        this.#trigger = document.createElement("button");
        this.#trigger.type = "button";
        this.#trigger.className = "statement-filter";
        this.#setTriggerLabel(null, null);

        this.#picker = document.createElement("div");
        this.#picker.className = "date-range-picker";
        this.#picker.hidden = true;

        const fromGroup = this.#buildGroup("De");
        const toGroup = this.#buildGroup("Até");
        this.#inputFrom = fromGroup.input;
        this.#inputTo = toGroup.input;

        const fields = document.createElement("div");
        fields.className = "date-range-fields";
        fields.append(fromGroup.el, toGroup.el);

        const clearBtn = document.createElement("button");
        clearBtn.type = "button";
        clearBtn.className = "date-range-clear";
        clearBtn.textContent = "Limpar";

        const applyBtn = document.createElement("button");
        applyBtn.type = "button";
        applyBtn.className = "ui-btn ui-btn-primary date-range-apply";
        applyBtn.textContent = "Aplicar";

        const actions = document.createElement("div");
        actions.className = "date-range-actions";
        actions.append(clearBtn, applyBtn);

        this.#picker.append(fields, actions);
        this.append(this.#trigger, this.#picker);
        this.dataset.rendered = "true";

        this.#trigger.addEventListener("click", (e) => {
            e.stopPropagation();
            this.#picker.hidden = !this.#picker.hidden;
        });

        applyBtn.addEventListener("click", () => {
            const from = this.#inputFrom.value || null;
            const to = this.#inputTo.value || null;
            this.#picker.hidden = true;
            this.#setTriggerLabel(from, to);
            this.#emit(from, to);
        });

        clearBtn.addEventListener("click", () => {
            this.#inputFrom.value = "";
            this.#inputTo.value = "";
            this.#picker.hidden = true;
            this.#setTriggerLabel(null, null);
            this.#emit(null, null);
        });

        this.#outsideClick = (e) => {
            if (!this.contains(e.target)) this.#picker.hidden = true;
        };
        document.addEventListener("click", this.#outsideClick);
    }

    disconnectedCallback() {
        document.removeEventListener("click", this.#outsideClick);
    }

    // ISO "YYYY-MM-DD" → "DD/MM"
    #fmtDate(iso) {
        const [, month, day] = iso.split("-");
        return `${day}/${month}`;
    }

    #rangeLabel(from, to) {
        if (from && to) return `${this.#fmtDate(from)} – ${this.#fmtDate(to)}`;
        if (from) return `de ${this.#fmtDate(from)}`;
        if (to) return `até ${this.#fmtDate(to)}`;
        return this.getAttribute("label") || "Período";
    }

    #setTriggerLabel(from, to) {
        const text = this.#rangeLabel(from, to);
        this.#trigger.innerHTML = `${text} <span class="date-range-caret">▾</span>`;
    }

    #emit(from, to) {
        this.dispatchEvent(new CustomEvent("bb:daterange", {
            bubbles: true,
            detail: { from, to, trigger: this.#trigger },
        }));
    }

    #buildGroup(labelText) {
        const el = document.createElement("div");
        el.className = "date-range-group";

        const label = document.createElement("p");
        label.className = "date-range-label";
        label.textContent = labelText;

        const input = document.createElement("input");
        input.type = "date";
        input.className = "ui-input date-range-input";

        el.append(label, input);
        return { el, input };
    }
}

if (!customElements.get("bb-date-range-picker")) {
    customElements.define("bb-date-range-picker", BBDateRangePicker);
}
