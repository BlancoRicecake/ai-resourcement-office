// 직원별 채용(다운로드) 횟수 — Amplitude 조회 프록시 (Vercel Serverless Function)
//
// 브라우저는 Amplitude 조회 API를 직접 못 부른다(시크릿 키 인증 + CORS).
// 이 함수가 Event Segmentation API를 대신 호출해 slug별 "uniques"(디바이스
// 기준 1회 중복 제거된 다운로드 수)를 돌려준다. api/views.js와 같은
// zero-npm 패턴(표준 fetch만 사용).
//
// 필요한 환경변수(Vercel 프로젝트 설정에서 직접 등록):
//   AMPLITUDE_API_KEY     — Amplitude 프로젝트 API Key
//   AMPLITUDE_SECRET_KEY  — 같은 프로젝트의 Secret Key
//
// 동작:
//   GET /api/downloads -> { "counts": { "<slug>": <uniqueDevices>, ... } }
//   키 미설정/조회 실패 시 { "counts": null } — 화면은 뱃지를 그리지 않는다(오류 노출 없음).
//
// 캐시: 엣지에서 1시간(s-maxage). Amplitude 집계 반영이 수 분 지연될 수 있어
// 실시간성보다 안정성을 택했다.

const TRACKING_START = "20260713"; // bundle_download 이벤트 배포 시점

function yyyymmdd(date) {
  return date.toISOString().slice(0, 10).replace(/-/g, "");
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "s-maxage=3600, stale-while-revalidate=86400");
  res.setHeader("Content-Type", "application/json; charset=utf-8");

  const apiKey = process.env.AMPLITUDE_API_KEY;
  const secretKey = process.env.AMPLITUDE_SECRET_KEY;
  if (!apiKey || !secretKey) {
    res.status(200).json({ counts: null });
    return;
  }

  try {
    // slug 속성으로 group-by한 bundle_download의 uniques(=디바이스 단위 중복 제거).
    const eventDef = JSON.stringify({
      event_type: "bundle_download",
      group_by: [{ type: "event", value: "slug" }],
    });
    const params = new URLSearchParams({
      e: eventDef,
      m: "uniques",
      start: TRACKING_START,
      end: yyyymmdd(new Date()),
    });
    const auth = Buffer.from(`${apiKey}:${secretKey}`).toString("base64");
    const response = await fetch(
      `https://amplitude.com/api/2/events/segmentation?${params}`,
      { headers: { Authorization: `Basic ${auth}` } }
    );
    if (!response.ok) {
      res.status(200).json({ counts: null });
      return;
    }

    const body = await response.json();
    const data = body && body.data;
    if (!data || !Array.isArray(data.seriesLabels)) {
      res.status(200).json({ counts: null });
      return;
    }

    // seriesCollapsed = 기간 전체에서 중복 제거된 총 uniques(일자 버킷 합산이 아님).
    // 없으면(형식 변화 대비) 일자 시리즈 최댓값으로 보수적 폴백.
    const counts = {};
    data.seriesLabels.forEach(function (label, i) {
      const raw = Array.isArray(label) ? label.join(" ") : String(label);
      // 라벨 예: [0, "web-uiux-advisor"] / "slug = web-uiux-advisor" 등 — slug 토큰만 추출
      const match = raw.match(/([a-z0-9][a-z0-9-]*[a-z0-9])\s*$/i);
      if (!match) return;
      const slug = match[1];
      let value = null;
      if (Array.isArray(data.seriesCollapsed) && data.seriesCollapsed[i] && data.seriesCollapsed[i][0]) {
        value = data.seriesCollapsed[i][0].value;
      } else if (Array.isArray(data.series) && Array.isArray(data.series[i])) {
        value = Math.max.apply(null, data.series[i].concat([0]));
      }
      if (typeof value === "number" && isFinite(value)) {
        counts[slug] = value;
      }
    });

    res.status(200).json({ counts: counts });
  } catch (error) {
    res.status(200).json({ counts: null });
  }
};
