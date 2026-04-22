import { requireManagerUser } from "/static/js/components/auth-token-guard.js";

document.addEventListener("DOMContentLoaded", async () => {
    await requireManagerUser();
});
