# 학원 문제지 조교

사용자가 직접 과목·학교급·학년·교육과정·교재·출력 형식을 설정하는 문제지
제작 에이전트다. 특정 과목 지식은 기본 탑재하지 않는다. PDF 시험지를 추출해
HWP/PDF 카피본으로 만들고, 사용자가 승인한 교육과정 지식팩이 준비된 뒤에는
변형문제지와 정답·해설지도 제작한다.

## 1. 처음 채용한 뒤 반드시 할 일

처음 사용하는 사람은 먼저 **[처음사용하기.md](./처음사용하기.md)**를 연다.
핵심 흐름은 다음 네 단계다.

1. ZIP 압축을 푼다.
2. Codex에서 `폴더 열기`로 연결하거나, 해당 폴더에서 Claude Code를 연다.
3. 아래 문장을 그대로 입력한다.

   > 이 폴더의 설명서를 읽고 학원 문제지 조교로 시작해줘. 초기 설정을 개발자
   > 용어 없이 한 번에 한 질문씩 진행하고, 저장하기 전에 마지막에 요약해서
   > 확인받아줘.

4. 조교가 묻는 질문에 하나씩 답하고 마지막 요약을 확인한다.

조교가 다음 정보를 쉬운 말로 한 가지씩 묻는다.

- 사용할 과목
- 학교급과 기본 학년
- 기준 시험 연도
- 적용 교육과정 이름과 공식 자료 경로 또는 URL
- 교과서 출판사와 교재명
- 출력 형식(HWP, PDF)
- 학원별 레이아웃 선호

모르는 항목은 `잘 모르겠어`라고 답해도 된다. 조교가 미정으로 기록하고 필요한
시점에 다시 안내한다. 답변 요약을 사용자가 승인하면 `config/profile.json`,
`memory/USER.md`, `memory/PROJECT.md`에 저장한다.

명령어 방식을 원하는 고급 사용자는 `python setup.py`를 사용할 수 있지만,
일반 사용자는 실행할 필요가 없다.

## 2. 과목 지식 준비

교육과정 PDF, 교재 목차, 기존 시험지 자료는 `user-materials/` 폴더에 복사한다.
설정 직후 `knowledge_status`는 `pending`이다. 에이전트에게 다음처럼 요청한다.

> 초기 설정을 확인하고, 내가 제공한 교육과정 자료를 바탕으로 지식팩 적재를
> 시작해 줘.

에이전트는 공식 교육과정과 사용자가 제공한 교재 자료를
`knowledge/curriculum.json` 구조로 정리해 승인 후보를 보여준다. 사용자가
출처·단원·성취기준을 승인하기 전에는 `knowledge_status=ready`로 바꾸거나
변형문제를 만들 수 없다. 과목 이름만 보고 지식을 추정하지 않는다.

승인 후 다음 명령으로 스키마와 출처를 검증하고 설정을 활성화한다.

```powershell
python scripts/validate_knowledge.py --activate
```

## 3. 첫 문제지 작업

시험지 PDF를 `user-materials/` 폴더에 넣고 다음처럼 말한다.

> user-materials 폴더에 넣은 시험지 PDF로 카피 작업을 시작해줘. 필요한
> 프로그램이 없으면 내가 따라 할 수 있게 한 단계씩 알려줘.

에이전트가 현재 PC 상태를 확인한 뒤 필요한 설치와 작업 순서를 안내한다.

## 4. 설치 요구사항과 명령어 방식

- Windows
- Python 3.11+
- 한컴오피스 한글(HWP 출력 시)
- Python 패키지

```powershell
python -m pip install -r requirements.txt
```

필수 API 키는 없다. 판단은 이 폴더를 여는 Claude Code, Codex 등 호스트
에이전트가 담당하며 해당 모델 비용은 사용자 부담이다.

다음 명령은 직접 실행하고 싶은 고급 사용자를 위한 참고다.

## 5. 기본 작업 흐름

```powershell
python scripts/step1_extract.py --pdf "시험지.pdf" --slug 2026-example-midterm
python scripts/step2_split.py --slug 2026-example-midterm
python scripts/step2b_normalize.py --slug 2026-example-midterm --term "1학기 중간"
python scripts/step3_build_hwp.py --slug 2026-example-midterm --pdf
python scripts/step4_qa.py --slug 2026-example-midterm
```

이후 에이전트가 원본 PDF 렌더와 `work/<slug>/exam.json`을 대조하고 사용자의
카피 확인을 받는다. 변형문제는 교육과정·성취기준 태깅과 블라인드 독립 검수가
끝난 뒤 다음 게이트를 통과해야 한다.

```powershell
python scripts/validate_variants.py --slug 2026-example-midterm --output-gate
python scripts/step3_build_hwp.py --slug 2026-example-midterm --mode variant --pdf
python scripts/step5_build_answer.py --slug 2026-example-midterm --pdf
```

## 산출물

`output/<slug>/`에 다음 파일이 생성된다.

- `시험지_카피.hwp` 및 선택한 경우 PDF
- `변형문제지.hwp` 및 선택한 경우 PDF
- `정답및해설지.hwp` 및 선택한 경우 PDF

## 현재 지원 범위

- 입력: 텍스트 레이어가 있는 PDF
- 출력: HWP, PDF
- 과목: 사용자가 설정하지만 지식팩은 사용자가 자료를 제공하고 승인해야 함
- HWP 출력: Windows + 한컴오피스 필수

학교 기출문제와 교재에는 저작권이 있을 수 있다. 사용 권한을 확인하고 학원
내부 수업 목적 범위에서만 처리·배포한다.
