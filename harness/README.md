---
type: harness
---
# AI 개발 하네스 (공통 부분)

이 폴더 하나가 하네스 전체입니다. 버전은 [[CHANGELOG]] 맨 위 항목입니다. 필요한 것은 Python 3.11 이상뿐이고 추가 패키지는 없습니다.

## 설치

```bash
# 새 프로젝트나 기존 프로젝트에 설치 (이미 있는 파일은 덮어쓰지 않음)
python path/to/ai-harness/harness/init.py --root path/to/project --name "프로젝트 이름"

# harness/ 폴더가 이미 프로젝트 안에 있으면
python harness/init.py --name "프로젝트 이름"
```

설치 후 할 일: `AGENTS.md`에 목표와 고유 규칙 작성 → `harness.toml`에 프로젝트 테스트·평가 명령 추가 → `python harness/check.py`.

| 설치되는 것 | 출처 |
|---|---|
| `AGENTS.md`, `CLAUDE.md`, `HOME.md`, `harness.toml`, `docs/progress.md` | `skeleton/` |
| `.obsidian/app.json`, `.obsidian/templates.json` | `skeleton/.obsidian/` |
| `.github/workflows/harness.yml` (push·PR마다 check 실행) | `skeleton/.github/` |
| `docs/failures/`, `docs/rules/`, `docs/decisions/`, `work_orders/` | 빈 폴더 |
| `.gitignore` 항목 (`.env`, 옵시디언 개인 화면 상태 등) | 없는 줄만 추가 |

## 한 문장 원칙

**AI가 제안하고, 코드가 검증하고, 사람이 승인한다.** 서비스 안(추출 → 검증 → 불확실 검토), 개발 과정(구현 → check → 사용자 승인), 하네스 개선(규칙 후보 → 승격 조건 확인 → 승인)에 같은 구조를 씁니다.

## 파일 역할

| 위치 | 역할 | 쓰는 방식 |
|---|---|---|
| 프로젝트 `AGENTS.md` | AI가 항상 지킬 프로젝트 규칙 | 짧게 유지 |
| `docs/progress.md` | 지금 어디까지 했는가 | **덮어쓰기**, 40줄 이하 |
| `docs/decisions/D-*.md` | 결정과 이유 | 추가만 |
| `docs/failures/F-*.md` | 실패 → 원인 유형 → 회귀 테스트 | 추가만 |
| `docs/rules/R-*.md` | 프로젝트 규칙과 공통 규칙 후보 | 상태 변경 |
| `work_orders/WO-*.md` | 큰 작업 단위 지시서 | 작업마다 하나 |
| `harness/rules/R-*.md` | 승격된 공통 규칙 | 승격 절차로만 추가 |
| `harness/failure_types.md` | 원인 유형 목록 | 드물게 추가 |

세션 시작 시 읽는 순서: `AGENTS.md` → `docs/progress.md` → 진행 중 작업지시서. 나머지는 필요할 때 찾아봅니다.

## 개선 루프

1. 실패 발견: check 실패, 평가 수치 하락, **사용자 승인 거부**
2. `docs/failures/F-*.md` 작성 (템플릿: `templates/failure.md`). 원인 유형은 `failure_types.md`에서 고릅니다.
3. 프로젝트 안에서 가장 강한 수단으로 막습니다: **구조 > 자동 검사(테스트·check) > 규칙 문장**. 수정이 끝난 실패는 회귀 테스트 이름이 반드시 있어야 합니다.
4. 일반화할 수 있으면 `docs/rules/R-*.md`에 규칙 후보로 등록합니다.
5. 승격 조건을 모두 만족하면 `harness/rules/`로 옮기고 상태를 `promoted`로 바꿉니다.
6. 하네스 버전을 올리고 CHANGELOG에 기록합니다.

## 규칙 상태와 승격 조건

`candidate`(후보) → `trial`(프로젝트에서 시험 적용) → `promoted`(공통 규칙) → `retired`(폐기)

승격하려면 모두 필요합니다.

- 출처 실패가 2건 이상이거나 2개 이상 프로젝트에서 발생
- 강제 수단(`structure`/`check`/`test`)이 있거나, `text`뿐이면 그 이유를 적음
- 하네스를 쓰는 프로젝트들의 check 통과
- `approved_by`에 승인한 사람 기록

공통 규칙은 최대 20개입니다. 넘으면 합치거나 폐기한 뒤 추가합니다. 도입 후 같은 원인 유형이 재발하면 그 규칙은 효과가 없는 것이므로 더 강한 수단으로 바꿉니다.

## 실행

```bash
python harness/check.py            # 모든 검사 + metrics 기록
python harness/check.py --no-run   # 기록 문서 검사만 (테스트·평가 실행 생략)
python -m unittest discover -s harness/tests -t .   # 하네스 자체 테스트
```

## 하네스 업데이트

템플릿 저장소의 `harness/` 폴더로 프로젝트의 `harness/`를 교체합니다. 프로젝트 기록(`docs/`, `work_orders/`)과 `harness.toml`은 건드리지 않습니다. 교체 후 `python harness/check.py`가 통과하는지 확인하고 `harness.toml`의 `harness_version`을 올립니다.

## 옵시디언

1. 옵시디언에서 "폴더를 볼트로 열기"로 **프로젝트 폴더 자체**를 엽니다. 상위 폴더를 열면 다른 프로젝트의 `.env` 등이 볼트에 들어갑니다.
2. 설정 → 핵심 플러그인 → **템플릿**을 켭니다. 템플릿 폴더(`harness/templates`)는 설치 때 이미 지정돼 있습니다.
3. 새 기록: 해당 폴더에 `F-003`처럼 ID를 제목으로 노트 생성 → Ctrl+P → "템플릿 삽입". `{{title}}`이 ID로, `{{date}}`가 오늘 날짜로 채워집니다.
4. 선택: 커뮤니티 플러그인 **Dataview**를 켜면 `HOME.md`에 실패·규칙·결정·작업지시서 표가 보입니다.

노트의 프론트매터가 옵시디언 속성으로 보이고, `[[F-001]]` 같은 링크로 실패 → 규칙 → 결정이 그래프로 이어집니다. check.py도 같은 프론트매터를 읽습니다. 속성 편집기가 저장하는 형식(목록은 `- 항목`)을 그대로 읽을 수 있습니다.
