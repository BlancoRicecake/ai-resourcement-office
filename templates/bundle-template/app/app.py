# -*- coding: utf-8 -*-
"""[번들 이름] (미니 SaaS) — 검증된 공통 골격

Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱 템플릿.
[대괄호]와 TODO를 채워서 사용하세요. 실제 예시는 seed-bundles/의 3개 번들 참고.

실행:
    python app.py              # 웹 UI (http://127.0.0.1:[포트])
    python app.py --cli 입력파일 [-o 출력파일]   # CLI 모드

OPENAI_API_KEY가 없으면 모의(mock) 모드로 동작한다.
"""

import json
import os
import sys
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"  # localhost 전용 바인딩 (외부 노출 금지)
PORT = int(os.environ.get("PORT", "8790"))  # TODO: 번들마다 고유 포트 (8787-8789 사용 중)
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
BUNDLE_ROOT = Path(__file__).resolve().parent.parent


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


def validate_input(payload):
    """TODO: 필수 입력을 검증하고 정규화한 dict를 돌려준다. 문제 시 ValueError."""
    raise NotImplementedError


def mock_generate(fields):
    """TODO: API 키 없이 동작하는 규칙/템플릿 기반 결과 생성.

    반환 형식: {"mode": "mock", "output_markdown": "..."}
    mock 결과 안에 'mock 모드 실행'임을 반드시 명시할 것.
    """
    raise NotImplementedError


def llm_generate(fields, model, api_key):
    """OpenAI Chat Completions API 호출 (stdlib urllib 사용)."""
    system_prompt = "[worker/agent.md의 역할·규칙을 요약해 넣는다]"
    user_prompt = "[fields를 조합해 작업 지시를 만든다]"
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
        "output_markdown": body["choices"][0]["message"]["content"],
        "usage": body.get("usage", {}),
    }


def generate(payload, model=DEFAULT_MODEL):
    fields = validate_input(payload)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    result = llm_generate(fields, model, api_key) if api_key else mock_generate(fields)
    result["fields"] = fields
    return result


INDEX_HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>[번들 이름]</title>
<!-- TODO: seed-bundles/의 스타일과 입력 폼/결과 렌더링 스크립트를 참고해 채운다 -->
</head>
<body>
<h1>[번들 이름]</h1>
<p>TODO: 입력 폼 → POST /generate → 결과 표시 + Markdown 다운로드</p>
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
        print("사용법: python app.py --cli 입력파일 [-o 출력파일]")
        return 2

    text = Path(input_path).read_text(encoding="utf-8-sig")
    result = generate({"raw": text})  # TODO: 입력 파일 파싱 방식에 맞게 수정
    mode = result.get("model") if result["mode"] == "llm" else "mock"
    print(f"[생성 완료] 모드: {mode}", file=sys.stderr)
    if output_path:
        Path(output_path).write_text(result["output_markdown"] + "\n", encoding="utf-8")
        print(f"[저장] {output_path}", file=sys.stderr)
    else:
        print(result["output_markdown"])
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
    print(f"[번들 이름] 실행 중: {url}")
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
