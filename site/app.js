const { workers, teams } = window.AIRO_DATA;

const workerGrid = document.querySelector("#workerGrid");
const teamGrid = document.querySelector("#teamGrid");
const workerBySlug = Object.fromEntries(workers.map((worker) => [worker.slug, worker]));

const agentSprites = {
  "review-analysis-worker": {
    bg: "#f7e1d6",
    pixels: [
      [8, 3, 8, 2, "#2d211c"],
      [7, 5, 10, 6, "#d69a73"],
      [9, 7, 2, 1, "#1a1815"],
      [14, 7, 2, 1, "#1a1815"],
      [11, 9, 3, 1, "#8f4b37"],
      [6, 12, 12, 7, "#b8482a"],
      [8, 13, 8, 5, "#fffdf7"],
      [11, 13, 2, 5, "#4e6250"],
      [7, 19, 4, 2, "#43342d"],
      [13, 19, 4, 2, "#43342d"],
      [17, 6, 3, 1, "#1a1815"],
      [16, 7, 1, 3, "#1a1815"],
      [20, 7, 1, 3, "#1a1815"],
      [17, 10, 3, 1, "#1a1815"],
      [20, 11, 1, 1, "#1a1815"],
      [21, 12, 1, 2, "#1a1815"]
    ]
  },
  "seo-geo-brief-worker": {
    bg: "#e6ebe2",
    pixels: [
      [8, 4, 8, 2, "#314a35"],
      [7, 6, 10, 6, "#d9a177"],
      [9, 8, 2, 1, "#1a1815"],
      [14, 8, 2, 1, "#1a1815"],
      [11, 10, 3, 1, "#8f4b37"],
      [6, 13, 12, 6, "#4e6250"],
      [8, 14, 8, 4, "#fffdf7"],
      [7, 19, 4, 2, "#26382a"],
      [13, 19, 4, 2, "#26382a"],
      [4, 5, 2, 1, "#b8482a"],
      [3, 4, 1, 1, "#b8482a"],
      [2, 3, 1, 1, "#b8482a"],
      [18, 4, 1, 1, "#b8482a"],
      [19, 3, 1, 1, "#b8482a"],
      [20, 2, 1, 1, "#b8482a"],
      [12, 1, 1, 3, "#1a1815"],
      [11, 0, 3, 1, "#1a1815"]
    ]
  },
  "proposal-draft-worker": {
    bg: "#efeadd",
    pixels: [
      [8, 3, 8, 3, "#3a2a24"],
      [7, 6, 10, 6, "#d9a177"],
      [9, 8, 2, 1, "#1a1815"],
      [14, 8, 2, 1, "#1a1815"],
      [11, 10, 3, 1, "#8f4b37"],
      [6, 13, 12, 6, "#2f4f66"],
      [9, 13, 6, 5, "#fffdf7"],
      [11, 13, 2, 5, "#b8482a"],
      [7, 19, 4, 2, "#1e303d"],
      [13, 19, 4, 2, "#1e303d"],
      [2, 14, 5, 4, "#6a4a2e"],
      [3, 13, 3, 1, "#6a4a2e"],
      [2, 15, 5, 1, "#efeadd"],
      [17, 14, 4, 5, "#fffdf7"],
      [18, 15, 2, 1, "#b8482a"],
      [18, 17, 2, 1, "#b8482a"]
    ]
  },
  "legal-docs-draft-worker": {
    bg: "#e9e4d8",
    pixels: [
      [8, 3, 8, 2, "#2b2b2b"],
      [7, 5, 10, 7, "#d9a177"],
      [8, 7, 3, 2, "#1a1815"],
      [14, 7, 3, 2, "#1a1815"],
      [11, 8, 3, 1, "#1a1815"],
      [11, 10, 3, 1, "#8f4b37"],
      [6, 13, 12, 6, "#1f2f3a"],
      [8, 14, 8, 4, "#fffdf7"],
      [7, 19, 4, 2, "#1a1815"],
      [13, 19, 4, 2, "#1a1815"],
      [19, 5, 1, 9, "#b8482a"],
      [17, 7, 5, 1, "#b8482a"],
      [16, 9, 2, 2, "#b8482a"],
      [21, 9, 2, 2, "#b8482a"],
      [17, 12, 5, 1, "#b8482a"]
    ]
  },
  "youtube-content-writer": {
    bg: "#f1e3c7",
    pixels: [
      [8, 3, 8, 2, "#2d211c"],
      [7, 5, 10, 7, "#d9a177"],
      [9, 7, 2, 1, "#1a1815"],
      [14, 7, 2, 1, "#1a1815"],
      [11, 10, 3, 1, "#8f4b37"],
      [6, 13, 12, 6, "#4e6250"],
      [8, 14, 8, 4, "#fffdf7"],
      [7, 19, 4, 2, "#43342d"],
      [13, 19, 4, 2, "#43342d"],
      [18, 12, 5, 7, "#fffdf7"],
      [18, 12, 5, 1, "#b8482a"],
      [19, 14, 3, 1, "#6a655b"],
      [19, 16, 3, 1, "#6a655b"],
      [2, 13, 5, 1, "#6a4a2e"],
      [2, 14, 1, 4, "#6a4a2e"],
      [3, 17, 4, 1, "#6a4a2e"],
      [5, 12, 1, 1, "#1a1815"],
      [6, 11, 1, 1, "#1a1815"]
    ]
  },
  "youtube-content-planner": {
    bg: "#e6ebe2",
    pixels: [
      [8, 3, 8, 2, "#2d211c"],
      [7, 5, 10, 7, "#d9a177"],
      [9, 7, 2, 1, "#1a1815"],
      [14, 7, 2, 1, "#1a1815"],
      [11, 10, 3, 1, "#8f4b37"],
      [6, 13, 12, 6, "#4e6250"],
      [8, 14, 8, 4, "#fffdf7"],
      [7, 19, 4, 2, "#26382a"],
      [13, 19, 4, 2, "#26382a"],
      [18, 4, 4, 4, "#fffdf7"],
      [19, 5, 2, 1, "#b8482a"],
      [19, 7, 2, 1, "#b8482a"],
      [3, 5, 3, 3, "#b8482a"],
      [4, 8, 1, 3, "#b8482a"]
    ]
  },
  "youtube-script-writer": {
    bg: "#f1e3c7",
    pixels: [
      [8, 3, 8, 2, "#2d211c"],
      [7, 5, 10, 7, "#d9a177"],
      [9, 7, 2, 1, "#1a1815"],
      [14, 7, 2, 1, "#1a1815"],
      [11, 10, 3, 1, "#8f4b37"],
      [6, 13, 12, 6, "#b8482a"],
      [8, 14, 8, 4, "#fffdf7"],
      [7, 19, 4, 2, "#43342d"],
      [13, 19, 4, 2, "#43342d"],
      [18, 12, 5, 7, "#fffdf7"],
      [18, 12, 5, 1, "#4e6250"],
      [19, 14, 3, 1, "#6a655b"],
      [19, 16, 3, 1, "#6a655b"],
      [2, 13, 5, 1, "#6a4a2e"],
      [2, 14, 1, 4, "#6a4a2e"],
      [3, 17, 4, 1, "#6a4a2e"]
    ]
  },
  "youtube-video-producer": {
    bg: "#e9e4d8",
    pixels: [
      [8, 3, 8, 2, "#2b2b2b"],
      [7, 5, 10, 7, "#d9a177"],
      [9, 7, 2, 1, "#1a1815"],
      [14, 7, 2, 1, "#1a1815"],
      [11, 10, 3, 1, "#8f4b37"],
      [6, 13, 12, 6, "#2f4f66"],
      [8, 14, 8, 4, "#fffdf7"],
      [7, 19, 4, 2, "#1e303d"],
      [13, 19, 4, 2, "#1e303d"],
      [18, 5, 5, 4, "#1a1815"],
      [19, 6, 2, 2, "#fffdf7"],
      [22, 6, 1, 2, "#1a1815"],
      [2, 12, 5, 4, "#6a4a2e"],
      [3, 13, 3, 1, "#efeadd"],
      [3, 15, 3, 1, "#efeadd"]
    ]
  },
  "youtube-channel-manager": {
    bg: "#efeadd",
    pixels: [
      [8, 3, 8, 2, "#314a35"],
      [7, 5, 10, 7, "#d9a177"],
      [8, 7, 3, 2, "#1a1815"],
      [14, 7, 3, 2, "#1a1815"],
      [11, 8, 3, 1, "#1a1815"],
      [11, 10, 3, 1, "#8f4b37"],
      [6, 13, 12, 6, "#4e6250"],
      [8, 14, 8, 4, "#fffdf7"],
      [7, 19, 4, 2, "#26382a"],
      [13, 19, 4, 2, "#26382a"],
      [18, 12, 5, 7, "#fffdf7"],
      [19, 17, 1, 1, "#b8482a"],
      [20, 15, 1, 3, "#b8482a"],
      [21, 13, 1, 5, "#b8482a"],
      [3, 4, 2, 1, "#b8482a"],
      [2, 3, 1, 1, "#b8482a"],
      [5, 5, 1, 1, "#b8482a"]
    ]
  },
  "job-role-analyst": {
    bg: "#ece8f0",
    pixels: [
      [7, 2, 10, 3, "#2b211d"],
      [6, 5, 12, 2, "#2b211d"],
      [5, 7, 3, 6, "#2b211d"],
      [16, 7, 3, 6, "#2b211d"],
      [7, 5, 10, 8, "#d9a177"],
      [8, 7, 3, 3, "#1a1815"],
      [14, 7, 3, 3, "#1a1815"],
      [9, 8, 1, 1, "#fffdf7"],
      [15, 8, 1, 1, "#fffdf7"],
      [11, 8, 3, 1, "#1a1815"],
      [11, 11, 3, 1, "#8f4b37"],
      [6, 14, 12, 6, "#2f4f66"],
      [8, 15, 8, 4, "#fffdf7"],
      [11, 15, 2, 4, "#b8482a"],
      [7, 20, 4, 1, "#1e303d"],
      [13, 20, 4, 1, "#1e303d"],
      [18, 11, 5, 7, "#fffdf7"],
      [19, 12, 3, 1, "#4e6250"],
      [19, 14, 3, 1, "#4e6250"],
      [19, 16, 2, 1, "#4e6250"],
      [3, 4, 2, 2, "#f0d15d"],
      [2, 6, 1, 1, "#f0d15d"],
      [5, 6, 1, 1, "#f0d15d"]
    ]
  }
};

function pill(text) {
  return `<span class="pill">${text}</span>`;
}

const downloadIcon = `<svg class="hire-icon" viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" focusable="false"><path d="M8 1.5v8m0 0L4.75 6.25M8 9.5l3.25-3.25M2.5 12.5h11" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

function hireButton(worker) {
  if (worker.downloadUrl) {
    return `<a class="hire-button" href="${worker.downloadUrl}" download data-hire aria-label="${worker.name} 채용하기 (zip 다운로드)">${downloadIcon}<span>직원 채용하기</span></a>`;
  }

  return `<span class="hire-button is-pending" data-hire aria-disabled="true">${downloadIcon}<span>채용 준비 중</span></span>`;
}

function pixelAgent(worker) {
  const sprite = agentSprites[worker.slug];

  if (!sprite) {
    return "";
  }

  const pixels = sprite.pixels
    .map(
      ([x, y, width, height, color]) =>
        `<rect x="${x}" y="${y}" width="${width}" height="${height}" fill="${color}" />`
    )
    .join("");

  return `
    <div class="agent-sprite" style="--agent-bg: ${sprite.bg}" aria-hidden="true">
      <svg viewBox="0 0 24 24" role="img" focusable="false" shape-rendering="crispEdges">
        ${pixels}
      </svg>
    </div>
  `;
}

function renderWorkers() {
  workerGrid.innerHTML = workers
    .map(
      (worker, index) => `
        <article class="card worker-card" data-slug="${worker.slug}" role="button" tabindex="0" aria-haspopup="dialog" aria-label="${worker.name} 상세 보기">
          <div class="card-top">
            <span class="category-chip">${worker.category}</span>
            <span class="card-no">W-${String(index + 1).padStart(2, "0")}</span>
          </div>
          <div class="worker-main">
            ${pixelAgent(worker)}
            <div>
              <h3>${worker.name}</h3>
              <p>${worker.summary}</p>
            </div>
          </div>
          <div class="tags">
            ${worker.skills.map(pill).join("")}
          </div>
          <div class="card-footer">
            <span>${worker.tools.join(" + ")}</span>
            <strong>→ ${worker.output}</strong>
          </div>
          <div class="worker-actions">
            <span class="card-cta" aria-hidden="true">워크플로우 · 세팅 가이드 보기 →</span>
            ${hireButton(worker)}
          </div>
        </article>
      `
    )
    .join("");
}

const modal = document.querySelector("#workerModal");
const modalBody = modal.querySelector(".modal-body");
let lastFocused = null;

function stepList(items) {
  return `<ol class="modal-steps">${items
    .map((item) => `<li>${item}</li>`)
    .join("")}</ol>`;
}

function advancedList(items) {
  return `<div class="modal-advanced">${items
    .map(
      (item) => `
        <article>
          <h4>${item.title}</h4>
          <p>${item.body}</p>
        </article>
      `
    )
    .join("")}</div>`;
}

function openWorkerModal(slug) {
  const worker = workerBySlug[slug];

  if (!worker || !worker.details) {
    return;
  }

  const { workflow, setup, advanced } = worker.details;

  modalBody.innerHTML = `
    <div class="modal-hero">
      ${pixelAgent(worker)}
      <div>
        <span class="category-chip">${worker.category}</span>
        <h3 id="workerModalTitle">${worker.name}</h3>
        <p>${worker.summary}</p>
        <div class="modal-meta">
          <span>${worker.tools.join(" + ")}</span>
          <strong>→ ${worker.output}</strong>
        </div>
        <div class="modal-hire">${hireButton(worker)}</div>
      </div>
    </div>
    <section class="modal-section">
      <p class="modal-eyebrow">WORKFLOW · 워크플로우</p>
      ${stepList(workflow)}
    </section>
    <section class="modal-section">
      <p class="modal-eyebrow">SETUP · 초기 세팅</p>
      ${stepList(setup)}
    </section>
    <section class="modal-section">
      <p class="modal-eyebrow">ADVANCED · 세부 세팅</p>
      ${advancedList(advanced)}
    </section>
  `;

  lastFocused = document.activeElement;
  modal.hidden = false;
  document.body.style.overflow = "hidden";
  modal.querySelector(".modal-close").focus();
}

function closeWorkerModal() {
  modal.hidden = true;
  document.body.style.overflow = "";

  if (lastFocused && typeof lastFocused.focus === "function") {
    lastFocused.focus();
  }
}

workerGrid.addEventListener("click", (event) => {
  if (event.target.closest("[data-hire]")) {
    return;
  }

  const card = event.target.closest(".worker-card");

  if (card) {
    openWorkerModal(card.dataset.slug);
  }
});

workerGrid.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") {
    return;
  }

  if (event.target.closest("[data-hire]")) {
    return;
  }

  const card = event.target.closest(".worker-card");

  if (card) {
    event.preventDefault();
    openWorkerModal(card.dataset.slug);
  }
});

modal.addEventListener("click", (event) => {
  if (event.target.closest(".modal-close") || event.target === modal.querySelector(".modal-overlay")) {
    closeWorkerModal();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !modal.hidden) {
    closeWorkerModal();
  }
});

function renderTeamMembers(team) {
  return team.members
    .map((slug) => {
      const worker = workerBySlug[slug];

      if (!worker) {
        return "";
      }

      return `
        <li>
          ${pixelAgent(worker)}
          <span>${worker.name}</span>
        </li>
      `;
    })
    .join("");
}

function renderTeams() {
  teamGrid.innerHTML = teams
    .map(
      (team) => `
        <article class="card team-card">
          <div class="card-top">
            <div>
              <span class="category-chip">${team.category}</span>
              <span class="team-version">${team.version}</span>
            </div>
            <span class="card-no">${team.status}</span>
          </div>
          <div class="team-layout">
            <div>
              <h3>${team.title}</h3>
              <p>${team.summary}</p>
              <div class="tags">
                ${team.includes.map(pill).join("")}
              </div>
              <div class="runtime">${team.runtime}</div>
            </div>
            <ul class="team-roster" aria-label="${team.title} 구성원">
              ${renderTeamMembers(team)}
            </ul>
          </div>
          <div class="card-footer">
            <span>${team.requiredKeys.join(" + ")}</span>
            <a href="${team.downloadUrl}" download>팀 zip 다운로드 ↓</a>
          </div>
        </article>
      `
    )
    .join("");
}

renderWorkers();
renderTeams();
