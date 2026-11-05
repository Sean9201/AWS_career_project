---
type: progress
updated: 2026-11-05
active_work_order: WO-001
---
# 현재 상태

## 된 것
- 합성 공고 8건·교육 7개로 추출 → 검증 → 집계 → 추천 → Streamlit 화면 연결
- 하네스 0.2.0 적용: 실패 2건([[F-001]], [[F-002]]), 규칙 2건([[R-001]], [[R-002]]), 결정 3건
- 옵시디언 볼트 설정, GitHub Actions check 워크플로

## 지금 하는 것
- [[WO-001]] 실제 공고 데이터 연결 — 데이터 출처 결정 대기

## 막힌 것
- 실제 공고 출처 (사용자 결정)
- Docker 빌드 미확인 (Docker Desktop 꺼짐)
- Bedrock 미호출 (`aws login`, `anthropic` 패키지, 모델·리전 사용 가능 여부)

## 다음 후보
- 정렬 기준 결정 [[D-003]]
- Bedrock 추출과 사전 추출 비교 (실데이터 정답셋 이후)
