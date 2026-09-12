/* ============================================================
   DevTrack — tasks.js
   Task manager UI: list, create, edit, complete, delete,
   plus search, status filter and priority filter.
   All data flows through the REST API in app.js.
   ============================================================ */

const TasksApp = (() => {
    let tasks = [];
    let filter = "all";
    let search = "";
    let priority = "";

    const listEl = document.getElementById("task-list");
    const searchEl = document.getElementById("task-search");
    const filterEl = document.getElementById("task-filters");
    const priorityEl = document.getElementById("priority-filter");
    const modalEl = document.getElementById("task-modal");
    const formEl = document.getElementById("task-form");
    const titleEl = document.getElementById("task-title");
    const titleErrorEl = document.getElementById("task-title-error");
    const descEl = document.getElementById("task-description");
    const priorityInputEl = document.getElementById("task-priority");
    const projectInputEl = document.getElementById("task-project");
    const idInputEl = document.getElementById("task-id");
    const submitEl = document.getElementById("task-submit");
    const modalTitleEl = document.getElementById("task-modal-title");

    const PRIORITY_LABEL = { low: "Low", medium: "Medium", high: "High" };
    const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    function esc(text) {
        const div = document.createElement("div");
        div.textContent = text == null ? "" : String(text);
        return div.innerHTML;
    }

    async function loadTasks() {
        showSpinner(listEl);
        try {
            tasks = (await API.get("/api/tasks")).tasks || [];
            render();
        } catch (err) {
            showToast(err.message, "error");
        } finally {
            hideSpinner(listEl);
        }
    }

    function filteredTasks() {
        return tasks.filter((t) => {
            if (filter === "active" && t.status !== "pending") return false;
            if (filter === "completed" && t.status !== "completed") return false;
            if (priority && t.priority !== priority) return false;
            if (search) {
                const hay = `${t.title} ${t.description || ""}`.toLowerCase();
                if (!hay.includes(search.toLowerCase())) return false;
            }
            return true;
        });
    }

    function render() {
        const items = filteredTasks();
        if (items.length === 0) {
            const empty = search || priority || filter !== "all";
            listEl.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">${empty ? "&#128269;" : "&#128221;"}</div>
                    <h3>${empty ? "No tasks match" : "No tasks yet"}</h3>
                    <p>${empty ? "Try a different search or filter." : 'Click "New Task" to get started.'}</p>
                </div>`;
            return;
        }

        listEl.innerHTML = items.map((t) => `
            <div class="task-item ${t.status === "completed" ? "completed" : ""}" data-id="${t.id}">
                <input type="checkbox" class="task-check" ${t.status === "completed" ? "checked" : ""} aria-label="Toggle task status">
                <div class="task-info">
                    <div class="task-title">${esc(t.title)}</div>
                    ${t.description ? `<div class="task-desc">${esc(t.description)}</div>` : ""}
                    <div class="task-meta">
                        <span class="badge badge-${esc(t.priority)}">${PRIORITY_LABEL[t.priority] || t.priority}</span>
                        <span class="badge badge-status">${t.status === "completed" ? "Done" : "Active"}</span>
                        ${t.project_name ? `<span class="badge badge-project">${esc(t.project_name)}</span>` : ""}
                    </div>
                </div>
                <div class="task-actions">
                    <button class="icon-btn" data-action="edit" title="Edit task" aria-label="Edit task">&#9998;&#65039;</button>
                    <button class="icon-btn danger" data-action="delete" title="Delete task" aria-label="Delete task">&#128465;&#65039;</button>
                </div>
            </div>`).join("");
    }

    function bindRenderer() {
        listEl.addEventListener("click", async (e) => {
            const item = e.target.closest(".task-item");
            if (!item) return;

            if (e.target.classList.contains("task-check")) {
                await toggleTask(item.dataset.id, e.target.checked);
            }

            const btn = e.target.closest("[data-action]");
            if (!btn) return;

            if (btn.dataset.action === "edit") {
                openEditTask(item.dataset.id);
            } else if (btn.dataset.action === "delete") {
                await confirmDeleteTask(item.dataset.id);
            }
        });
    }

    function bindToolbar() {
        searchEl.addEventListener("input", (e) => {
            search = e.target.value;
            render();
        });

        filterEl.addEventListener("click", (e) => {
            const btn = e.target.closest(".filter-btn");
            if (!btn) return;
            filterEl.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            filter = btn.dataset.filter;
            render();
        });

        priorityEl.addEventListener("change", (e) => {
            priority = e.target.value;
            render();
        });
    }

    function bindModal() {
        document.querySelector("[data-open-task-modal]").addEventListener("click", () => {
            resetForm();
            submitEl.textContent = "Create Task";
            modalTitleEl.textContent = "New Task";
            openModal(modalEl);
        });

        document.querySelectorAll("[data-close-task-modal]").forEach((btn) => {
            btn.addEventListener("click", () => closeModal(modalEl));
        });

        formEl.addEventListener("submit", async (e) => {
            e.preventDefault();
            const title = titleEl.value.trim();
            if (!title) {
                titleEl.classList.add("error-input");
                titleErrorEl.textContent = "Title is required.";
                return;
            }
            titleEl.classList.remove("error-input");
            titleErrorEl.textContent = "";
            submitEl.disabled = true;

            const payload = {
                title,
                description: descEl.value.trim(),
                priority: priorityInputEl.value,
                project_id: projectInputEl.value ? Number(projectInputEl.value) : null,
            };

            try {
                if (idInputEl.value) {
                    await API.put(`/api/tasks/${idInputEl.value}`, payload);
                    showToast("Task updated.");
                } else {
                    await API.post("/api/tasks", payload);
                    showToast("Task created.");
                }
                closeModal(modalEl);
                resetForm();
                await reloadAll();
            } catch (err) {
                showToast(err.message, "error");
            } finally {
                submitEl.disabled = false;
            }
        });

        titleEl.addEventListener("input", () => {
            titleEl.classList.remove("error-input");
            titleErrorEl.textContent = "";
        });
    }

    function resetForm() {
        formEl.reset();
        idInputEl.value = "";
        titleEl.classList.remove("error-input");
        titleErrorEl.textContent = "";
        priorityInputEl.value = "medium";
    }

    async function toggleTask(id, completed) {
        try {
            await API.put(`/api/tasks/${id}`, { status: completed ? "completed" : "pending" });
            await reloadAll();
        } catch (err) {
            showToast(err.message, "error");
        }
    }

    function openEditTask(id) {
        const task = tasks.find((t) => String(t.id) === String(id));
        if (!task) return;
        idInputEl.value = task.id;
        titleEl.value = task.title;
        descEl.value = task.description || "";
        priorityInputEl.value = task.priority;
        projectInputEl.value = task.project_id || "";
        submitEl.textContent = "Save Changes";
        modalTitleEl.textContent = "Edit Task";
        openModal(modalEl);
    }

    async function confirmDeleteTask(id) {
        if (!window.confirm("Delete this task? This cannot be undone.")) return;
        try {
            await API.del(`/api/tasks/${id}`);
            showToast("Task deleted.", "info");
            await reloadAll();
        } catch (err) {
            showToast(err.message, "error");
        }
    }

    async function refreshStats() {
        try {
            const stats = await API.get("/api/analytics");
            const setNum = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            };
            setNum("stat-total", stats.total);
            setNum("stat-completed", stats.completed);
            setNum("stat-projects", stats.projects);
            setNum("stat-streak", stats.current_streak);
            const streakEl = document.getElementById("streak-value");
            if (streakEl) streakEl.innerHTML = `${stats.current_streak} <small style="font-size: 16px; color: var(--muted);">days</small>`;
            const longestEl = document.getElementById("streak-longest");
            if (longestEl) longestEl.textContent = `Longest streak: ${stats.longest_streak} days`;
        } catch (_) {
            /* stats are non-critical; fall back silently */
        }
    }

    async function reloadAll() {
        await Promise.all([loadTasks(), refreshStats()]);
        if (window.ContributionGraph) window.ContributionGraph.load();
        if (window.ProductivityChart) window.ProductivityChart.load();
    }

    function init() {
        bindRenderer();
        bindToolbar();
        bindModal();
        loadTasks();
        refreshStats();
    }

    return { init, reloadAll };
})();

document.addEventListener("DOMContentLoaded", () => TasksApp.init());

/* Faster than a full-text search: rerender happens client side. */