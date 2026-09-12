/* ============================================================
   DevTrack — contributions.js
   GitHub-style 365-day contribution calendar rendered from
   the /api/analytics activity map. Hovering a cell shows a
   tooltip like "September 12 — 5 tasks completed".
   ============================================================ */

const ContributionGraph = (() => {
    const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const SHORT_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const LABEL_ROWS = [1, 3, 5]; // Mon, Wed, Fri

    const headEl = document.getElementById("graph-head");
    const bodyEl = document.getElementById("graph-body");

    let tooltip = null;

    function ensureTooltip() {
        if (!tooltip) {
            tooltip = document.createElement("div");
            tooltip.className = "c-tooltip";
            tooltip.style.display = "none";
            document.body.appendChild(tooltip);
        }
        return tooltip;
    }

    function levelFor(count) {
        if (count <= 0) return 0;
        if (count <= 2) return 1;
        if (count <= 4) return 2;
        if (count <= 7) return 3;
        return 4;
    }

    function toLocalDateKey(d) {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, "0");
        const day = String(d.getDate()).padStart(2, "0");
        return `${y}-${m}-${day}`;
    }

    function render(activity) {
        if (!headEl || !bodyEl) return;

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Start on the Sunday 51 weeks before the Sunday of the current week.
        const start = new Date(today);
        start.setDate(start.getDate() - ((start.getDay() + 1) % 7)); // back to Monday
        start.setDate(start.getDate() - 7); // one full week back
        start.setDate(start.getDate() - 51 * 7); // 52 weeks total
        if (start.getDay() !== 0) {
            start.setDate(start.getDate() - start.getDay()); // snap to Sunday
        }

        // Month labels: one header cell per week where month changes.
        headEl.innerHTML = "";
        let currentMonth = -1;
        const cursor = new Date(start);
        for (let week = 0; week < 53; week++) {
            const span = document.createElement("span");
            span.className = "month-label";
            if (cursor.getMonth() !== currentMonth) {
                currentMonth = cursor.getMonth();
                span.textContent = MONTHS[cursor.getMonth()].slice(0, 3);
            } else {
                span.textContent = "\u00A0";
            }
            headEl.appendChild(span);
            cursor.setDate(cursor.getDate() + 7);
        }

        // Day cells.
        bodyEl.innerHTML = "";
        cursor.setTime(start.getTime());
        for (let week = 0; week < 53; week++) {
            for (let day = 0; day < 7; day++) {
                const cell = document.createElement("div");
                cell.className = "cell";
                cell.dataset.level = "0";

                if (cursor <= today) {
                    const key = toLocalDateKey(cursor);
                    const count = (activity && activity[key]) || 0;
                    cell.dataset.level = levelFor(count);
                    cell.dataset.count = count;
                    cell.dataset.date = key;

                    cell.addEventListener("mouseenter", (e) => showTooltip(e, cell));
                    cell.addEventListener("mousemove", moveTooltip);
                    cell.addEventListener("mouseleave", hideTooltip);
                } else {
                    cell.style.visibility = "hidden";
                }
                bodyEl.appendChild(cell);
                cursor.setDate(cursor.getDate() + 1);
            }
        }

        // Weekday labels (Mon, Wed, Fri) via absolute positioning.
        SHORT_DAYS.forEach((label, idx) => {
            if (!LABEL_ROWS.includes(idx)) return;
            const el = document.createElement("span");
            el.className = "day-label";
            el.style.top = `${idx * 17}px`;
            el.textContent = label;
            bodyEl.appendChild(el);
        });
    }

    function showTooltip(e, cell) {
        const tip = ensureTooltip();
        const count = parseInt(cell.dataset.count, 10) || 0;
        const [y, m, d] = cell.dataset.date.split("-").map(Number);
        const label = `${MONTHS[m - 1]} ${d}`;
        tip.textContent = count > 0
            ? `${label} — ${count} ${count === 1 ? "task" : "tasks"} completed`
            : `${label} — no activity`;
        tip.style.display = "block";
        moveTooltip(e);
    }

    function moveTooltip(e) {
        const tip = ensureTooltip();
        const pad = 12;
        let x = e.clientX + pad;
        let y = e.clientY + pad;
        if (x + 220 > window.innerWidth) x = e.clientX - 220;
        tip.style.left = `${x}px`;
        tip.style.top = `${y}px`;
    }

    function hideTooltip() {
        ensureTooltip().style.display = "none";
    }

    async function load() {
        try {
            const data = await API.get("/api/analytics");
            render(data.activity || {});
        } catch (_) {
            render({});
        }
    }

    function init() {
        load();
    }

    return { init, load };
})();

document.addEventListener("DOMContentLoaded", () => ContributionGraph.init());