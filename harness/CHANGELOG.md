---
type: harness
---
# 하네스 변경 이력

## 0.2.0 — 2026-11-05
- `harness/` 폴더 하나로 완결: `init.py`가 `skeleton/`의 기본 파일(AGENTS.md, CLAUDE.md, HOME.md, harness.toml, progress.md, 옵시디언 설정)과 기록 폴더를 설치. 기존 파일은 덮어쓰지 않음
- 하네스 자체 테스트를 `harness/tests/`로 이동 (프로젝트 코드와 무관하게 실행)
- 노트 템플릿에 옵시디언 `{{title}}`, `{{date}}` 적용, `.obsidian/templates.json`으로 템플릿 폴더 연결
- 회귀 테스트 탐색에서 `.venv`, `node_modules` 등 제외
- GitHub Actions 워크플로(`.github/workflows/harness.yml`)를 기본 설치: push·PR마다 `check.py` 실행

## 0.1.0 — 2026-11-05
- 최초 구성: 파일 역할, 원인 유형 8개, 템플릿 4종, check.py (테스트·평가 실행, 실패↔회귀 테스트 연결, 규칙 상태·승격 조건, 원인 유형 재발 집계, progress 길이, 비밀값 패턴, metrics 기록)
- 첫 적용 프로젝트: 채용공고 기반 학습경로 추천 (황승현)
