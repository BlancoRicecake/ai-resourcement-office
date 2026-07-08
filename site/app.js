const { workers, bundles } = window.AIRO_DATA;

const workerGrid = document.querySelector("#workerGrid");
const bundleGrid = document.querySelector("#bundleGrid");
const filters = document.querySelectorAll(".filter");

function pill(text) {
  return `<span class="pill">${text}</span>`;
}

function renderWorkers() {
  workerGrid.innerHTML = workers
    .map(
      (worker, index) => `
        <article class="card">
          <div class="card-top">
            <span class="category-chip">${worker.category}</span>
            <span class="card-no">W-${String(index + 1).padStart(2, "0")}</span>
          </div>
          <div>
            <h3>${worker.name}</h3>
            <p>${worker.summary}</p>
          </div>
          <div class="tags">
            ${worker.skills.map(pill).join("")}
          </div>
          <div class="card-footer">
            <span>${worker.tools.join(" + ")}</span>
            <strong>→ ${worker.output}</strong>
          </div>
        </article>
      `
    )
    .join("");
}

function renderBundles(category = "all") {
  const visible =
    category === "all"
      ? bundles
      : bundles.filter((bundle) => bundle.category === category);

  bundleGrid.innerHTML = visible
    .map(
      (bundle) => `
        <article class="card bundle-card">
          <div class="card-top">
            <div>
              <span class="category-chip">${bundle.category}</span>
              <span class="bundle-difficulty">${bundle.difficulty}</span>
            </div>
          </div>
          <div>
            <h3>${bundle.title}</h3>
            <p>${bundle.description}</p>
          </div>
          <div class="tags">
            ${bundle.includes.map(pill).join("")}
          </div>
          <div class="runtime">${bundle.runtime}</div>
          <div class="card-footer">
            <span>${bundle.estimatedCost}</span>
            <a href="${bundle.downloadUrl}" target="_blank" rel="noopener">zip 다운로드 ↓</a>
          </div>
        </article>
      `
    )
    .join("");
}

filters.forEach((button) => {
  button.addEventListener("click", () => {
    filters.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    renderBundles(button.dataset.filter);
  });
});

renderWorkers();
renderBundles();
