# -*- coding: utf-8 -*-
"""온라인 서비스 법률 문서 초안 생성기 (미니 SaaS)

Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱.
이용약관, 개인정보처리방침, 면책조항 초안을 서비스 상황에 맞게 생성한다.

⚠️ 이 도구는 법률 자문이 아니다. 생성물은 변호사 검토를 거쳐야 하는 초안이다.

실행:
    python app.py              # 웹 UI (http://127.0.0.1:8790)
    python app.py --cli 입력.md [-o 문서.md]   # CLI 모드

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
PORT = int(os.environ.get("PORT", "8790"))
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
BUNDLE_ROOT = Path(__file__).resolve().parent.parent

FIELD_ALIASES = {
    "service": ["service name", "service", "서비스명", "서비스 이름", "서비스"],
    "desc": ["description", "서비스 설명", "설명"],
    "operator": ["operator", "운영 주체", "운영자", "사업자 유형"],
    "payment": ["payment", "유료 여부", "결제", "요금"],
    "privacy_items": ["personal data", "개인정보", "수집 항목", "개인정보 수집 항목"],
    "contact": ["contact", "이메일", "연락처"],
    "docs": ["documents", "문서", "대상 문서"],
}

ALL_DOCS = ["이용약관", "개인정보처리방침", "면책조항"]

LEGAL_NOTICE = (
    "> ⚠️ **법적 고지**: 이 문서는 자동 생성된 초안이며 법률 자문이 아닙니다.\n"
    "> 실제 서비스에 게시하기 전에 반드시 변호사 등 전문가의 검토를 받으세요.\n"
    "> [대괄호] 항목은 서비스 실정에 맞게 직접 채워야 하며, 관련 법령의 최신\n"
    "> 개정 여부를 확인해야 합니다.\n"
)


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
    """'Service name: ...' / '서비스명: ...' 형식의 입력 파일에서 필드를 추출한다."""
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


def _is_paid(value):
    value = (value or "").lower()
    return any(k in value for k in ("유료", "결제", "구독", "paid", "yes", "예"))


def _collects_privacy(value):
    value = (value or "").strip().lower()
    return value not in ("", "없음", "미수집", "none", "no", "수집 안 함", "수집안함")


def validate_fields(fields):
    service = (fields.get("service") or "").strip()
    desc = (fields.get("desc") or "").strip()
    if not service:
        raise ValueError("서비스명은 필수입니다. (입력 파일에는 'Service name: ...' 또는 '서비스명: ...' 형식)")
    if not desc:
        raise ValueError("서비스 설명은 필수입니다. (입력 파일에는 'Description: ...' 또는 '서비스 설명: ...' 형식)")

    docs_raw = (fields.get("docs") or "").strip()
    if docs_raw:
        docs = [d.strip() for d in re.split(r"[,、·;]", docs_raw) if d.strip() in ALL_DOCS]
        if not docs:
            raise ValueError(f"대상 문서는 {', '.join(ALL_DOCS)} 중에서 선택하세요.")
    else:
        docs = list(ALL_DOCS)

    return {
        "service": service,
        "desc": desc,
        "operator": (fields.get("operator") or "[운영 주체: 개인/개인사업자/법인]").strip(),
        "payment": (fields.get("payment") or "무료").strip(),
        "privacy_items": (fields.get("privacy_items") or "없음").strip(),
        "contact": (fields.get("contact") or "[연락처 이메일]").strip(),
        "docs": docs,
    }


# ---------------------------------------------------------------------------
# 모의(mock) 모드: 한국 법령 구조를 따르는 템플릿 기반 초안
# ---------------------------------------------------------------------------

def _terms_of_service(f):
    paid = _is_paid(f["payment"])
    lines = [
        f"# {f['service']} 이용약관",
        "",
        "## 제1조 (목적)",
        "",
        f"이 약관은 운영자({f['operator']})가 제공하는 {f['service']}"
        f"(이하 \"서비스\")의 이용과 관련하여 운영자와 이용자의 권리, 의무 및",
        "책임사항, 기타 필요한 사항을 규정함을 목적으로 합니다.",
        "",
        "## 제2조 (정의)",
        "",
        "1. \"서비스\"란 아래 설명에 해당하는 서비스와 이에 부수하는 제반 기능을",
        "   말합니다.",
        f"   - {f['desc']}",
        "2. \"이용자\"란 이 약관에 따라 서비스를 이용하는 자를 말합니다.",
        "3. [서비스 특성에 맞는 추가 정의: 회원, 콘텐츠, 패키지 등]",
        "",
        "## 제3조 (약관의 명시, 효력 및 변경)",
        "",
        "1. 운영자는 이 약관의 내용을 이용자가 쉽게 알 수 있도록 서비스 화면에",
        "   게시합니다.",
        "2. 운영자는 약관의 규제에 관한 법률 등 관련 법령을 위배하지 않는 범위에서",
        "   이 약관을 개정할 수 있습니다.",
        "3. 약관을 개정할 경우 적용일자 및 개정사유를 명시하여 적용일자",
        "   [7일(이용자에게 불리한 변경은 30일)] 전부터 공지합니다.",
        "",
        "## 제4조 (서비스의 제공 및 변경)",
        "",
        "1. 운영자는 다음 서비스를 제공합니다.",
        f"   - {f['desc']}",
        "   - [기타 부수 서비스]",
        "2. 운영자는 운영상·기술상 필요에 따라 제공하는 서비스의 전부 또는 일부를",
        "   변경하거나 중단할 수 있으며, 이 경우 사전에 공지합니다.",
        "",
        "## 제5조 (서비스 이용)",
        "",
        "1. 서비스는 연중무휴, 1일 24시간 제공을 원칙으로 하되, 시스템 점검 등",
        "   운영상 필요한 경우 일시 중단될 수 있습니다.",
        "2. 서비스 이용에 필요한 인터넷 회선, 기기, 소프트웨어 실행 환경 및 그",
        "   비용은 이용자가 부담합니다.",
    ]
    if paid:
        lines += [
            "",
            "## 제6조 (유료 서비스, 결제 및 청약철회)",
            "",
            "1. 유료 서비스의 이용 요금, 결제 방법, 이용 기간은 해당 서비스 화면에",
            "   표시된 바에 따릅니다.",
            "2. 이용자는 전자상거래 등에서의 소비자보호에 관한 법률에 따라 결제일",
            "   또는 이용 가능일로부터 7일 이내에 청약철회를 할 수 있습니다. 다만,",
            "   디지털 콘텐츠의 제공이 개시된 경우 등 같은 법 제17조 제2항의",
            "   청약철회 제한 사유에 해당하면 청약철회가 제한될 수 있습니다.",
            "3. 환불의 방법과 절차: [환불 정책 상세 기재]",
        ]
    lines += [
        "",
        f"## 제{7 if paid else 6}조 (이용자의 의무)",
        "",
        "이용자는 다음 행위를 하여서는 안 됩니다.",
        "",
        "1. 서비스의 정상적인 운영을 방해하는 행위",
        "2. 타인의 지식재산권, 개인정보 등 권리를 침해하는 행위",
        "3. 관련 법령, 이 약관, 이용안내에서 금지한 행위",
        "4. [서비스 특성에 맞는 금지 행위 추가]",
        "",
        f"## 제{8 if paid else 7}조 (지식재산권)",
        "",
        "1. 서비스에 포함된 콘텐츠에 대한 저작권 등 지식재산권은 운영자 또는 해당",
        "   권리자에게 귀속됩니다.",
        "2. [오픈소스로 배포하는 자산이 있다면 적용 라이선스(MIT 등)와 허용 범위를",
        "   명시]",
        "",
        f"## 제{9 if paid else 8}조 (책임의 제한)",
        "",
        "1. 운영자는 천재지변, 이용자의 귀책사유 등 운영자의 고의 또는 과실이 없는",
        "   사유로 발생한 손해에 대해 책임을 지지 않습니다.",
        "2. 무료로 제공되는 서비스의 이용과 관련하여 관련 법령에 특별한 규정이",
        "   없는 한 운영자는 책임을 지지 않습니다.",
        "",
        f"## 제{10 if paid else 9}조 (준거법 및 재판관할)",
        "",
        "1. 이 약관은 대한민국 법령에 따라 해석됩니다.",
        "2. 서비스 이용과 관련하여 분쟁이 발생한 경우 민사소송법에 따른 관할",
        "   법원에 제소합니다.",
        "",
        "## 부칙",
        "",
        "이 약관은 [YYYY-MM-DD]부터 시행합니다.",
    ]
    return "\n".join(lines)


def _privacy_policy(f):
    collects = _collects_privacy(f["privacy_items"])
    head = [
        f"# {f['service']} 개인정보처리방침",
        "",
        f"운영자({f['operator']})는 개인정보 보호법 등 관련 법령을 준수하며,",
        "이용자의 개인정보를 보호하기 위해 다음과 같이 개인정보처리방침을 수립·공개합니다.",
        "",
    ]
    if not collects:
        body = [
            "## 1. 개인정보의 수집 여부",
            "",
            f"운영자는 {f['service']} 운영 과정에서 회원가입을 받지 않으며, 이용자의",
            "개인정보를 직접 수집·저장하지 않습니다.",
            "",
            "## 2. 인프라 사업자에 의한 자동 수집",
            "",
            "서비스는 [호스팅 사업자명: 예) GitHub Pages] 인프라를 통해 제공됩니다.",
            "해당 인프라 사업자는 서비스 제공 과정에서 접속 IP 주소, 브라우저 정보 등",
            "접속 기록을 자체 정책에 따라 수집할 수 있습니다. 자세한 내용은 해당",
            "사업자의 개인정보처리방침을 확인하세요: [인프라 사업자 방침 링크]",
            "",
            "## 3. 쿠키(Cookie) 사용 여부",
            "",
            "서비스는 자체적으로 쿠키를 사용하지 않습니다. [쿠키·로컬스토리지를",
            "사용하게 되면 사용 목적과 거부 방법을 기재]",
            "",
            "## 4. 이메일 문의 시 처리",
            "",
            f"이용자가 {f['contact']}로 문의하는 경우, 답변 목적으로 이메일 주소와",
            "문의 내용이 처리되며 문의 처리 완료 후 [보유 기간]이 지나면 지체 없이",
            "복구 불가능한 방법으로 파기합니다. 문의 이메일은 [접근 권한이 통제된",
            "계정]에서만 관리하는 등 안전성 확보에 필요한 조치를 적용합니다.",
            "",
            "## 5. 개인정보의 제3자 제공 및 처리위탁",
            "",
            "운영자는 이용자의 개인정보를 제3자에게 제공하거나 처리를 위탁하지",
            "않습니다. [위탁이 발생하면 수탁자와 위탁 업무를 표로 공개]",
            "",
            "## 6. 정보주체의 권리",
            "",
            "이용자는 언제든지 자신의 개인정보에 대한 열람, 정정, 삭제, 처리정지를",
            f"요구할 수 있습니다. 문의: {f['contact']}",
            "",
            "## 7. 개인정보 보호책임자",
            "",
            f"- 성명: [보호책임자 성명]",
            f"- 연락처: {f['contact']}",
            "",
            "## 8. 방침의 변경",
            "",
            "이 방침이 변경되는 경우 시행 [7]일 전부터 서비스 화면에 공지합니다.",
            "",
            "- 시행일: [YYYY-MM-DD]",
        ]
    else:
        body = [
            "## 1. 수집하는 개인정보 항목 및 수집 방법",
            "",
            f"- 수집 항목: {f['privacy_items']}",
            "- 수집 방법: [회원가입, 문의 양식, 서비스 이용 과정에서 자동 수집 등]",
            "",
            "## 2. 개인정보의 처리 목적",
            "",
            "- [서비스 제공 및 운영]",
            "- [문의 응대]",
            "- [수집 항목별 목적을 구체적으로 기재 — 목적 외 이용 금지]",
            "",
            "## 3. 개인정보의 보유 및 이용 기간",
            "",
            "- 원칙: 수집·이용 목적 달성 시 지체 없이 파기",
            "- 관련 법령에 따른 보존: [전자상거래법상 계약·결제 기록 5년, 소비자",
            "  불만·분쟁처리 기록 3년, 통신비밀보호법상 접속기록 3개월 등 해당",
            "  사항만 기재]",
            "",
            "## 4. 개인정보의 제3자 제공",
            "",
            "운영자는 이용자의 동의가 있거나 법령에 근거가 있는 경우를 제외하고",
            "개인정보를 제3자에게 제공하지 않습니다. [제공이 있다면 제공받는 자,",
            "목적, 항목, 보유 기간을 표로 기재]",
            "",
            "## 5. 개인정보 처리의 위탁",
            "",
            "- [수탁자명]: [위탁 업무 내용, 예: 클라우드 호스팅, 결제 처리]",
            "- 위탁계약 시 개인정보 보호 관련 법령 준수 사항을 규정합니다.",
            "",
            "## 6. 개인정보의 파기 절차 및 방법",
            "",
            "- 전자적 파일: 복구 불가능한 방법으로 영구 삭제",
            "- 종이 문서: 분쇄 또는 소각",
            "",
            "## 7. 정보주체와 법정대리인의 권리·의무 및 행사 방법",
            "",
            "이용자는 언제든지 개인정보 열람, 정정, 삭제, 처리정지 요구를 할 수",
            f"있으며, 운영자는 지체 없이 조치합니다. 문의: {f['contact']}",
            "",
            "## 8. 개인정보의 안전성 확보 조치",
            "",
            "- [접근 권한 관리, 암호화, 접속기록 보관 등 실제 적용 중인 조치 기재]",
            "",
            "## 9. 개인정보 보호책임자",
            "",
            "- 성명: [보호책임자 성명]",
            f"- 연락처: {f['contact']}",
            "",
            "## 10. 방침의 변경",
            "",
            "이 방침이 변경되는 경우 시행 [7]일 전부터 서비스 화면에 공지합니다.",
            "",
            "- 시행일: [YYYY-MM-DD]",
        ]
    return "\n".join(head + body)


def _disclaimer(f):
    return "\n".join([
        f"# {f['service']} 면책조항",
        "",
        "## 1. 정보 제공 목적",
        "",
        f"{f['service']}에서 제공하는 모든 콘텐츠와 자료는 정보 제공을 목적으로",
        "하며, 특정 결과를 보증하지 않습니다.",
        "",
        "## 2. 무보증 (AS-IS 제공)",
        "",
        "서비스와 배포 자료는 \"있는 그대로(AS-IS)\" 제공됩니다. 운영자는 자료의",
        "정확성, 완전성, 특정 목적 적합성에 대해 명시적·묵시적 보증을 하지",
        "않습니다.",
        "",
        "## 3. 이용자 책임",
        "",
        "1. 배포 자료의 실행, 설정, 비용(API·클라우드 요금 등), 데이터 보안,",
        "   결과물 검증은 이용자의 책임입니다.",
        "2. 자료 이용으로 발생한 직접·간접 손해에 대해 운영자는 관련 법령이",
        "   허용하는 최대 범위에서 책임을 지지 않습니다. 다만 운영자의 고의",
        "   또는 중대한 과실로 인한 손해는 그러하지 않습니다.",
        "",
        "## 4. 외부 링크 및 제3자 서비스",
        "",
        "서비스에 포함된 외부 링크와 제3자 서비스(API 제공자 등)는 운영자의",
        "통제 범위 밖에 있으며, 해당 서비스의 약관과 정책이 별도로 적용됩니다.",
        "",
        "## 5. 전문 자문 아님",
        "",
        "서비스가 제공하는 자동 생성 결과물(리포트, 문서 초안 등)은 법률, 세무,",
        "의료 등 전문 자문이 아니며, 중요한 의사결정 전에 해당 분야 전문가의",
        "검토를 받아야 합니다.",
    ])


def mock_generate(fields):
    """API 키 없이 동작하는 한국 법령 구조 기반 템플릿 초안."""
    builders = {
        "이용약관": _terms_of_service,
        "개인정보처리방침": _privacy_policy,
        "면책조항": _disclaimer,
    }
    parts = [LEGAL_NOTICE]
    parts.append(
        f"생성 모드: 모의(mock) — 대한민국 법령 구조 기반 템플릿. 생성 대상: "
        f"{', '.join(fields['docs'])}\n"
    )
    for doc in fields["docs"]:
        parts.append("\n---\n")
        parts.append(builders[doc](fields))
    return {"mode": "mock", "docs_markdown": "\n".join(parts)}


def llm_generate(fields, model, api_key):
    """OpenAI Chat Completions API로 법률 문서 초안을 생성한다 (stdlib urllib 사용)."""
    system_prompt = (
        "너는 한국 온라인 서비스의 법률 문서 초안을 작성하는 AI 직원이다. "
        "대한민국 법령(약관규제법, 개인정보 보호법, 전자상거래법 등)의 구조와 "
        "필수 기재사항을 따르는 초안을 작성한다. "
        "반드시 지킬 규칙: (1) 문서 최상단에 '법률 자문이 아니며 변호사 검토가 "
        "필요한 초안'임을 명시한다. (2) 확정할 수 없는 값은 [대괄호]로 표시한다. "
        "(3) 서비스 실정에 맞지 않는 조항을 만들어내지 않는다 (예: 무료 서비스에 "
        "결제 조항, 개인정보 미수집 서비스에 수집 조항). (4) 법령 개정 가능성을 "
        "언급하고 최신 법령 확인을 권고한다. 한국어 Markdown 문서로만 응답한다."
    )
    user_prompt = (
        f"서비스명: {fields['service']}\n"
        f"서비스 설명: {fields['desc']}\n"
        f"운영 주체: {fields['operator']}\n"
        f"유료 여부: {fields['payment']}\n"
        f"수집하는 개인정보: {fields['privacy_items']}\n"
        f"연락처: {fields['contact']}\n\n"
        f"위 서비스에 대해 다음 문서의 초안을 작성하라: {', '.join(fields['docs'])}\n"
        "각 문서는 '# <서비스명> <문서명>' 제목으로 시작하고, 문서 사이는 '---'로 "
        "구분한다. 개인정보처리방침은 개인정보 보호법 제30조의 필수 기재사항 "
        "구조를 따른다."
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

    content = body["choices"][0]["message"]["content"]
    # 초안 상단에 법적 고지가 없으면 강제로 붙인다
    if "법률 자문" not in content[:400]:
        content = LEGAL_NOTICE + "\n" + content
    return {
        "mode": "llm",
        "model": model,
        "docs_markdown": content,
        "usage": body.get("usage", {}),
    }


def generate(payload, model=DEFAULT_MODEL):
    fields = validate_fields(payload)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    result = llm_generate(fields, model, api_key) if api_key else mock_generate(fields)
    result["fields"] = fields
    return result


INDEX_HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>온라인 서비스 법률 문서 초안 생성기</title>
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
  .notice { border-left: 3px solid var(--accent); padding: 10px 14px;
            background: var(--bg); border-radius: 0 10px 10px 0; font-size: 0.88rem;
            color: var(--muted); }
  input[type=text], textarea, select { width: 100%; border-radius: 10px;
    border: 1px solid var(--line); background: var(--bg); color: var(--ink);
    padding: 9px 12px; font-family: inherit; font-size: 0.95rem; }
  textarea { min-height: 70px; }
  label { font-weight: 700; display: block; margin: 14px 0 6px; }
  label small { font-weight: 400; color: var(--muted); }
  .checks { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 6px; }
  .checks label { display: inline-flex; align-items: center; gap: 6px; margin: 0;
                  font-weight: 600; }
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
<h1>온라인 서비스 법률 문서 초안 생성기</h1>
<p class="notice">⚠️ 이 도구는 <strong>법률 자문이 아닙니다</strong>. 생성물은 초안이며,
실제 서비스에 게시하기 전에 반드시 변호사 등 전문가의 검토를 받아야 합니다.</p>
<p class="muted">서비스 정보를 입력하면 이용약관, 개인정보처리방침, 면책조항 초안을
상황에 맞게 생성합니다 (무료/유료, 개인정보 수집 여부에 따라 조항이 달라집니다).
API 키가 설정된 경우에만 입력 내용이 OpenAI API로 전송됩니다.</p>

<div class="card">
  <label for="service">서비스명 <small>(필수)</small></label>
  <input type="text" id="service" placeholder="예: AI력 사무소" />
  <label for="desc">서비스 설명 <small>(필수)</small></label>
  <textarea id="desc" placeholder="예: 다운로드형 AI 워커 패키지를 무료로 배포하는 웹 디렉토리"></textarea>
  <label for="operator">운영 주체 <small>(선택)</small></label>
  <select id="operator">
    <option value="">선택 안 함</option>
    <option>개인</option>
    <option>개인사업자</option>
    <option>법인</option>
  </select>
  <label for="payment">유료 여부 <small>(선택)</small></label>
  <select id="payment">
    <option>무료</option>
    <option>유료(결제 있음)</option>
  </select>
  <label for="privacy">수집하는 개인정보 항목 <small>(선택, 없으면 "없음")</small></label>
  <input type="text" id="privacy" placeholder="예: 이메일, 이름 / 수집하지 않으면 '없음'" />
  <label for="contact">연락처 이메일 <small>(선택)</small></label>
  <input type="text" id="contact" placeholder="예: contact@example.com" />
  <label>생성할 문서</label>
  <div class="checks">
    <label><input type="checkbox" class="doc" value="이용약관" checked /> 이용약관</label>
    <label><input type="checkbox" class="doc" value="개인정보처리방침" checked /> 개인정보처리방침</label>
    <label><input type="checkbox" class="doc" value="면책조항" checked /> 면책조항</label>
  </div>
  <p><button id="run">초안 생성</button> <span id="status" class="muted"></span></p>
  <p id="error"></p>
</div>

<div class="card" id="result" hidden>
  <p>실행 모드: <span id="mode" class="badge"></span> <span id="meta" class="muted"></span></p>
  <pre id="docs"></pre>
  <p><button id="download">legal-docs.md 다운로드</button></p>
</div>

<script>
const $ = (id) => document.getElementById(id);
$("run").addEventListener("click", async () => {
  $("error").textContent = "";
  $("result").hidden = true;
  $("run").disabled = true;
  $("status").textContent = "생성 중입니다...";
  try {
    const docs = Array.from(document.querySelectorAll(".doc:checked"))
      .map((c) => c.value).join(", ");
    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        service: $("service").value,
        desc: $("desc").value,
        operator: $("operator").value,
        payment: $("payment").value,
        privacy_items: $("privacy").value,
        contact: $("contact").value,
        docs: docs,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "생성에 실패했습니다.");
    $("mode").textContent = data.mode === "llm" ? "LLM (" + data.model + ")" : "모의(mock)";
    $("mode").className = "badge " + data.mode;
    $("meta").textContent =
      data.usage && data.usage.total_tokens ? "사용 토큰 " + data.usage.total_tokens : "";
    $("docs").textContent = data.docs_markdown;
    $("result").hidden = false;
  } catch (err) {
    $("error").textContent = err.message;
  } finally {
    $("run").disabled = false;
    $("status").textContent = "";
  }
});
$("download").addEventListener("click", () => {
  const blob = new Blob([$("docs").textContent], { type: "text/markdown" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "legal-docs.md";
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
        print("사용법: python app.py --cli 입력.md [-o 문서.md]")
        return 2

    text = Path(input_path).read_text(encoding="utf-8-sig")
    result = generate(parse_input_file(text))
    mode = result.get("model") if result["mode"] == "llm" else "mock"
    print(f"[생성 완료] 문서: {', '.join(result['fields']['docs'])} / 모드: {mode}", file=sys.stderr)
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result["docs_markdown"] + "\n", encoding="utf-8")
        print(f"[저장] {output_path}", file=sys.stderr)
    else:
        print(result["docs_markdown"])
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
    print(f"온라인 서비스 법률 문서 초안 생성기 실행 중: {url}")
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
