# -*- coding: utf-8 -*-
"""SEO/GEO 콘텐츠 브리프 생성기 (미니 SaaS)

Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱.

실행:
    python app.py              # 웹 UI (http://127.0.0.1:8788)
    python app.py --cli 입력.md [-o 브리프.md]   # CLI 모드

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
PORT = int(os.environ.get("PORT", "8788"))
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
BUNDLE_ROOT = Path(__file__).resolve().parent.parent

FIELD_ALIASES = {
    "keyword": ["keyword", "키워드"],
    "product": ["product", "제품", "제품 설명", "서비스"],
    "audience": ["audience", "타깃", "타겟", "타깃 고객", "대상"],
    "tone": ["tone", "톤", "문체"],
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
    """'Keyword: ...' / '키워드: ...' 형식의 입력 파일에서 필드를 추출한다."""
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
    keyword = (fields.get("keyword") or "").strip()
    if not keyword:
        raise ValueError("키워드는 필수입니다. (입력 파일에는 'Keyword: ...' 또는 '키워드: ...' 형식)")
    return {
        "keyword": keyword,
        "product": (fields.get("product") or "").strip(),
        "audience": (fields.get("audience") or "").strip(),
        "tone": (fields.get("tone") or "").strip(),
    }


def mock_generate(fields):
    """API 키 없이 동작하는 템플릿 기반 브리프 생성."""
    kw = fields["keyword"]
    product = fields["product"] or "(제품/서비스 설명 미입력)"
    audience = fields["audience"] or "일반 독자"
    meta = f"{kw}에 대해 알아야 할 핵심 정보를 정리했습니다. {product}"
    if len(meta) > 150:
        meta = meta[:147] + "..."

    lines = [
        f"# 콘텐츠 브리프: {kw}",
        "",
        "생성 모드: 모의(mock) — 템플릿 기반 골격. 항목별 내용은 직접 채우거나",
        "API 키 설정 후 재생성하세요.",
        "",
        "## 제목 후보",
        "",
        f"- {kw}란 무엇인가: 개념과 활용법 총정리",
        f"- {audience}를 위한 {kw} 시작 가이드",
        f"- {kw} 도입 전 반드시 확인할 것들",
        f"- {kw} vs 대안: 무엇을 선택해야 할까",
        f"- 실전 사례로 보는 {kw} 활용법",
        "",
        "## 콘텐츠 목차",
        "",
        f"1. {kw}의 정의와 배경",
        f"2. {audience}에게 {kw}가 필요한 이유",
        "3. 핵심 기능/구성 요소",
        "4. 시작하는 방법 (단계별)",
        "5. 흔한 실수와 주의사항",
        "6. 자주 묻는 질문",
        "7. 요약 및 다음 단계",
        "",
        "## FAQ 후보",
        "",
        f"- {kw}는 무엇인가요?",
        f"- {kw}를 시작하려면 무엇이 필요한가요?",
        "- 비용은 얼마나 드나요?",
        "- 초보자도 사용할 수 있나요?",
        f"- {kw}의 한계는 무엇인가요?",
        "",
        "## 메타 설명 (150자 이내)",
        "",
        f"{meta}",
        "",
        "## AI 검색(GEO) 대응 문장",
        "",
        "AI 답변 엔진이 인용하기 쉽도록 본문에 포함할 자기완결형 문장:",
        "",
        f"- {kw}는 [한 문장 정의]이다.",
        f"- {kw}의 주요 장점은 [장점 1], [장점 2], [장점 3]이다.",
        f"- {kw}는 {audience}에게 적합하다. 그 이유는 [근거]이다.",
        "",
        "## 참고",
        "",
        "- 검색량/경쟁도 데이터는 포함되지 않습니다. 외부 SEO 도구로 검증하세요.",
        "- 근거가 필요한 주장([...]로 표시)은 채우기 전에 사실 확인이 필요합니다.",
    ]
    return {"mode": "mock", "brief_markdown": "\n".join(lines)}


def llm_generate(fields, model, api_key):
    """OpenAI Chat Completions API로 브리프를 생성한다 (stdlib urllib 사용)."""
    system_prompt = (
        "너는 콘텐츠 브리프를 만드는 AI 마케팅 직원이다. "
        "검색 사용자와 AI 답변 엔진 사용자 모두가 이해하기 쉬운 구조를 만든다. "
        "실제 검색량, 순위, 경쟁도는 외부 도구 없이 단정하지 않는다. "
        "근거가 필요한 주장은 [확인 필요]로 표시한다. "
        "한국어 Markdown 문서로만 응답한다."
    )
    user_prompt = (
        f"키워드: {fields['keyword']}\n"
        + (f"제품/서비스: {fields['product']}\n" if fields["product"] else "")
        + (f"타깃 고객: {fields['audience']}\n" if fields["audience"] else "")
        + (f"톤: {fields['tone']}\n" if fields["tone"] else "")
        + "\n위 정보로 콘텐츠 브리프를 작성하라. 다음 섹션을 포함한다:\n"
        + "1. 제목 후보 5개\n2. 콘텐츠 목차 (H2/H3 구조)\n3. FAQ 5개 (답변 포함)\n"
        + "4. 메타 설명 (150자 이내)\n5. AI 검색(GEO) 대응 자기완결형 문장 3개\n"
        + "6. 콘텐츠 작성 시 주의사항\n\n"
        + "문서 제목은 '# 콘텐츠 브리프: <키워드>'로 시작한다."
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
        "brief_markdown": body["choices"][0]["message"]["content"],
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
<title>SEO/GEO 콘텐츠 브리프 생성기</title>
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
  input[type=text] { width: 100%; border-radius: 10px; border: 1px solid var(--line);
                     background: var(--bg); color: var(--ink); padding: 9px 12px;
                     font-family: inherit; font-size: 0.95rem; }
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
<h1>SEO/GEO 콘텐츠 브리프 생성기</h1>
<p class="muted">키워드와 제품 정보를 입력하면 제목 후보, 목차, FAQ, 메타 설명,
AI 검색(GEO) 대응 문장을 담은 브리프를 생성합니다. API 키가 설정된 경우에만
입력 내용이 OpenAI API로 전송됩니다.</p>

<div class="card">
  <label for="keyword">키워드 <small>(필수)</small></label>
  <input type="text" id="keyword" placeholder="예: AI 직원 패키지" />
  <label for="product">제품/서비스 설명 <small>(선택)</small></label>
  <input type="text" id="product" placeholder="예: 다운로드해서 직접 실행하는 AI 에이전트 세팅 패키지" />
  <label for="audience">타깃 고객 <small>(선택)</small></label>
  <input type="text" id="audience" placeholder="예: 개발자, 마케터, 소규모 사업자" />
  <label for="tone">톤 <small>(선택)</small></label>
  <input type="text" id="tone" placeholder="예: 전문적이지만 친근하게" />
  <p><button id="run">브리프 생성</button> <span id="status" class="muted"></span></p>
  <p id="error"></p>
</div>

<div class="card" id="result" hidden>
  <p>실행 모드: <span id="mode" class="badge"></span> <span id="meta" class="muted"></span></p>
  <pre id="brief"></pre>
  <p><button id="download">brief.md 다운로드</button></p>
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
        keyword: $("keyword").value,
        product: $("product").value,
        audience: $("audience").value,
        tone: $("tone").value,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "생성에 실패했습니다.");
    $("mode").textContent = data.mode === "llm" ? "LLM (" + data.model + ")" : "모의(mock)";
    $("mode").className = "badge " + data.mode;
    $("meta").textContent =
      data.usage && data.usage.total_tokens ? "사용 토큰 " + data.usage.total_tokens : "";
    $("brief").textContent = data.brief_markdown;
    $("result").hidden = false;
  } catch (err) {
    $("error").textContent = err.message;
  } finally {
    $("run").disabled = false;
    $("status").textContent = "";
  }
});
$("download").addEventListener("click", () => {
  const blob = new Blob([$("brief").textContent], { type: "text/markdown" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "brief.md";
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
        print("사용법: python app.py --cli 입력.md [-o 브리프.md]")
        return 2

    text = Path(input_path).read_text(encoding="utf-8-sig")
    result = generate(parse_input_file(text))
    mode = result.get("model") if result["mode"] == "llm" else "mock"
    print(f"[생성 완료] 키워드: {result['fields']['keyword']} / 모드: {mode}", file=sys.stderr)
    if output_path:
        Path(output_path).write_text(result["brief_markdown"] + "\n", encoding="utf-8")
        print(f"[저장] {output_path}", file=sys.stderr)
    else:
        print(result["brief_markdown"])
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
    print(f"SEO/GEO 콘텐츠 브리프 생성기 실행 중: {url}")
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
