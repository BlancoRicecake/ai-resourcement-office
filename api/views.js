// 누적 방문자 수 카운터 (Vercel Serverless Function)
//
// 저장소로 Upstash Redis(REST API)를 사용한다. 외부 npm 패키지 없이
// 표준 fetch만 사용하므로 별도 설치가 필요 없다.
//
// 필요한 환경변수(Vercel에서 Upstash 연동 시 자동 주입됨):
//   KV_REST_API_URL / KV_REST_API_TOKEN
//   또는 UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN
//
// 동작:
//   POST /api/views  -> 방문 수 +1 후 현재 총합 반환 (새 방문자)
//   GET  /api/views  -> 증가 없이 현재 총합만 반환
//
// 저장소가 아직 연결되지 않았으면 count: null 을 돌려주고, 화면은
// 기존 숫자를 그대로 유지한다(오류 노출 없음).

// Upstash 연동 시 접두어(prefix)에 따라 변수 이름이 달라질 수 있으므로
// 이름 끝부분 패턴으로 자동 탐지한다. 예: KV_REST_API_URL,
// STORAGE_REST_API_URL, UPSTASH_REDIS_REST_URL 등 모두 인식.
// 쓰기 권한이 없는 READ_ONLY_TOKEN 은 자동으로 제외된다.
function findEnv(pattern) {
  const key = Object.keys(process.env).find((k) => pattern.test(k));
  return key ? process.env[key] : undefined;
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");

  const url =
    process.env.KV_REST_API_URL ||
    process.env.UPSTASH_REDIS_REST_URL ||
    findEnv(/REST_API_URL$/);
  const token =
    process.env.KV_REST_API_TOKEN ||
    process.env.UPSTASH_REDIS_REST_TOKEN ||
    findEnv(/(?<!READ_ONLY_)REST_API_TOKEN$/) ||
    findEnv(/REST_API_TOKEN$/);

  if (!url || !token) {
    res.status(200).json({ count: null, ready: false });
    return;
  }

  try {
    const command = req.method === "POST" ? "incr/visits" : "get/visits";
    const response = await fetch(`${url}/${command}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json();
    const count = Number(data.result) || 0;
    res.status(200).json({ count, ready: true });
  } catch (err) {
    res.status(200).json({ count: null, ready: false });
  }
};
