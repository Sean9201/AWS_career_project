---
id: "{{title}}"
type: work_order
status: active
verify:
  - python harness/check.py
---
# 작업 제목

## 목표
사용자 관점에서 무엇이 가능해지는가.

## 범위
- 바꿀 파일·모듈

## 제외
- 이번에 하지 않을 것

## 완료 조건 (사용자 관점 문장 + 확인 방법)
- [ ] 예: 수요 표의 모든 부족 기술이 추천 섹션에 나온다 → `test_every_missing_skill_is_returned`

## 중단하고 보고할 조건
- 요구사항 충돌, 범위 변경 필요, 유료 호출·외부 수집 필요

## 미결 사항
- 사람이 정해야 할 것
