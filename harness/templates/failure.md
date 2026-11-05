---
id: "{{title}}"
type: failure
failure_type: silent-drop
status: open
found_by: check
found_at: "{{date}}"
work_order:
regression_test:
rule:
---
# 한 줄 제목

## 증상
무엇이 잘못 보였나. 누가 어떻게 발견했나 (check / 평가 / 사용자).

## 원인
왜 그렇게 됐나. 코드 위치. 원인 유형은 [[failure_types]]에서 고른다.

## 수정
무엇을 바꿨나.

## 재발 방지
- 회귀 테스트: `test_name` (status를 fixed로 바꾸려면 필수)
- 일반화할 수 있으면 규칙 후보: [[R-000]]
