function createTextElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) {
        element.className = className;
    }
    element.textContent = text;
    return element;
}

function appendCurrencyValue(container, value) {
    const currency = createTextElement("span", "currency", "R$");
    container.appendChild(currency);
    container.append(value || "0,00");
}

class BBInsightCard extends HTMLElement {
    connectedCallback() {
        if (this.dataset.rendered === "true") {
            return;
        }

        const article = createTextElement("article", "dashboard-card ui-card", "");
        const title = createTextElement("h3", "", this.getAttribute("title") || "");
        const text = createTextElement("p", "", this.getAttribute("text") || "");

        article.append(title, text);

        const buttonLabel = this.getAttribute("button-label") || "";
        if (buttonLabel) {
            const variant = this.getAttribute("button-variant") || "ui-btn-primary";
            const button = createTextElement("button", `ui-btn ${variant}`, buttonLabel);
            button.type = "button";
            article.appendChild(button);
        }

        this.replaceChildren(article);
        this.dataset.rendered = "true";
    }
}

class BBInvestmentStat extends HTMLElement {
    connectedCallback() {
        if (this.dataset.rendered === "true") {
            return;
        }

        const article = createTextElement("article", "investment-stat ui-card", "");
        if (this.hasAttribute("main")) {
            article.classList.add("main-stat");
        }

        const label = createTextElement("p", "investment-stat-label", this.getAttribute("label") || "-");
        const value = createTextElement("p", "investment-stat-value", "");
        appendCurrencyValue(value, this.getAttribute("value"));

        const subtitle = createTextElement(
            "p",
            "investment-stat-sub",
            this.getAttribute("subtitle") || "-"
        );

        article.append(label, value, subtitle);
        this.replaceChildren(article);
        this.dataset.rendered = "true";
    }
}

class BBAssetCard extends HTMLElement {
    connectedCallback() {
        if (this.dataset.rendered === "true") {
            return;
        }

        const tone = this.getAttribute("tone") || "teal";
        const article = createTextElement("article", `asset-card ui-card tone-${tone}`, "");

        const kind = createTextElement("p", "asset-kind", this.getAttribute("kind") || "-");
        const title = createTextElement("h3", "asset-title", this.getAttribute("title") || "-");
        const subtitle = createTextElement("p", "asset-subtitle", this.getAttribute("subtitle") || "-");
        const tag = createTextElement("p", "asset-tag", this.getAttribute("tag") || "-");

        article.append(kind, title, subtitle, tag);
        this.replaceChildren(article);
        this.dataset.rendered = "true";
    }
}

class BBStatementItem extends HTMLElement {
    connectedCallback() {
        if (this.dataset.rendered === "true") {
            return;
        }

        const type = (this.getAttribute("kind") || "out").toLowerCase();
        const month = this.getAttribute("month") || "";

        const article = createTextElement("article", "statement-item ui-card", "");
        article.dataset.type = type;
        article.dataset.month = month;

        const icon = createTextElement("div", `statement-icon ${type}`, type === "in" ? "+" : "-");

        const meta = createTextElement("div", "statement-meta", "");
        const name = createTextElement("p", "statement-name", this.getAttribute("title") || "-");
        const date = createTextElement("p", "statement-date", this.getAttribute("date") || "-");
        meta.append(name, date);

        const amount = createTextElement(
            "p",
            `statement-amount ${type}`,
            this.getAttribute("amount") || "R$ 0,00"
        );

        article.append(icon, meta, amount);
        this.replaceChildren(article);
        this.dataset.rendered = "true";
    }
}

if (!customElements.get("bb-insight-card")) {
    customElements.define("bb-insight-card", BBInsightCard);
}

if (!customElements.get("bb-investment-stat")) {
    customElements.define("bb-investment-stat", BBInvestmentStat);
}

if (!customElements.get("bb-asset-card")) {
    customElements.define("bb-asset-card", BBAssetCard);
}

if (!customElements.get("bb-statement-item")) {
    customElements.define("bb-statement-item", BBStatementItem);
}
