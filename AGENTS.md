# 작업 규칙

목표: 채용공고에 나타난 기술 수요를 근거 있는 학습 경로로 바꾸는 **개인 추천 서비스**. 시장 분석(수집 공고 기준 기술 요구 비율)은 추천의 근거로 쓴다. 대회 발표 2026-11-25. 목적과 맥락 원본: `docs/brief.md`.

## 세션 시작
1. 이 파일 → `docs/brief.md` → `docs/progress.md` → `docs/workflow.md` → 진행 중인 `work_orders/WO-*.md` 순서로 읽는다.
2. 작업 전 관련 코드를 검색해 이미 있는 기능인지 확인한다.
3. 새 작업을 시작하면 `docs/workflow.md`의 현재 단계와 상태를 갱신하고, 사용자에게 지금 워크플로의 어디에 있는지 시각적으로 먼저 보여준다.

## 반드시 지킬 것
- **AI가 제안하고, 코드가 검증하고, 사람이 승인한다.** 모델 출력은 원문 대조 없이 집계·추천에 쓰지 않는다.
- 결과 목록을 줄이면 생략 건수를 표시하거나 전체를 보여준다. ([[R-001]])
- 완료 보고 전 `python harness/check.py`를 실행하고 결과를 그대로 보고한다. 통과해도 작업지시서의 사용자 관점 완료 조건을 따로 확인한다. ([[R-002]])
- 합성 데이터 결과는 화면과 보고에 합성이라고 표시한다. 정확도 근거로 쓰지 않는다.
- Bedrock 호출·유료 AWS 리소스·외부 데이터 수집은 사용자 승인 후에만 한다.
- `.env`, 키, 토큰을 출력·문서화·커밋하지 않는다.
- `C:\All_Project\AWS_code\career-matching`은 수정하지 않는다.

## 실패가 생기면
`harness/templates/failure.md`로 `docs/failures/F-*.md`를 만들고, 수정했으면 회귀 테스트 이름을 적는다. 하네스 운영 방식은 `harness/README.md`.

## 명령
- 테스트: `python -m unittest discover -s tests -t .`
- 파이프라인: `python -m skillpath.pipeline`
- 평가: `python -m eval.evaluate`
- 전체 검사: `python harness/check.py`
