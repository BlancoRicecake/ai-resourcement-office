// Vercel Web Analytics 부트스트랩.
// 실제 집계 스크립트(/_vercel/insights/script.js)가 로드되기 전 큐를 준비한다.
// 쿠키를 사용하지 않으며, 데이터는 같은 도메인으로만 전송된다.
window.va =
  window.va ||
  function () {
    (window.vaq = window.vaq || []).push(arguments);
  };
