---
type: index
---
# 홈

옵시디언에서 이 폴더를 볼트로 열었을 때의 시작 노트입니다.

## 지금
- 현재 상태: [[progress]]
- 진행 중 작업: [[WO-001]]
- AI 작업 규칙: [[AGENTS]]

## 기록
- 실패: [[F-001]] · [[F-002]]
- 규칙: [[R-001]] (후보) · [[R-002]] (시험 적용)
- 결정: [[D-001]] · [[D-002]] · [[D-003]] (미정)

## 하네스
- 운영 방식: [[harness/README|하네스 README]]
- 원인 유형: [[failure_types]]
- 변경 이력: [[CHANGELOG]]
- 템플릿: `harness/templates/` (옵시디언 설정 → 템플릿 폴더로 지정)

## 제품
- 개요: [[README]]
- 설계 계약: [[DESIGN]]

> Dataview 플러그인을 설치하면 아래 블록이 표로 보입니다. 없으면 무시해도 됩니다.

```dataview
TABLE failure_type, status, regression_test, rule
FROM "docs/failures"
SORT id ASC
```

```dataview
TABLE status, enforcement, sources
FROM "docs/rules" OR "harness/rules"
SORT id ASC
```
