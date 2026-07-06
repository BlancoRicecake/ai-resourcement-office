# -*- coding: utf-8 -*-
"""고객 요구사항 기반 제안서 초안 생성기 (미니 SaaS)

Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱.

실행:
    python app.py              # 웹 UI (http://127.0.0.1:8789)
    python app.py --cli 입력.md [-o 제안서.md]   # CLI 모드

OPENAI_API_KEY가 없으면 템플릿 기반 모의(mock) 모드로 동작한다.
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
PORT = int(os.environ.get("PORT", "8789"))
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
BUNDLE_ROOT = Path(__file__).resolve().parent.parent

FIELD_ALIASES = {
    "problem": ["client problem", "problem", "고객 문제", "문제", "요구사항"],
    "scope": ["service scope", "scope", "제공 서비스", "범위", "제안 범위"],
    "timeline": ["timeline", "일정", "기간"],
    "budget": ["budget", "예산", "견적"],
    "notes": ["notes", "reference notes", "참고", "비고"],
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


def parse_input_file(text):
    """'Client problem: ...' / '고객 문제: ...' 형식의 입력 파일에서 필드를 추출한다."""
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
    problem = (fields.get("problem") or "").strip()
    scope = (fields.get("scope") or "").strip()
    if not problem:
        raise ValueError("고객 문제는 필수입니다. (입력 파일에는 'Client problem: ...' 또는 '고객 문제: ...' 형식)")
    if not scope:
        raise ValueError("제공 서비스 범위는 필수입니다. (입력 파일에는 'Service scope: ...' 또는 '범위: ...' 형식)")
    return {
        "problem": problem,
        "scope": scope,
        "timeline": (fields.get("timeline") or "").strip(),
        "budget": (fields.get("budget") or "").strip(),
        "notes": (fields.get("notes") or "").strip(),
    }


def mock_generate(fields):
    """API 키 없이 동작하는 템플릿 기반 제안서 초안 생성."""
    scope_items = [s.strip() for s in re.split(r"[,、·;]", fields["scope"]) if s.strip()]
    scope_lines = [f"- {item}" for item in scope_items] or ["- (범위 미입력)"]
    timeline = fields["timeline"] or "[일정 협의 필요]"
    budget = fields["budget"] or "[견적 협의 필요]"

    lines = [
        "# 제안서 초안",
        "",
        "생성 모드: 모의(mock) — 템플릿 기반 골격. [대괄호] 항목은 직접 채우거나",
        "API 키 설정 후 재생성하세요.",
        "",
        "> ⚠️ 이 문서는 초안입니다. 가격, 일정, 계약 조건은 반드시 사람이",
        "> 검토·확정해야 합니다.",
        "",
        "## 1. 배경 및 문제 정의",
        "",
        f"{fields['problem']}",
        "",
        "## 2. 제안 목표",
        "",
        "- [문제 해결 후 달성할 정량 목표 1]",
        "- [정성 목표 1]",
        "",
        "## 3. 제안 범위",
        "",
        "### 포함",
        "",
        *scope_lines,
        "",
        "### 제외 (명시 권장)",
        "",
        "- [이번 계약에 포함되지 않는 작업 1]",
        "- [이번 계약에 포함되지 않는 작업 2]",
        "",
        "## 4. 산출물",
        "",
        *[f"- {item} 관련 산출물: [구체화 필요]" for item in scope_items[:3]],
        "",
        "## 5. 일정",
        "",
        f"- 전체 기간: {timeline}",
        "- 단계별 일정: [착수 → 구현 → 검수 → 인도 로 분해하여 작성]",
        "",
        "## 6. 견적 항목 초안",
        "",
        f"- 예산 기준: {budget}",
        "",
        "| 항목 | 내용 | 금액 |",
        "| --- | --- | --- |",
        *[f"| {item} | [상세] | [금액] |" for item in scope_items[:5]],
        "",
        "## 7. 전제 조건",
        "",
        "- 고객사가 제공해야 할 자료/접근 권한: [명시 필요]",
        "- 범위 변경 시 별도 협의",
        "",
        "## 8. 다음 단계",
        "",
        "1. 초안 검토 미팅",
        "2. 범위/일정/견적 확정",
        "3. 계약 및 착수",
    ]
    if fields["notes"]:
        lines += ["", "## 참고 사항", "", fields["notes"]]
    return {"mode": "mock", "proposal_markdown": "\n".join(lines)}


def llm_generate(fields, model, api_key):
    """OpenAI Chat Completions API로 제안서 초안을 생성한다 (stdlib urllib 사용)."""
    system_prompt = (
        "너는 B2B 제안서 초안을 만드는 AI 직원이다. "
        "고객의 문제와 요구사항을 정리하고, 제공 범위와 제외 범위를 구분하며, "
        "일정, 산출물, 견적 항목 초안을 만든다. "
        "법적 계약 문구를 확정하지 않는다. "
        "가격과 일정은 사용자가 검토해야 할 초안임을 문서 상단에 명시한다. "
        "한국어 Markdown 문서로만 응답한다."
    )
    user_prompt = (
        f"고객 문제: {fields['problem']}\n"
        f"제공 서비스 범위: {fields['scope']}\n"
        + (f"일정: {fields['timeline']}\n" if fields["timeline"] else "")
        + (f"예산: {fields['budget']}\n" if fields["budget"] else "")
        + (f"참고 사항: {fields['notes']}\n" if fields["notes"] else "")
        + "\n위 정보로 B2B 제안서 초안을 작성하라. 다음 섹션을 포함한다:\n"
        + "1. 배경 및 문제 정의\n2. 제안 목표\n3. 제안 범위 (포함/제외 구분)\n"
        + "4. 산출물\n5. 단계별 일정\n6. 견적 항목 초안 (표)\n"
        + "7. 전제 조건\n8. 다음 단계\n\n"
        + "문서 제목은 '# 제안서 초안'으로 시작하고, 확정할 수 없는 값은 [대괄호]로 표시한다."
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
        "proposal_markdown": body["choices"][0]["message"]["content"],
        "usage": body.get("usage", {}),
    }


def generate(fields, model=DEFAULT_MODEL):
    fields = validate_fields(fields)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    result = llm_generate(fields, model, api_key) if api_key else mock_generate(fields)
    result["fields"] = fields
    return result


INDEX_HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>제안서 초안 생성기</title>
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
  .card { border: 1px solid var(--line); border-radius: 16px; background: var(--surface);
          padding: 20px 24px; margin: 18px 0;
          box-shadow: 0 1px 2px rgba(31,30,29,.04), 0 8px 24px -12px rgba(31,30,29,.12); }
  input[type=text], textarea { width: 100%; border-radius: 10px; border: 1px solid var(--line);
    background: var(--bg); color: var(--ink); padding: 9px 12px;
    font-family: inherit; font-size: 0.95rem; }
  textarea { min-height: 70px; }
  label { font-weight: 700; display: block; margin: 14px 0 6px; }
  label small { font-weight: 400; color: var(--muted); }
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
  pre { white-space: pre-wrap; background: var(--bg); border: 1px solid var(--line);
        padding: 16px; border-radius: 10px; }
  #error { color: #dc2626; font-weight: 600; }
</style>
</head>
<body>
<p class="eyebrow">AI력 사무소 · AI Resourcement Office</p>
<h1>고객 요구사항 기반 제안서 초안 생성기</h1>
<p class="muted">고객 문제와 제공 서비스를 입력하면 목차, 범위, 일정, 견적 항목을 담은
제안서 초안을 생성합니다. 가격·일정·계약 조건은 반드시 사람이 검토해야 합니다.
API 키가 설정된 경우에만 입력 내용이 OpenAI API로 전송됩니다.</p>

<div class="card">
  <label for="problem">고객 문제 / 요구사항 <small>(필수)</small></label>
  <textarea id="problem" placeholder="예: 반복적인 고객 문의 응답 시간이 길다."></textarea>
  <label for="scope">제공 서비스 범위 <small>(필수, 쉼표로 구분)</small></label>
  <textarea id="scope" placeholder="예: FAQ 정리, 상담 분류 자동화, 관리자 검토 화면"></textarea>
  <label for="timeline">일정 <small>(선택)</small></label>
  <input type="text" id="timeline" placeholder="예: 2주 MVP" />
  <label for="budget">예산 <small>(선택)</small></label>
  <input type="text" id="budget" placeholder="예: 500만원 이내 / 견적 초안 필요" />
  <label for="notes">참고 사항 <small>(선택)</small></label>
  <input type="text" id="notes" placeholder="예: 기존 CS 툴은 채널톡 사용 중" />
  <p><button id="run">초안 생성</button> <span id="status" class="muted"></span></p>
  <p id="error"></p>
</div>

<div class="card" id="result" hidden>
  <p>실행 모드: <span id="mode" class="badge"></span> <span id="meta" class="muted"></span></p>
  <pre id="proposal"></pre>
  <p><button id="download">proposal.md 다운로드</button></p>
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
        problem: $("problem").value,
        scope: $("scope").value,
        timeline: $("timeline").value,
        budget: $("budget").value,
        notes: $("notes").value,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "생성에 실패했습니다.");
    $("mode").textContent = data.mode === "llm" ? "LLM (" + data.model + ")" : "모의(mock)";
    $("mode").className = "badge " + data.mode;
    $("meta").textContent =
      data.usage && data.usage.total_tokens ? "사용 토큰 " + data.usage.total_tokens : "";
    $("proposal").textContent = data.proposal_markdown;
    $("result").hidden = false;
  } catch (err) {
    $("error").textContent = err.message;
  } finally {
    $("run").disabled = false;
    $("status").textContent = "";
  }
});
$("download").addEventListener("click", () => {
  const blob = new Blob([$("proposal").textContent], { type: "text/markdown" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "proposal.md";
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
        print("사용법: python app.py --cli 입력.md [-o 제안서.md]")
        return 2

    text = Path(input_path).read_text(encoding="utf-8-sig")
    result = generate(parse_input_file(text))
    mode = result.get("model") if result["mode"] == "llm" else "mock"
    print(f"[생성 완료] 모드: {mode}", file=sys.stderr)
    if output_path:
        Path(output_path).write_text(result["proposal_markdown"] + "\n", encoding="utf-8")
        print(f"[저장] {output_path}", file=sys.stderr)
    else:
        print(result["proposal_markdown"])
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
    print(f"제안서 초안 생성기 실행 중: {url}")
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
