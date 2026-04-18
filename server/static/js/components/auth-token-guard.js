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

export async function requireAuthenticatedUser() {
    const token = localStorage.getItem("token");
    if (!token) {
        window.location.href = "/login";
        return null;
    }

    try {
        const response = await fetch("/api/me", {
            headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
            throw new Error("invalid-token");
        }

        return await response.json();
    } catch {
        localStorage.removeItem("token");
        localStorage.removeItem("usuario");
        window.location.href = "/login";
        return null;
    }
}

export function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("usuario");
    window.location.href = "/login";
}
