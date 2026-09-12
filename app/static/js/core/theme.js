/* ============================================================
   DevTrack — core/theme.js
   Theme switcher: dark / light / system preference, persisted
   in localStorage and wired to the sidebar switcher plus the
   quick toggle button in the top bar.
   ============================================================ */

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

    window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", () => {
        const current = localStorage.getItem(THEME_KEY) || "system";
        if (current === "system") applyTheme("system");
    });

    applyTheme(choice);
}

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
});