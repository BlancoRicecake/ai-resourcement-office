# 문제지 제작 파이프라인

1. S1 추출: `step1_extract.py`
2. S2 분할: `step2_split.py`
3. S2 정규화: `step2b_normalize.py`
4. 원본 페이지 렌더와 문항별 대조
5. G1: 카피 검토표 사용자 확인
6. 정답 기입: 정답 자료 출처와 배점 교차검증
7. S3 카피: `step3_build_hwp.py --pdf`
8. S4 QA: `step4_qa.py`
9. G2: QA 리포트와 실제 HWP 사람 확인
10. 지식 ready 이후 문항 분석과 G3 확인
11. 변형·독립 검수·flag 판정
12. G5: `validate_variants.py --output-gate`
13. S8: 변형문제지와 정답·해설지 생성

텍스트 레이어가 없는 스캔 PDF, 복잡한 표, 수식 인식 실패는 자동으로 확정하지
않고 수동 교정 대상으로 표시한다.
