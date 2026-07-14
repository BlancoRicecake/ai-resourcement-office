// Amplitude 커스텀 이벤트 트래킹 — 핵심 퍼널 3종.
// worker_card_open(직원 상세 열람) → bundle_download(채용 zip, 핵심 전환), team_modal_open(팀 상세).
// app.js를 건드리지 않는 이벤트 위임 방식(캡처 단계)이라 카드/모달 마크업의 data-slug·data-hire에만 의존한다.
// window.amplitude가 없으면(광고차단 등) 조용히 아무것도 하지 않는다.
(function () {
  function track(name, props) {
    if (window.amplitude && typeof window.amplitude.track === "function") {
      window.amplitude.track(name, props);
    }
  }

  function findWorker(slug) {
    var data = window.AIRO_DATA;
    return data && data.workers ? data.workers.find(function (w) { return w.slug === slug; }) : null;
  }

  function isTeamSlug(slug) {
    var data = window.AIRO_DATA;
    return !!(data && data.teams && data.teams.some(function (t) { return t.slug === slug; }));
  }

  // zip 다운로드: href("./downloads/<slug>.zip")에서 slug를 파생 — 카드/모달 어느 위치의 버튼이든 동일 동작.
  function handleDownload(hire) {
    if (hire.hasAttribute("aria-disabled")) return; // "채용 준비 중" 비활성 버튼
    var href = hire.getAttribute("href") || "";
    var match = href.match(/downloads\/([^/]+)\.zip/);
    var slug = match ? match[1] : "unknown";
    track("bundle_download", { slug: slug, type: isTeamSlug(slug) ? "team" : "worker" });
  }

  function handleCardOpen(card) {
    var slug = card.getAttribute("data-slug");
    if (!slug) return;
    if (card.classList.contains("team-card")) {
      track("team_modal_open", { slug: slug });
    } else {
      var worker = findWorker(slug);
      track("worker_card_open", {
        slug: slug,
        name: worker ? worker.name : undefined,
        category: worker ? worker.category : undefined,
      });
    }
  }

  function handleActivate(event) {
    var target = event.target instanceof Element ? event.target : null;
    if (!target) return;
    var hire = target.closest("[data-hire]");
    if (hire) {
      handleDownload(hire); // 카드 내부의 채용 버튼 클릭은 다운로드로만 집계(카드 열람 중복 방지)
      return;
    }
    var card = target.closest(".card[data-slug]");
    if (card) handleCardOpen(card);
  }

  document.addEventListener("click", handleActivate, true);
  document.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === " ") {
      var target = event.target instanceof Element ? event.target : null;
      if (target && target.closest(".card[data-slug]")) handleActivate(event); // 키보드 사용자도 동일 집계
    }
  }, true);
})();
