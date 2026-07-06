# -*- coding: utf-8 -*-
"""CSV 리뷰 분석 리포트 생성기 (미니 SaaS)

Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱.

실행:
    python app.py              # 웹 UI (http://127.0.0.1:8787)
    python app.py --cli 입력.csv [-o 리포트.md]   # CLI 모드

OPENAI_API_KEY가 없으면 키워드 기반 모의(mock) 모드로 동작한다.
"""

import csv
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8787"))
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
MAX_ROWS = int(os.environ.get("MAX_REVIEW_ROWS", "200"))
BUNDLE_ROOT = Path(__file__).resolve().parent.parent

REVIEW_COLUMN_NAMES = {
    "review", "reviews", "리뷰", "내용", "본문", "후기", "리뷰내용",
    "content", "text", "comment", "body", "message",
}

POSITIVE_KEYWORDS = [
    "좋", "만족", "최고", "빠르", "추천", "친절", "재구매", "감사", "훌륭",
    "맘에 들", "마음에 들", "괜찮", "튼튼", "정확",
]
NEGATIVE_KEYWORDS = [
    "불편", "늦", "아쉬", "별로", "최악", "느리", "불만", "환불", "고장",
    "파손", "실망", "누락", "불친절", "오배송", "하자", "찢어", "깨져",
]
TOPIC_KEYWORDS = {
    "배송": ["배송", "택배", "도착"],
    "포장": ["포장", "박스", "파손"],
    "품질": ["품질", "재질", "마감", "내구", "고장", "하자"],
    "가격": ["가격", "가성비", "비싸", "저렴"],
    "고객센터/응대": ["고객센터", "문의", "답변", "응대", "상담"],
    "사이즈/규격": ["사이즈", "크기", "규격", "핏"],
    "환불/교환": ["환불", "교환", "반품"],
    "사용성": ["사용", "설치", "조립", "앱", "사이트"],
}


def load_env_file():
    """번들 루트의 .env 파일을 읽어 비어 있는 환경변수만 채운다."""
    env_path = BUNDLE_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and not os.environ.get(key):
            os.environ[key] = value


def parse_reviews(csv_text):
    """CSV 텍스트에서 리뷰 컬럼을 찾아 리뷰 목록을 돌려준다."""
    csv_text = csv_text.lstrip("﻿").strip()
    if not csv_text:
        raise ValueError("CSV 내용이 비어 있습니다.")

    reader = csv.reader(io.StringIO(csv_text))
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        raise ValueError("CSV에서 데이터를 찾지 못했습니다.")

    header = [cell.strip().lower() for cell in rows[0]]
    review_idx = None
    for i, name in enumerate(header):
        if name in REVIEW_COLUMN_NAMES:
            review_idx = i
            break

    if review_idx is not None:
        data_rows = rows[1:]
    else:
        # 헤더에 리뷰 컬럼명이 없으면: 평균 텍스트 길이가 가장 긴 컬럼을 리뷰로 간주
        data_rows = rows[1:] if len(rows) > 1 else rows
        width = max(len(r) for r in data_rows)
        best_len = -1.0
        review_idx = 0
        for i in range(width):
            cells = [r[i] for r in data_rows if i < len(r) and r[i].strip()]
            texts = [c for c in cells if not re.fullmatch(r"[\d.\-/:\s]+", c)]
            avg = sum(len(c) for c in texts) / len(texts) if texts else 0
            if avg > best_len:
                best_len, review_idx = avg, i

    reviews = []
    for row in data_rows:
        if review_idx < len(row):
            text = row[review_idx].strip()
            if text:
                reviews.append(text)

    if not reviews:
        raise ValueError("리뷰 텍스트를 찾지 못했습니다. 'review' 또는 '리뷰' 컬럼이 있는지 확인하세요.")

    truncated = len(reviews) > MAX_ROWS
    return reviews[:MAX_ROWS], truncated


def estimate_tokens(text):
    """대략적인 토큰 수 추정 (한국어 기준 보수적으로 chars/2)."""
    return max(1, len(text) // 2)


def mock_analyze(reviews):
    """API 키 없이 동작하는 키워드 기반 분석."""
    sentiments = []
    topic_hits = {}
    for text in reviews:
        pos = sum(1 for k in POSITIVE_KEYWORDS if k in text)
        neg = sum(1 for k in NEGATIVE_KEYWORDS if k in text)
        if pos > neg:
            label = "긍정"
        elif neg > pos:
            label = "부정"
        else:
            label = "중립"
        sentiments.append(label)
        for topic, keys in TOPIC_KEYWORDS.items():
            if any(k in text for k in keys):
                bucket = topic_hits.setdefault(topic, {"긍정": 0, "부정": 0, "중립": 0})
                bucket[label] += 1

    counts = {s: sentiments.count(s) for s in ("긍정", "부정", "중립")}
    total = len(reviews)

    def topic_lines(label):
        pairs = sorted(
            ((t, h[label]) for t, h in topic_hits.items() if h[label] > 0),
            key=lambda p: -p[1],
        )
        return [f"- {t}: {n}건" for t, n in pairs[:5]] or ["- (해당 없음)"]

    lines = [
        "# 리뷰 분석 리포트",
        "",
        f"총 {total}건 리뷰 분석 (모의 모드: 키워드 기반 규칙 분석)",
        "",
        "## 감성 분포",
        "",
        f"- 긍정: {counts['긍정']}건 ({counts['긍정'] * 100 // total}%)",
        f"- 부정: {counts['부정']}건 ({counts['부정'] * 100 // total}%)",
        f"- 중립: {counts['중립']}건 ({counts['중립'] * 100 // total}%)",
        "",
        "## 부정 리뷰 주요 주제",
        "",
        *topic_lines("부정"),
        "",
        "## 긍정 리뷰 주요 주제",
        "",
        *topic_lines("긍정"),
        "",
        "## 참고",
        "",
        "- 이 리포트는 OPENAI_API_KEY 없이 실행된 모의(mock) 모드 결과입니다.",
        "- 키워드 규칙 기반이므로 짧거나 반어적인 리뷰는 오분류될 수 있습니다.",
        "- API 키를 설정하면 LLM 기반의 심층 분석 리포트가 생성됩니다.",
    ]
    return {"mode": "mock", "sentiments": sentiments, "report_markdown": "\n".join(lines)}


def llm_analyze(reviews, model, api_key, context=""):
    """OpenAI Chat Completions API로 리뷰를 분석한다 (stdlib urllib 사용)."""
    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(reviews))
    system_prompt = (
        "너는 고객 리뷰 분석을 담당하는 AI 직원이다. "
        "리뷰를 긍정/부정/중립으로 분류하고, 반복되는 불만/칭찬/개선 요청을 추출해 "
        "비즈니스 담당자가 바로 읽을 수 있는 한국어 Markdown 리포트를 작성한다. "
        "반드시 JSON 객체로만 응답한다."
    )
    user_prompt = (
        (f"제품/서비스 맥락: {context}\n\n" if context else "")
        + f"아래 {len(reviews)}개의 고객 리뷰를 분석하라.\n\n"
        + numbered
        + "\n\n다음 JSON 스키마로 응답하라:\n"
        + '{"sentiments": ["긍정"|"부정"|"중립", ...리뷰 순서대로], '
        + '"report_markdown": "# 리뷰 분석 리포트로 시작하는 Markdown 문서. '
        + '감성 분포, 주요 불만, 주요 칭찬, 개선 요청 우선순위, 3줄 요약을 포함"}'
    )
    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:500]
        if err.code == 401:
            raise RuntimeError("OpenAI API 키가 올바르지 않습니다 (401). .env의 OPENAI_API_KEY를 확인하세요.")
        if err.code == 429:
            raise RuntimeError("요청 한도 초과 또는 크레딧 부족입니다 (429). OpenAI 대시보드를 확인하세요.")
        raise RuntimeError(f"OpenAI API 오류 (HTTP {err.code}): {detail}")
    except urllib.error.URLError as err:
        raise RuntimeError(f"네트워크 오류: {err.reason}")

    content = body["choices"][0]["message"]["content"]
    usage = body.get("usage", {})
    try:
        parsed = json.loads(content)
        sentiments = parsed.get("sentiments", [])
        report = parsed.get("report_markdown", "")
    except (json.JSONDecodeError, AttributeError):
        sentiments, report = [], content

    # 모델이 리뷰 수보다 적거나 많게 분류한 경우 길이를 맞춘다
    sentiments = (list(sentiments) + ["중립"] * len(reviews))[: len(reviews)]
    return {
        "mode": "llm",
        "model": model,
        "sentiments": sentiments,
        "report_markdown": report or "(리포트 생성 실패: 모델 응답이 비어 있습니다)",
        "usage": usage,
    }


def analyze(csv_text, model=DEFAULT_MODEL, context=""):
    reviews, truncated = parse_reviews(csv_text)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    result = (
        llm_analyze(reviews, model, api_key, context) if api_key else mock_analyze(reviews)
    )
    result["reviews"] = reviews
    result["truncated"] = truncated
    result["row_limit"] = MAX_ROWS
    result["estimated_input_tokens"] = estimate_tokens("\n".join(reviews))
    return result


INDEX_HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>CSV 리뷰 분석 리포트 생성기</title>
<style>
  @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@700;900&display=swap");
  :root { color-scheme: light dark;
    --bg: #faf9f5; --surface: #ffffff; --ink: #1f1e1d; --muted: #6e6a63;
    --line: #e5e1d8; --accent: #c9603d; }
  @media (prefers-color-scheme: dark) { :root {
    --bg: #262624; --surface: #30302e; --ink: #f5f4ef; --muted: #aaa69d;
    --line: #43423e; --accent: #d97757; } }
  * { box-sizing: border-box; }
  body { font-family: 'Pretendard Variable', Pretendard, 'Segoe UI',
           'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
         background: var(--bg); color: var(--ink); max-width: 880px;
         margin: 0 auto; padding: 32px 16px 64px; line-height: 1.65; }
  .eyebrow { margin: 0; color: var(--accent); font-size: 0.78rem; font-weight: 800;
             letter-spacing: 1.4px; text-transform: uppercase; }
  h1 { font-family: 'Noto Serif KR', 'Apple SD Gothic Neo', serif;
       font-size: 1.65rem; font-weight: 900; letter-spacing: -0.3px; margin: 6px 0 12px; }
  h2 { font-size: 1.05rem; letter-spacing: -0.2px; }
  .card { border: 1px solid var(--line); border-radius: 16px; background: var(--surface);
          padding: 20px 24px; margin: 18px 0;
          box-shadow: 0 1px 2px rgba(31,30,29,.04), 0 8px 24px -12px rgba(31,30,29,.12); }
  textarea { width: 100%; min-height: 180px; font-family: Consolas, monospace;
             font-size: 0.85rem; border-radius: 10px; border: 1px solid var(--line);
             background: var(--bg); color: var(--ink); padding: 10px 12px; }
  input[type=text] { width: 100%; border-radius: 10px; border: 1px solid var(--line);
                     background: var(--bg); color: var(--ink); padding: 9px 12px;
                     font-family: inherit; font-size: 0.95rem; }
  label { font-weight: 700; display: block; margin: 14px 0 6px; }
  button { background: var(--accent); color: #fff; border: 0; border-radius: 999px;
           padding: 11px 26px; font-size: 0.98rem; font-weight: 700; cursor: pointer;
           font-family: inherit; }
  button:hover { filter: brightness(1.06); }
  button:disabled { opacity: 0.5; cursor: wait; }
  .muted { color: var(--muted); font-size: 0.85rem; }
  .badge { display: inline-block; padding: 3px 12px; border-radius: 999px;
           font-size: 0.8rem; font-weight: 700; }
  .badge.mock { background: #f0b35a33; color: #a16207; }
  .badge.llm { background: #5e736033; color: #4c7a52; }
  @media (prefers-color-scheme: dark) {
    .badge.mock { color: #f0b35a; } .badge.llm { color: #a3b8a4; } }
  table { border-collapse: collapse; width: 100%; font-size: 0.85rem; }
  th, td { border: 1px solid var(--line); padding: 6px 10px; text-align: left; }
  th { background: var(--bg); }
  pre { white-space: pre-wrap; background: var(--bg); border: 1px solid var(--line);
        padding: 16px; border-radius: 10px; }
  #error { color: #dc2626; font-weight: 600; }
</style>
</head>
<body>
<p class="eyebrow">AI력 사무소 · AI Resourcement Office</p>
<h1>CSV 리뷰 분석 리포트 생성기</h1>
<p class="muted">고객 리뷰 CSV를 붙여넣거나 업로드하면 감성 분류와 인사이트 리포트를 생성합니다.
모든 처리는 이 PC에서 실행되며, API 키가 설정된 경우에만 리뷰 텍스트가 OpenAI API로 전송됩니다.</p>

<div class="card">
  <label for="file">CSV 파일 업로드</label>
  <input type="file" id="file" accept=".csv,text/csv" />
  <label for="csv">또는 CSV 붙여넣기 (첫 행은 헤더, 리뷰 컬럼명: review / 리뷰 / 내용 등)</label>
  <textarea id="csv" placeholder="review&#10;&quot;배송이 빨라서 좋았어요&quot;&#10;&quot;포장이 아쉬웠습니다&quot;"></textarea>
  <label for="context">제품/서비스 맥락 (선택)</label>
  <input type="text" id="context" placeholder="예: 온라인 주방용품 쇼핑몰" />
  <p><button id="run">분석 시작</button> <span id="status" class="muted"></span></p>
  <p id="error"></p>
</div>

<div class="card" id="result" hidden>
  <p>실행 모드: <span id="mode" class="badge"></span> <span id="meta" class="muted"></span></p>
  <h2>리포트</h2>
  <pre id="report"></pre>
  <p><button id="download">report.md 다운로드</button></p>
  <h2>리뷰별 감성 분류</h2>
  <table><thead><tr><th>#</th><th>리뷰</th><th>감성</th></tr></thead><tbody id="rows"></tbody></table>
</div>

<script>
const $ = (id) => document.getElementById(id);
$("file").addEventListener("change", (e) => {
  const f = e.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = () => { $("csv").value = reader.result; };
  reader.readAsText(f, "utf-8");
});
$("run").addEventListener("click", async () => {
  $("error").textContent = "";
  $("result").hidden = true;
  $("run").disabled = true;
  $("status").textContent = "분석 중입니다...";
  try {
    const res = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ csv_text: $("csv").value, context: $("context").value }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "분석에 실패했습니다.");
    $("mode").textContent = data.mode === "llm" ? "LLM (" + data.model + ")" : "모의(mock)";
    $("mode").className = "badge " + data.mode;
    let meta = "리뷰 " + data.reviews.length + "건";
    if (data.truncated) meta += " (행 제한 " + data.row_limit + "건 적용)";
    if (data.usage && data.usage.total_tokens) meta += " · 사용 토큰 " + data.usage.total_tokens;
    $("meta").textContent = meta;
    $("report").textContent = data.report_markdown;
    const tbody = $("rows");
    tbody.innerHTML = "";
    data.reviews.forEach((text, i) => {
      const tr = document.createElement("tr");
      [i + 1, text, data.sentiments[i] || "-"].forEach((v) => {
        const td = document.createElement("td");
        td.textContent = v;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    $("result").hidden = false;
  } catch (err) {
    $("error").textContent = err.message;
  } finally {
    $("run").disabled = false;
    $("status").textContent = "";
  }
});
$("download").addEventListener("click", () => {
  const blob = new Blob([$("report").textContent], { type: "text/markdown" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "report.md";
  a.click();
  URL.revokeObjectURL(a.href);
});
</script>
</body>
</html>
"""


class AppHandler(BaseHTTPRequestHandler):
    def _send(self, status, content_type, body):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, "text/html", INDEX_HTML)
        else:
            self._send(404, "text/plain", "Not Found")

    def do_POST(self):
        if self.path != "/analyze":
            self._send(404, "application/json", '{"error": "Not Found"}')
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = analyze(
                payload.get("csv_text", ""),
                model=payload.get("model") or DEFAULT_MODEL,
                context=payload.get("context", ""),
            )
            self._send(200, "application/json", json.dumps(result, ensure_ascii=False))
        except (ValueError, RuntimeError) as err:
            self._send(400, "application/json", json.dumps({"error": str(err)}, ensure_ascii=False))
        except Exception as err:  # 예상 밖 오류도 사용자에게 보여준다
            self._send(500, "application/json", json.dumps({"error": f"서버 오류: {err}"}, ensure_ascii=False))

    def log_message(self, fmt, *args):
        sys.stderr.write("[app] %s\n" % (fmt % args))


def run_cli(argv):
    input_path = None
    output_path = None
    i = 0
    while i < len(argv):
        if argv[i] in ("-o", "--output"):
            i += 1
            output_path = argv[i]
        else:
            input_path = argv[i]
        i += 1
    if not input_path:
        print("사용법: python app.py --cli 입력.csv [-o 리포트.md]")
        return 2

    csv_text = Path(input_path).read_text(encoding="utf-8-sig")
    result = analyze(csv_text)
    mode = result.get("model") if result["mode"] == "llm" else "mock"
    print(f"[분석 완료] 리뷰 {len(result['reviews'])}건 / 모드: {mode}", file=sys.stderr)
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result["report_markdown"] + "\n", encoding="utf-8")
        print(f"[저장] {output_path}", file=sys.stderr)
    else:
        print(result["report_markdown"])
    return 0


def main():
    if sys.platform == "win32":
        # Windows 콘솔 코드페이지(cp949)에서 한국어 출력이 깨지지 않도록 강제
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
    load_env_file()
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        sys.exit(run_cli(sys.argv[2:]))

    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    url = f"http://{HOST}:{PORT}"
    key_state = "LLM 모드 (OPENAI_API_KEY 감지됨)" if os.environ.get("OPENAI_API_KEY") else "모의(mock) 모드 (API 키 없음)"
    print(f"CSV 리뷰 분석 리포트 생성기 실행 중: {url}")
    print(f"현재 상태: {key_state}")
    print("종료: Ctrl+C")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n종료합니다.")


if __name__ == "__main__":
    main()
