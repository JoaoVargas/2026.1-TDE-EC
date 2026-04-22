class HealthLiveStatus extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: "open" });
        this.endpoint = this.getAttribute("endpoint") || "/api/health";
        this.handleRefreshClick = this.refresh.bind(this);
        this.render();
    }

    connectedCallback() {
        const button = this.shadowRoot?.querySelector("button");
        button?.addEventListener("click", this.handleRefreshClick);
        this.refresh();
    }

    disconnectedCallback() {
        const button = this.shadowRoot?.querySelector("button");
        button?.removeEventListener("click", this.handleRefreshClick);
    }

    async refresh() {
        const statusElement = this.shadowRoot?.querySelector("[data-status]");
        const timeElement = this.shadowRoot?.querySelector("[data-time]");

        if (!statusElement || !timeElement) {
            return;
        }

        statusElement.textContent = "checking...";
        statusElement.className = "value pending";

        try {
            const response = await fetch(this.endpoint, {
                headers: {
                    Accept: "application/json",
                },
            });
            const payload = await response.json();
            const healthy = response.ok && payload.status === "ok";

            statusElement.textContent = healthy ? "ok" : "error";
            statusElement.className = healthy ? "value ok" : "value error";
        } catch {
            statusElement.textContent = "error";
            statusElement.className = "value error";
        }

        timeElement.textContent = new Date().toLocaleTimeString("pt-BR");
    }

    render() {
        if (!this.shadowRoot) {
            return;
        }

        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    border-radius: 10px;
                    background: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    padding: 0.9rem 1rem;
                }

                .row {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 0.75rem;
                    flex-wrap: wrap;
                }

                .meta {
                    display: grid;
                    gap: 0.35rem;
                    color: #c9d0e5;
                    font-size: 0.9rem;
                }

                .label {
                    color: #ffffff;
                    font-weight: 600;
                    letter-spacing: 0.02em;
                }

                .value {
                    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
                    text-transform: uppercase;
                    letter-spacing: 0.06em;
                }

                .value.ok {
                    color: #4ade80;
                }

                .value.error {
                    color: #f97373;
                }

                .value.pending {
                    color: #f8d66d;
                }

                button {
                    border: none;
                    border-radius: 8px;
                    padding: 0.52rem 0.85rem;
                    cursor: pointer;
                    color: #0b132b;
                    background: #5bc0be;
                    font-weight: 600;
                }

                button:hover {
                    filter: brightness(0.95);
                }
            </style>

            <div class="row">
                <div class="meta">
                    <span class="label">Live API status</span>
                    <span class="value pending" data-status>checking...</span>
                    <span data-time>--:--:--</span>
                </div>
                <button type="button">Refresh</button>
            </div>
        `;
    }
}

if (!customElements.get("health-live-status")) {
    customElements.define("health-live-status", HealthLiveStatus);
}
