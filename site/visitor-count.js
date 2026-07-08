// 화면의 "누적 방문자 수"를 실제 값으로 채운다.
// 같은 브라우저 세션에서는 한 번만 +1 하고, 그 외에는 현재 총합만 읽어온다.
// /api/views 는 같은 도메인이므로 보안 설정(CSP)과 충돌하지 않는다.
(function () {
  var SESSION_KEY = "airo_counted";
  var counted = false;
  try {
    counted = sessionStorage.getItem(SESSION_KEY) === "1";
  } catch (e) {}

  fetch("/api/views", { method: counted ? "GET" : "POST" })
    .then(function (r) {
      return r.json();
    })
    .then(function (data) {
      if (!counted) {
        try {
          sessionStorage.setItem(SESSION_KEY, "1");
        } catch (e) {}
      }
      var el = document.getElementById("visitorCount");
      if (el && data && typeof data.count === "number") {
        el.textContent = data.count.toLocaleString("ko-KR");
      }
    })
    .catch(function () {
      // 저장소 미설정 등으로 실패하면 기존 숫자를 그대로 둔다.
    });
})();
