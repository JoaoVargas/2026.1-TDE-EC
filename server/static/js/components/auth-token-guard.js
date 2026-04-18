export async function redirectIfAuthenticated() {
    const token = localStorage.getItem("token");
    if (!token) {
        return;
    }

    try {
        const response = await fetch("/api/me", {
            headers: { Authorization: `Bearer ${token}` },
        });

        if (response.ok) {
            window.location.href = "/home";
            return;
        }
    } catch {
        // noop: token cleanup below
    }

    localStorage.removeItem("token");
    localStorage.removeItem("usuario");
}
