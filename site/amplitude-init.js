// Amplitude 초기화 (페이지당 1회) — CDN 로더 다음에 로드되어야 한다.
// 인라인 스크립트는 CSP(script-src 'self')에 막히므로 외부 파일로 분리했다.
// window.amplitude가 없으면(광고차단 등) 조용히 아무것도 하지 않는다.
if (window.amplitude) {
  if (window.sessionReplay) {
    window.amplitude.add(window.sessionReplay.plugin({ sampleRate: 1 }));
  }
  window.amplitude.init("0bbcd35d4f486ca5c80831ce586f36", {
    autocapture: true,
    fetchRemoteConfig: true,
  });
}
