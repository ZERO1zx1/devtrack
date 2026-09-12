/* ============================================================
   DevTrack — projects.js
   Project manager: list, create, edit, delete. Progress % is
   recomputed by the backend from completed task ratio.
   ============================================================ */

const ProjectsApp = (() => {
    const gridEl = document.getElementById("projects-grid");
    const modalEl = document.getElementById("project-modal");
    const formEl = document.getElementById("project-form");
    const nameEl = document.getElementById("project-name");
    const nameErrorEl = document.getElementById("project-name-error");
    const descEl = document.getElementById("project-description");
    const startEl = document.getElementById("project-start");
    const deadlineEl = document.getElementById("project-deadline");
    const idEl = document.getElementById("project-id");
    const submitEl = document.getElementById("project-submit");
    const modalTitleEl = document.getElementById("project-modal-title");

    let projects = [];

    function esc(text) {
        const div = document.createElement("div");
        div.textContent = text == null ? "" : String(text);
        return div.innerHTML;
    }

    function fmtDate(iso) {
        if (!iso) return "—";
        const [y, m, d] = iso.split("-");
        return `${d}.${m}.${y}`;
    }

    async function loadProjects() {
        showSpinner(gridEl);
        try {
            projects = (await API.get("/api/projects")).projects || [];
            render();
        } catch (err) {
            showToast(err.message, "error");
            gridEl.innerHTML = "";
        } finally {
            hideSpinner(gridEl);
        }
    }

    function render() {
        if (projects.length === 0) {
            gridEl.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <div class="empty-icon">&#128736;</div>
                    <h3>No projects yet</h3>
                    <p>Create a project and group your tasks around a real goal.</p>
                </div>`;
            return;
        }
        gridEl.innerHTML = projects.map((p) => `
            <div class="card project-card" data-id="${p.id}">
                <h3>${esc(p.name)}
                    <span class="badge badge-project">${p.progress}%</span>
                </h3>
                ${p.description ? `<p class="project-desc">${esc(p.description)}</p>` : ""}
                <div class="progress" role="progressbar" aria-valuenow="${p.progress}" aria-valuemin="0" aria-valuemax="100">
                    <div class="progress-fill" style="width: ${Math.min(100, p.progress)}%"></div>
                </div>
                <div class="project-meta">
                    <span>&#128197; Start: ${fmtDate(p.start_date)}</span>
                    <span>&#9200; Due: ${fmtDate(p.deadline)}</span>
                    <span>&#128221; ${p.tasks_count} ${p.tasks_count === 1 ? "task" : "tasks"}</span>
                </div>
                <div class="card-footer">
                    <span style="font-size:12px; color:var(--muted);">Created ${fmtDate(p.created_at)}</span>
                    <div style="display:flex; gap:6px;">
                        <button class="btn btn-sm btn-outline" data-action="edit">Edit</button>
                        <button class="btn btn-sm btn-danger" data-action="delete">Delete</button>
                    </div>
                </div>
            </div>`).join("");
    }

    function bindRenderer() {
        gridEl.addEventListener("click", async (e) => {
            const btn = e.target.closest("[data-action]");
            if (!btn) return;
            const card = e.target.closest(".project-card");
            if (btn.dataset.action === "edit") {
                openEditProject(card.dataset.id);
            } else if (btn.dataset.action === "delete") {
                if (!window.confirm("Delete this project? Its tasks will remain but become unassigned.")) return;
                try {
                    await API.del(`/api/projects/${card.dataset.id}`);
                    showToast("Project deleted.", "info");
                    await loadProjects();
                } catch (err) {
                    showToast(err.message, "error");
                }
            }
        });
    }

    function bindModal() {
        document.querySelector("[data-open-project-modal]").addEventListener("click", () => {
            formEl.reset();
            idEl.value = "";
            submitEl.textContent = "Create Project";
            modalTitleEl.textContent = "New Project";
            openModal(modalEl);
        });

        document.querySelectorAll("[data-close-project-modal]").forEach((btn) => {
            btn.addEventListener("click", () => closeModal(modalEl));
        });

        formEl.addEventListener("submit", async (e) => {
            e.preventDefault();
            const name = nameEl.value.trim();
            if (!name) {
                nameEl.classList.add("error-input");
                nameErrorEl.textContent = "Project name is required.";
                return;
            }
            nameEl.classList.remove("error-input");
            nameErrorEl.textContent = "";
            submitEl.disabled = true;

            const payload = {
                name,
                description: descEl.value.trim(),
                start_date: startEl.value || null,
                deadline: deadlineEl.value || null,
            };

            try {
                if (idEl.value) {
                    await API.put(`/api/projects/${idEl.value}`, payload);
                    showToast("Project updated.");
                } else {
                    await API.post("/api/projects", payload);
                    showToast("Project created.");
                }
                closeModal(modalEl);
                await loadProjects();
            } catch (err) {
                showToast(err.message, "error");
            } finally {
                submitEl.disabled = false;
            }
        });

        nameEl.addEventListener("input", () => {
            nameEl.classList.remove("error-input");
            nameErrorEl.textContent = "";
        });
    }

    function openEditProject(id) {
        const p = projects.find((x) => String(x.id) === String(id));
        if (!p) return;
        idEl.value = p.id;
        nameEl.value = p.name;
        descEl.value = p.description || "";
        startEl.value = p.start_date || "";
        deadlineEl.value = p.deadline || "";
        submitEl.textContent = "Save Changes";
        modalTitleEl.textContent = "Edit Project";
        openModal(modalEl);
    }

    function init() {
        bindRenderer();
        bindModal();
        loadProjects();
    }

    return { init };
})();

document.addEventListener("DOMContentLoaded", () => ProjectsApp.init());