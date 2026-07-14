// 직원 카드 우측 상단 인덱스번호(.card-no, 예: W-01) 자리에 "채용 N회" 뱃지를 교체해 넣는다.
//
// 페이지/필터 전환에도 뱃지가 유지되도록:
//  - /api/downloads(Amplitude uniques dedup) 응답을 sessionStorage에 1시간 캐싱해
//    페이지를 옮겨다녀도 매번 재요청하지 않는다(엣지 캐시 s-maxage=3600과 정렬).
//  - app.js가 소속 필터 전환 시 #workerGrid를 innerHTML로 통째로 다시 그리면
//    뱃지가 날아가므로, MutationObserver로 그리드 재생성을 감지해 캐시값으로 다시 그린다.
//
// 채용 수가 있는 카드만 인덱스번호를 뱃지로 대체하고, 없는 카드는 W-01을 유지한다.
// counts가 null(키 미설정/조회 실패)이면 아무것도 그리지 않는다(오류 노출 없음).
(function () {
  var CACHE_KEY = "airo_hire_counts_v1";
  var TTL_MS = 60 * 60 * 1000; // 1시간 — 엣지 캐시(s-maxage=3600)와 정렬
  var counts = null;

  function readCache() {
    try {
      var raw = sessionStorage.getItem(CACHE_KEY);
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      if (!parsed || (Date.now() - parsed.at) > TTL_MS) return null;
      return parsed.counts;
    } catch (e) {
      return null;
    }
  }

  function writeCache(value) {
    try {
      sessionStorage.setItem(CACHE_KEY, JSON.stringify({ at: Date.now(), counts: value }));
    } catch (e) { /* 저장 실패(사생활 모드 등) 무시 */ }
  }

  function applyBadges() {
    if (!counts) return;
    Object.keys(counts).forEach(function (slug) {
      var card = document.querySelector('.card[data-slug="' + slug + '"]');
      if (!card || card.querySelector(".hire-count")) return; // 없거나 이미 적용됨
      var no = card.querySelector(".card-no");
      if (!no) return;
      var badge = document.createElement("span");
      badge.className = "hire-count";
      badge.textContent = "채용 " + counts[slug] + "회";
      no.replaceWith(badge);
    });
  }

  // #workerGrid는 필터 전환 때마다 innerHTML로 재생성된다 — 재생성될 때마다
  // 캐시된 값으로 뱃지를 다시 붙인다. (.card-no는 그리드의 직계 자식이 아니라
  // replaceWith가 childList 옵저버를 재트리거하지 않아 무한 루프가 없다.)
  function observeGrid() {
    var grid = document.querySelector("#workerGrid");
    if (!grid || typeof MutationObserver === "undefined") return;
    new MutationObserver(applyBadges).observe(grid, { childList: true });
  }

  function start() {
    applyBadges();
    observeGrid();
  }

  counts = readCache();
  if (counts) {
    start(); // 캐시 적중 — 재요청 없이 즉시 반영
    return;
  }

  fetch("/api/downloads")
    .then(function (response) { return response.json(); })
    .then(function (body) {
      if (!body || !body.counts) return;
      counts = body.counts;
      writeCache(counts);
      start();
    })
    .catch(function () { /* 네트워크 실패 시 조용히 무시 */ });
})();
