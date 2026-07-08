# -*- coding: utf-8 -*-
"""유튜브 컨텐츠 원고 작성기 (미니 SaaS)

Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱.

실행:
    python app.py              # 웹 UI (http://127.0.0.1:8791)
    python app.py --cli 입력.md [-o 영상원고.md]   # CLI 모드

OPENAI_API_KEY가 없으면 무료 템플릿 모드로 동작한다.
"""

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
PORT = int(os.environ.get("PORT", "8791"))
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
BUNDLE_ROOT = Path(__file__).resolve().parent.parent

FORMATS = {
    "tutorial": {
        "label": "Tutorial",
        "sections": [
            ("Hook", "문제가 왜 중요한지 보여주고 오늘 얻을 결과를 약속한다."),
            ("Setup", "필요한 준비물, 전제 조건, 화면 구성을 짧게 설명한다."),
            ("Steps", "단계를 순서대로 보여주며 각 단계의 실수 포인트를 짚는다."),
            ("Recap", "완성 결과와 핵심 체크포인트를 정리한다."),
            ("CTA", "다음 행동을 자연스럽게 제안한다."),
        ],
    },
    "listicle": {
        "label": "Listicle",
        "sections": [
            ("Hook", "목록을 끝까지 봐야 하는 이유와 선택 기준을 제시한다."),
            ("Criteria", "추천 기준과 제외 기준을 설명한다."),
            ("Items", "각 항목을 문제, 장점, 사용 상황 순서로 보여준다."),
            ("Best Pick", "상황별 추천을 정리한다."),
            ("CTA", "시청자의 다음 행동을 제안한다."),
        ],
    },
    "opinion": {
        "label": "Opinion / Hot Take",
        "sections": [
            ("Hook", "논쟁적이지만 방어 가능한 관점을 제시한다."),
            ("Context", "왜 이 주제가 지금 중요한지 설명한다."),
            ("Argument", "핵심 주장과 근거를 2-3개로 나눈다."),
            ("Counterpoint", "반대 의견을 인정하고 선을 긋는다."),
            ("CTA", "댓글, 구독, 뉴스레터 등 참여를 유도한다."),
        ],
    },
    "case study": {
        "label": "Case Study",
        "sections": [
            ("Hook", "변화 전후 또는 핵심 결과를 먼저 보여준다."),
            ("Background", "상황, 제약, 목표를 설명한다."),
            ("Process", "무엇을 시도했고 왜 그렇게 했는지 설명한다."),
            ("Result", "결과와 배운 점을 정리한다."),
            ("CTA", "비슷한 문제를 가진 시청자의 다음 행동을 제안한다."),
        ],
    },
    "product demo": {
        "label": "Product Demo",
        "sections": [
            ("Hook", "제품이 해결하는 실제 문제를 보여준다."),
            ("Problem", "현재 방식의 불편함과 비용을 설명한다."),
            ("Demo", "핵심 기능을 실제 사용 순서대로 보여준다."),
            ("Use Case", "누가 언제 쓰면 좋은지 정리한다."),
            ("CTA", "체험, 다운로드, 상담 등 다음 행동을 제안한다."),
        ],
    },
}

FIELD_ALIASES = {
    "topic": ["topic", "video topic", "주제", "영상 주제", "아이디어"],
    "audience": ["audience", "target audience", "시청자", "타깃", "타겟"],
    "format": ["format", "video format", "형식", "포맷"],
    "output_mode": ["output mode", "mode", "출력 모드", "결과 형식"],
    "runtime": ["runtime", "length", "duration", "러닝타임", "길이"],
    "tone": ["tone", "voice", "말투", "톤"],
    "cta": ["cta", "call to action", "다음 행동"],
    "business_context": ["business context", "business", "브랜드", "비즈니스", "채널"],
    "notes": ["notes", "reference notes", "참고", "비고", "메모"],
}


def load_env_file():
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


def normalize_format(value):
    text = (value or "").strip().lower()
    if not text:
        return "tutorial"
    if "tutorial" in text or "튜토리얼" in text or "how" in text:
        return "tutorial"
    if "list" in text or "리스트" in text or "순위" in text:
        return "listicle"
    if "opinion" in text or "hot" in text or "의견" in text or "논평" in text:
        return "opinion"
    if "case" in text or "사례" in text:
        return "case study"
    if "demo" in text or "product" in text or "제품" in text or "시연" in text:
        return "product demo"
    return text if text in FORMATS else "tutorial"


def normalize_mode(value):
    text = (value or "").strip().lower()
    if "talk" in text or "point" in text or "토킹" in text or "outline" in text:
        return "Talking Points"
    return "Full Script"


def parse_input_file(text):
    fields = {}
    for line in text.splitlines():
        match = re.match(r"^\s*([A-Za-z가-힣 ]+?)\s*[:：]\s*(.+)$", line)
        if not match:
            continue
        label = match.group(1).strip().lower()
        value = match.group(2).strip()
        for field, aliases in FIELD_ALIASES.items():
            if label in aliases:
                fields[field] = value
    return fields


def validate_fields(fields):
    topic = (fields.get("topic") or "").strip()
    audience = (fields.get("audience") or "").strip()
    if not topic:
        raise ValueError("영상 주제는 필수입니다. (Topic: ... 또는 영상 주제: ...)")
    if not audience:
        raise ValueError("타깃 시청자는 필수입니다. (Audience: ... 또는 시청자: ...)")
    return {
        "topic": topic,
        "audience": audience,
        "format": normalize_format(fields.get("format")),
        "output_mode": normalize_mode(fields.get("output_mode")),
        "runtime": (fields.get("runtime") or "6 minutes").strip(),
        "tone": (fields.get("tone") or "친절하고 명확한 말투").strip(),
        "cta": (fields.get("cta") or "구독과 다음 영상 시청").strip(),
        "business_context": (fields.get("business_context") or "").strip(),
        "notes": (fields.get("notes") or "").strip(),
    }


def section_times(count, runtime):
    match = re.search(r"(\d+)", runtime or "")
    minutes = int(match.group(1)) if match else 6
    total_seconds = max(180, minutes * 60)
    weights = [0.1, 0.16, 0.48, 0.16, 0.1]
    if count != 5:
        weights = [1 / count] * count
    starts = []
    current = 0
    for weight in weights[:count]:
        duration = int(total_seconds * weight)
        starts.append((current, current + duration))
        current += duration
    starts[-1] = (starts[-1][0], total_seconds)
    return [f"{a // 60}:{a % 60:02d}-{b // 60}:{b % 60:02d}" for a, b in starts]


def make_hooks(fields):
    topic = fields["topic"]
    audience = fields["audience"]
    return [
        f'"{topic}"을 알고 싶지만 어디서 시작해야 할지 막막했다면, 이 영상에서 바로 쓸 수 있는 흐름을 보여드리겠습니다.',
        f"{audience}가 가장 자주 놓치는 지점을 먼저 짚고, 끝까지 따라오면 실행 가능한 형태로 정리해드리겠습니다.",
        f"오늘 영상은 이론보다 실제 적용에 초점을 맞춥니다. {topic}을 내 상황에 맞게 바꾸는 방법을 보겠습니다.",
    ]


def template_generate(fields):
    fmt = FORMATS[fields["format"]]
    times = section_times(len(fmt["sections"]), fields["runtime"])
    hooks = make_hooks(fields)
    mode_note = (
        "아래는 텔레프롬프터로 읽을 수 있는 완성 원고 초안입니다."
        if fields["output_mode"] == "Full Script"
        else "아래는 촬영자가 자연스럽게 말할 수 있도록 정리한 토킹포인트 초안입니다."
    )
    lines = [
        "# 유튜브 영상 원고 초안",
        "",
        "생성 모드: 무료 템플릿 모드",
        "",
        "## 제목 후보",
        "",
        f"1. {fields['topic']}, 처음 시작하는 사람을 위한 현실적인 가이드",
        f"2. {fields['audience']}를 위한 {fields['topic']} 실전 정리",
        f"3. {fields['topic']}을 더 쉽게 이해하는 방법",
        "",
        "## 영상 정보",
        "",
        f"- 포맷: {fmt['label']}",
        f"- 출력 모드: {fields['output_mode']}",
        f"- 예상 러닝타임: {fields['runtime']}",
        f"- 타깃 시청자: {fields['audience']}",
        f"- 톤: {fields['tone']}",
        f"- CTA: {fields['cta']}",
    ]
    if fields["business_context"]:
        lines.append(f"- 비즈니스 맥락: {fields['business_context']}")
    lines += ["", "## 후킹 후보", ""]
    lines += [f"- {hook}" for hook in hooks]
    lines += ["", "## 섹션별 구성", "", mode_note, ""]

    for idx, ((name, purpose), time_range) in enumerate(zip(fmt["sections"], times), start=1):
        lines += [
            f"### {time_range} {idx}. {name}",
            "",
            f"목적: {purpose}",
            "",
        ]
        if fields["output_mode"] == "Full Script":
            lines += [
                "말할 내용:",
                f"{fields['tone']}로 말합니다. {fields['topic']}을 다루면서 "
                f"{fields['audience']}가 바로 이해할 수 있는 예시를 넣습니다. "
                "확인되지 않은 수치나 사례는 [검증 필요]로 남겨둡니다.",
                "",
            ]
        else:
            lines += [
                "토킹포인트:",
                f"- {fields['topic']}과 연결되는 핵심 메시지 1개",
                f"- {fields['audience']}가 겪는 문제 또는 기대 효과",
                "- 화면에서 보여줄 예시 또는 데모 포인트",
                "",
            ]
        lines += [
            "화면/B-roll 큐:",
            "- 핵심 문장을 자막으로 강조",
            "- 설명 중인 화면, 자료, 제품, 예시를 클로즈업",
            "",
        ]

    lines += [
        "## CTA",
        "",
        f"{fields['cta']}로 자연스럽게 연결합니다. "
        "시청자가 다음에 무엇을 해야 하는지 한 문장으로 분명히 말합니다.",
        "",
        "## 촬영 전 체크리스트",
        "",
        "- 첫 15초 후킹이 분명한가",
        "- 화면 녹화나 B-roll 자료가 준비됐는가",
        "- 검증되지 않은 수치와 사례를 확인했는가",
        "- CTA 링크나 설명란 문구가 준비됐는가",
    ]
    if fields["notes"]:
        lines += ["", "## 참고 메모", "", fields["notes"]]
    return {"mode": "template", "script_markdown": "\n".join(lines)}


def llm_generate(fields, model, api_key):
    system_prompt = (
        "너는 유튜브 컨텐츠 작가다. "
        "영상 형식에 맞는 원고 구조, 후킹, 전환 문장, 섹션별 예상 시간, "
        "B-roll/화면 큐, CTA, 촬영 체크리스트를 포함한다. "
        "확인되지 않은 수치와 사례는 [검증 필요]로 표시한다. "
        "저작권 있는 대본이나 특정 크리에이터의 문장을 베끼지 않는다. "
        "한국어 Markdown으로만 응답한다."
    )
    user_prompt = (
        f"영상 주제: {fields['topic']}\n"
        f"타깃 시청자: {fields['audience']}\n"
        f"영상 형식: {FORMATS[fields['format']]['label']}\n"
        f"출력 모드: {fields['output_mode']}\n"
        f"러닝타임: {fields['runtime']}\n"
        f"톤: {fields['tone']}\n"
        f"CTA: {fields['cta']}\n"
        + (f"비즈니스 맥락: {fields['business_context']}\n" if fields["business_context"] else "")
        + (f"참고 메모: {fields['notes']}\n" if fields["notes"] else "")
        + "\n다음 섹션을 포함해 촬영 가능한 유튜브 영상 원고를 작성하라:\n"
        + "1. 제목 후보 3개\n2. 영상 정보\n3. 후킹 후보 3개\n"
        + "4. 섹션별 완성 원고 또는 토킹포인트\n5. B-roll/화면 큐\n"
        + "6. CTA\n7. 촬영 전 체크리스트\n"
    )
    payload = {
        "model": model,
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
    return {
        "mode": "llm",
        "model": model,
        "script_markdown": body["choices"][0]["message"]["content"],
        "usage": body.get("usage", {}),
    }


def generate(fields, model=DEFAULT_MODEL):
    fields = validate_fields(fields)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    result = llm_generate(fields, model, api_key) if api_key else template_generate(fields)
    result["fields"] = fields
    return result


INDEX_HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>유튜브 컨텐츠 원고 작성기</title>
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
         background: var(--bg); color: var(--ink); max-width: 920px;
         margin: 0 auto; padding: 32px 16px 64px; line-height: 1.65; }
  .eyebrow { margin: 0; color: var(--accent); font-size: 0.78rem; font-weight: 800;
             letter-spacing: 1.4px; text-transform: uppercase; }
  h1 { font-family: 'Noto Serif KR', 'Apple SD Gothic Neo', serif;
       font-size: 1.75rem; font-weight: 900; letter-spacing: 0; margin: 6px 0 12px; }
  .card { border: 1px solid var(--line); border-radius: 16px; background: var(--surface);
          padding: 20px 24px; margin: 18px 0;
          box-shadow: 0 1px 2px rgba(31,30,29,.04), 0 8px 24px -12px rgba(31,30,29,.12); }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  input, textarea, select { width: 100%; border-radius: 10px; border: 1px solid var(--line);
    background: var(--bg); color: var(--ink); padding: 9px 12px;
    font-family: inherit; font-size: 0.95rem; }
  textarea { min-height: 76px; }
  label { font-weight: 700; display: block; margin: 14px 0 6px; }
  label small { font-weight: 400; color: var(--muted); }
  button { background: var(--accent); color: #fff; border: 0; border-radius: 999px;
           padding: 11px 26px; font-size: 0.98rem; font-weight: 700; cursor: pointer;
           font-family: inherit; }
  button:hover { filter: brightness(1.06); }
  button:disabled { opacity: 0.5; cursor: wait; }
  .muted { color: var(--muted); font-size: 0.9rem; }
  .badge { display: inline-block; padding: 3px 12px; border-radius: 999px;
           font-size: 0.8rem; font-weight: 700; background: #5e736033; color: #4c7a52; }
  .badge.template { background: #f0b35a33; color: #a16207; }
  @media (prefers-color-scheme: dark) {
    .badge { color: #a3b8a4; } .badge.template { color: #f0b35a; } }
  pre { white-space: pre-wrap; background: var(--bg); border: 1px solid var(--line);
        padding: 16px; border-radius: 10px; }
  #error { color: #dc2626; font-weight: 600; }
  @media (max-width: 720px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<p class="eyebrow">AI력 사무소 · AI Resourcement Office</p>
<h1>유튜브 컨텐츠 원고 작성기</h1>
<p class="muted">영상 아이디어를 입력하면 형식에 맞는 원고, 섹션별 시간,
화면 큐, CTA를 생성합니다. API 키가 설정된 경우에만 입력 내용이 OpenAI API로 전송됩니다.</p>

<div class="card">
  <label for="topic">영상 주제 <small>(필수)</small></label>
  <textarea id="topic" placeholder="예: Notion으로 콘텐츠 캘린더를 관리하는 법"></textarea>
  <label for="audience">타깃 시청자 <small>(필수)</small></label>
  <input id="audience" placeholder="예: 1인 창업자와 마케팅 담당자" />
  <div class="grid">
    <div>
      <label for="format">영상 형식</label>
      <select id="format">
        <option>Product Demo</option>
        <option>Tutorial</option>
        <option>Listicle</option>
        <option>Opinion / Hot Take</option>
        <option>Case Study</option>
      </select>
    </div>
    <div>
      <label for="output_mode">출력 모드</label>
      <select id="output_mode">
        <option>Full Script</option>
        <option>Talking Points</option>
      </select>
    </div>
  </div>
  <div class="grid">
    <div>
      <label for="runtime">러닝타임</label>
      <input id="runtime" value="6 minutes" />
    </div>
    <div>
      <label for="cta">CTA</label>
      <input id="cta" placeholder="예: 무료 템플릿 다운로드" />
    </div>
  </div>
  <label for="tone">톤</label>
  <input id="tone" placeholder="예: 차분하고 실무적인 말투" />
  <label for="business_context">비즈니스 / 채널 맥락</label>
  <input id="business_context" placeholder="예: Notion 업무 템플릿을 판매하는 작은 스튜디오" />
  <label for="notes">참고 메모</label>
  <input id="notes" placeholder="예: 화면 녹화 큐와 B-roll 아이디어 포함" />
  <p><button id="run">원고 생성</button> <span id="status" class="muted"></span></p>
  <p id="error"></p>
</div>

<div class="card" id="result" hidden>
  <p>실행 모드: <span id="mode" class="badge"></span> <span id="meta" class="muted"></span></p>
  <pre id="script"></pre>
  <p><button id="download">youtube-content-draft.md 다운로드</button></p>
</div>

<script>
const $ = (id) => document.getElementById(id);
$("run").addEventListener("click", async () => {
  $("error").textContent = "";
  $("result").hidden = true;
  $("run").disabled = true;
  $("status").textContent = "생성 중입니다...";
  try {
    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: $("topic").value,
        audience: $("audience").value,
        format: $("format").value,
        output_mode: $("output_mode").value,
        runtime: $("runtime").value,
        tone: $("tone").value,
        cta: $("cta").value,
        business_context: $("business_context").value,
        notes: $("notes").value,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "생성에 실패했습니다.");
    $("mode").textContent = data.mode === "llm" ? "LLM (" + data.model + ")" : "무료 템플릿";
    $("mode").className = "badge " + data.mode;
    $("meta").textContent =
      data.usage && data.usage.total_tokens ? "사용 토큰 " + data.usage.total_tokens : "";
    $("script").textContent = data.script_markdown;
    $("result").hidden = false;
  } catch (err) {
    $("error").textContent = err.message;
  } finally {
    $("run").disabled = false;
    $("status").textContent = "";
  }
});
$("download").addEventListener("click", () => {
  const blob = new Blob([$("script").textContent], { type: "text/markdown" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "youtube-content-draft.md";
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
        if self.path != "/generate":
            self._send(404, "application/json", '{"error": "Not Found"}')
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = generate(payload, model=payload.get("model") or DEFAULT_MODEL)
            self._send(200, "application/json", json.dumps(result, ensure_ascii=False))
        except (ValueError, RuntimeError) as err:
            self._send(400, "application/json", json.dumps({"error": str(err)}, ensure_ascii=False))
        except Exception as err:
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
        print("사용법: python app.py --cli 입력.md [-o 영상원고.md]")
        return 2

    text = Path(input_path).read_text(encoding="utf-8-sig")
    result = generate(parse_input_file(text))
    mode = result.get("model") if result["mode"] == "llm" else "template"
    print(f"[생성 완료] 모드: {mode}", file=sys.stderr)
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result["script_markdown"] + "\n", encoding="utf-8")
        print(f"[저장] {output_path}", file=sys.stderr)
    else:
        print(result["script_markdown"])
    return 0


def main():
    if sys.platform == "win32":
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
    key_state = "LLM 모드 (OPENAI_API_KEY 감지됨)" if os.environ.get("OPENAI_API_KEY") else "무료 템플릿 모드 (API 키 없음)"
    print(f"유튜브 컨텐츠 원고 작성기 실행 중: {url}")
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
