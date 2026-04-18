const TOKEN_STORAGE_KEY = "token";
const USER_STORAGE_KEY = "usuario";
const AUTH_ME_ENDPOINT = "/api/me";

function clearAuthStorage() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
}

function saveStoredUser(user) {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

function readStoredUser() {
    const rawUser = localStorage.getItem(USER_STORAGE_KEY);
    if (!rawUser) {
        return null;
    }

    try {
        return JSON.parse(rawUser);
    } catch {
        localStorage.removeItem(USER_STORAGE_KEY);
        return null;
    }
}

function isUnauthorizedStatus(statusCode) {
    return statusCode === 401 || statusCode === 403;
}

async function requestCurrentUser(token) {
    try {
        const response = await fetch(AUTH_ME_ENDPOINT, {
            headers: { Authorization: `Bearer ${token}` },
        });

        if (isUnauthorizedStatus(response.status)) {
            return { status: "unauthorized", user: null };
        }

        if (!response.ok) {
            return { status: "error", user: null };
        }

        const user = await response.json();
        saveStoredUser(user);
        return { status: "ok", user };
    } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
            return { status: "aborted", user: null };
        }
        return { status: "error", user: null };
    }
}

export async function redirectIfAuthenticated() {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
        return;
    }

    const result = await requestCurrentUser(token);

    if (result.status === "ok") {
        window.location.href = "/home";
        return;
    }

    if (result.status === "unauthorized") {
        clearAuthStorage();
    }
}

export async function requireAuthenticatedUser() {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
        window.location.href = "/login";
        return null;
    }

    const cachedUser = readStoredUser();
    const result = await requestCurrentUser(token);

    if (result.status === "ok") {
        return result.user;
    }

    if (result.status === "unauthorized") {
        clearAuthStorage();
        window.location.href = "/login";
        return null;
    }

    return cachedUser;
}

export function logout() {
    clearAuthStorage();
    window.location.href = "/login";
}
