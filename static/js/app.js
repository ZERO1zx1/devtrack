/* ============================================================
   DevTrack — app.js
   Theme switcher (dark / light / system), toasts, modals,
   loading helpers and a small fetch-based API client.
   ============================================================ */

const API = {
    async request(url, options = {}) {
        const config = {
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            ...options,
        };
        if (config.body && typeof config.body !== "string") {
            config.body = JSON.stringify(config.body);
        }
        const res = await fetch(url, config);
        if (res.status === 204) return null;
        let data = null;
        try {
            data = await res.json();
        } catch (_) {
            data = null;
        }
        if (!res.ok) {
            const message = (data && data.error) ? data.error : `Request failed (${res.status})`;
            throw new Error(message);
        }
        return data;
    },

    get(url) {
        return this.request(url);
    },
    post(url, body) {
        return this.request(url, { method: "POST", body });
    },
    put(url, body) {
        return this.request(url, { method: "PUT", body });
    },
    del(url) {
        return this.request(url, { method: "DELETE" });
    },
};

/* ---------------- Toast notifications ---------------- */

function showToast(message, type = "success", duration = 2800) {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add("out");
        setTimeout(() => toast.remove(), 260);
    }, duration);
}

/* ---------------- Modal helpers ---------------- */

function openModal(overlay) {
    overlay.classList.remove("hidden");
    const input = overlay.querySelector("input, textarea, select");
    if (input) setTimeout(() => input.focus(), 60);
}

function closeModal(overlay) {
    overlay.classList.add("hidden");
}

/* ---------------- Loading helpers ---------------- */

function showSpinner(container) {
    const existing = container.querySelector(".spinner");
    if (!existing) container.innerHTML = '<div class="spinner"></div>';
}

function hideSpinner(container) {
    container.querySelectorAll(".spinner").forEach((s) => s.remove());
}

/* ---------------- Theme switcher ---------------- */

const THEME_KEY = "devtrack-theme";

function resolveTheme(choice) {
    if (choice === "dark" || choice === "light") return choice;
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function applyTheme(choice) {
    const resolved = resolveTheme(choice);
    document.documentElement.dataset.theme = resolved;
    localStorage.setItem(THEME_KEY, choice);

    document.querySelectorAll("[data-theme-switcher] [data-theme]").forEach((btn) => {
        const active = btn.dataset.theme === choice;
        btn.classList.toggle("btn-primary", active);
        btn.classList.toggle("btn-ghost", !active);
    });
}

function initTheme() {
    let choice = localStorage.getItem(THEME_KEY) || "system";
    const stored = localStorage.getItem(THEME_KEY);
    if (stored) choice = stored;

    document.querySelectorAll("[data-theme-switcher] [data-theme]").forEach((btn) => {
        btn.addEventListener("click", () => applyTheme(btn.dataset.theme));
    });

    const quick = document.querySelector("[data-quick-theme]");
    if (quick) {
        quick.addEventListener("click", () => {
            const current = localStorage.getItem(THEME_KEY) || "system";
            const resolved = resolveTheme(current);
            applyTheme(resolved === "dark" ? "light" : "dark");
        });
    }

    if (choice === "system") {
        window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", () => {
            const current = localStorage.getItem(THEME_KEY) || "system";
            if (current === "system") applyTheme("system");
        });
    }

    applyTheme(choice);
}

document.addEventListener("DOMContentLoaded", () => {
    initTheme();

    document.querySelectorAll(".modal-overlay").forEach((overlay) => {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) closeModal(overlay);
        });
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && !overlay.classList.contains("hidden")) closeModal(overlay);
        });
    });
});