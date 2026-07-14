// 직원 카드에 "채용 N회" 뱃지 표시 — /api/downloads(Amplitude uniques 프록시)에서
// 디바이스 기준 1회로 중복 제거된 다운로드 수를 받아 그린다.
// counts가 null(키 미설정/조회 실패)이면 아무것도 그리지 않는다(오류 노출 없음).
(function () {
  fetch("/api/downloads")
    .then(function (response) { return response.json(); })
    .then(function (body) {
      if (!body || !body.counts) return;
      Object.keys(body.counts).forEach(function (slug) {
        var card = document.querySelector('.card[data-slug="' + slug + '"]');
        if (!card) return;
        var no = card.querySelector(".card-no");
        if (!no || card.querySelector(".hire-count")) return;
        var badge = document.createElement("span");
        badge.className = "hire-count";
        badge.textContent = "채용 " + body.counts[slug] + "회";
        no.insertAdjacentElement("beforebegin", badge);
      });
    })
    .catch(function () { /* 네트워크 실패 시 조용히 무시 */ });
})();
