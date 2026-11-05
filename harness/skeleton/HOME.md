---
type: index
---
# __PROJECT_NAME__

옵시디언에서 이 폴더를 볼트로 열었을 때의 시작 노트입니다.

## 지금
- 현재 상태: [[progress]]
- AI 작업 규칙: [[AGENTS]]
- 하네스 운영 방식: [[harness/README|하네스 README]]
- 원인 유형: [[failure_types]]

## 새 기록 만들기
1. `docs/failures`, `docs/rules`, `docs/decisions`, `work_orders` 중 맞는 폴더에 `F-001`처럼 ID를 제목으로 새 노트를 만든다.
2. 명령 팔레트(Ctrl+P) → "템플릿: 템플릿 삽입" → failure / rule / decision / work_order 선택.
3. 저장 후 `python harness/check.py`로 기록이 규칙에 맞는지 확인한다.

## 목록

> Dataview 커뮤니티 플러그인을 켜면 아래가 표로 보입니다. 없어도 하네스 동작에는 영향이 없습니다.

```dataview
TABLE status, verify
FROM "work_orders"
SORT id ASC
```

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

```dataview
TABLE status, date
FROM "docs/decisions"
SORT id ASC
```
