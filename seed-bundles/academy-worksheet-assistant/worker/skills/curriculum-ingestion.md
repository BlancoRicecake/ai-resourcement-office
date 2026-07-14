# 교육과정·과목 지식 적재

## 원칙

과목 지식은 기본 탑재하지 않는다. 사용자가 제공한 공식 교육과정, 기관 자료,
교재 목차를 자기 언어로 구조화하며 원문 전체를 복제하지 않는다.

## 단계

1. 출처 목록을 먼저 제시한다: 제목, 기관/저자, 연도, 파일 경로 또는 URL.
2. 공식 교육과정과 교과서 배열, 실제 시험범위를 분리한다.
3. `knowledge/curriculum.example.json`을 기준으로 단원·성취기준을 구조화한다.
4. 누락·중복 코드, 출처 없는 항목, 과목·교육과정 불일치를 검사한다.
5. 사용자에게 출처·단원·성취기준 검토표를 보여준다.
6. 사용자가 승인한 뒤에만 `approval.status=approved`로 바꾸고
   `python scripts/validate_knowledge.py --activate`를 실행한다. 검증이 통과해야
   `config/profile.json`의 `knowledge_status=ready`가 된다.

출처를 확인할 수 없으면 `pending`을 유지한다. 모델의 기억만으로 official,
verified, approved 상태를 만들지 않는다.
