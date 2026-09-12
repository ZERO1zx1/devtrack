/* ============================================================
   DevTrack — charts.js
   Tiny dependency-free canvas bar chart showing weekly
   completed tasks (productivity analytics).
   ============================================================ */

const ProductivityChart = (() => {
    const canvas = document.getElementById("weekly-chart");
    let data = [];

    function draw() {
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const cssWidth = canvas.parentElement.clientWidth || 400;
        const cssHeight = 220;
        const dpr = window.devicePixelRatio || 1;

        canvas.width = Math.round(cssWidth * dpr);
        canvas.height = Math.round(cssHeight * dpr);
        canvas.style.width = `${cssWidth}px`;
        canvas.style.height = `${cssHeight}px`;
        ctx.scale(dpr, dpr);

        ctx.clearRect(0, 0, cssWidth, cssHeight);

        const theme = document.documentElement.dataset.theme || "dark";
        const isDark = theme === "dark";
        const muted = isDark ? "#8b949e" : "#656d76";
        const grid = isDark ? "#30363d" : "#d0d7de";
        const barColor = isDark ? "#58a6ff" : "#0969da";
        const barTop = isDark ? "#79c0ff" : "#0550ae";
        const text = isDark ? "#e6edf3" : "#1f2328";

        const pad = { top: 24, right: 12, bottom: 26, left: 34 };
        const innerW = cssWidth - pad.left - pad.right;
        const innerH = cssHeight - pad.top - pad.bottom;

        const maxVal = Math.max(1, ...data.map((d) => d.count));
        const n = data.length || 7;
        const slot = innerW / n;
        const barW = Math.min(34, slot * 0.6);

        // Grid lines + y labels
        ctx.font = "11px Segoe UI, sans-serif";
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        for (let g = 0; g <= 4; g++) {
            const val = Math.round((maxVal * g) / 4);
            const y = pad.top + innerH - (innerH * g) / 4;
            ctx.strokeStyle = grid;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(pad.left, y + 0.5);
            ctx.lineTo(cssWidth - pad.right, y + 0.5);
            ctx.stroke();
            ctx.fillStyle = muted;
            ctx.fillText(String(val), pad.left - 8, y);
        }

        // Bars
        data.forEach((d, i) => {
            const h = (d.count / maxVal) * innerH;
            const x = pad.left + i * slot + (slot - barW) / 2;
            const y = pad.top + innerH - h;
            const grad = ctx.createLinearGradient(0, y, 0, pad.top + innerH);
            grad.addColorStop(0, barTop);
            grad.addColorStop(1, barColor);
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.roundRect(x, y, barW, h, 3);
            ctx.fill();

            ctx.fillStyle = muted;
            ctx.textAlign = "center";
            ctx.fillText(d.count > 0 ? String(d.count) : "", x + barW / 2, y - 10);

            ctx.fillStyle = text;
            ctx.textBaseline = "top";
            ctx.fillText(d.label, x + barW / 2, pad.top + innerH + 8);
            ctx.textBaseline = "middle";
        });

        if (data.every((d) => d.count === 0)) {
            ctx.fillStyle = muted;
            ctx.textAlign = "center";
            ctx.fillText("No completed tasks this week yet.", cssWidth / 2, pad.top + innerH / 2);
            ctx.textAlign = "right";
        }
    }

    async function load() {
        try {
            const analytics = await API.get("/api/analytics");
            data = analytics.weekly || [];
        } catch (_) {
            data = [];
        }
        draw();
    }

    function init() {
        load();
        window.addEventListener("resize", draw);
    }

    return { init, load };
})();

document.addEventListener("DOMContentLoaded", () => ProductivityChart.init());