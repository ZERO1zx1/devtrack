/* ============================================================
   DevTrack — core/toast.js
   UI helpers shared by every page: toast notifications, modal
   open/close, loading spinners and overlay keyboard handling.
   ============================================================ */

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

function openModal(overlay) {
    overlay.classList.remove("hidden");
    const input = overlay.querySelector("input, textarea, select");
    if (input) setTimeout(() => input.focus(), 60);
}

function closeModal(overlay) {
    overlay.classList.add("hidden");
}

function showSpinner(container) {
    const existing = container.querySelector(".spinner");
    if (!existing) container.innerHTML = '<div class="spinner"></div>';
}

function hideSpinner(container) {
    container.querySelectorAll(".spinner").forEach((s) => s.remove());
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".modal-overlay").forEach((overlay) => {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) closeModal(overlay);
        });
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && !overlay.classList.contains("hidden")) closeModal(overlay);
        });
    });
});