# 채용공고 기반 학습경로 추천 (버티컬 슬라이스)

채용공고의 기술 요구를 **근거 문장과 함께** 추출하고, 코드로 검증·집계한 뒤, 부족한 기술을 실제로 다루는 교육과정을 이유와 함께 추천합니다.

> 현재 데이터는 **합성 데이터**입니다(`data/fixtures`). 흐름 검증용이며 실제 채용시장 분석 결과로 발표하지 않습니다.

## 흐름

```
공고 ──► ① 추출 ──► ② 검증 ──► ③ 집계 ──► ④ 추천 ──► ⑤ 화면
        사전/Bedrock   코드        코드        코드       Streamlit
```

| 단계 | AI / 코드 | 결과 파일 (`outputs/latest`) |
|---|---|---|
| ① 추출: 기술·근거 문장·필수/우대 | 사전 기반(기본) 또는 Bedrock Claude | `claims.json` |
| ② 검증: 근거가 원문에 있는가, 기술이 그 문장에 있는가, 필수/우대가 원문과 맞는가 | 코드 | `claims.json`의 `status`, `review_queue.json` |
| ③ 집계: 직무별로 몇 건의 공고가 요구하는가 | 코드 (확인된 근거만) | `demand.json` |
| ④ 추천: 부족 기술 → 그 기술을 실제로 다루는 과정 | 코드 (이유 문장도 코드가 조립) | 화면 |

검증 상태는 세 가지입니다: **확인** / **불확실**(사전에 없는 기술, 판정 충돌) / **제외**(근거가 원문에 없음).
자세한 계약은 [docs/DESIGN.md](docs/DESIGN.md)를 참고하세요.

## 개발 방식 (하네스)

AI와 함께 개발하는 절차와 기록은 [harness/README.md](harness/README.md)를 따릅니다. 작업 규칙은 [AGENTS.md](AGENTS.md), 현재 상태는 [docs/progress.md](docs/progress.md)입니다. 완료 판단은 `python harness/check.py` 통과 + 작업지시서의 사용자 관점 완료 조건입니다. 옵시디언으로 볼 때는 [HOME.md](HOME.md)에서 시작하세요.

## 로컬 실행

```bash
pip install -r requirements.txt
python -m skillpath.pipeline          # AWS 호출 없음
python -m eval.evaluate               # 정답셋과 비교
streamlit run app.py                  # http://localhost:8501
python -m unittest discover -s tests -t .
```

Docker:

```bash
docker compose up --build             # http://localhost:8501
docker compose --profile tunnel up    # 외부 시연용 임시 URL (Cloudflare quick tunnel, 누구나 접속 가능)
```

## Bedrock 추출 (선택, 유료)

```bash
aws login                              # 또는 ~/.aws 프로필
USE_BEDROCK=true python -m skillpath.pipeline --extractor bedrock
```

- 모델 기본값: `anthropic.claude-opus-5-5`, 리전 `ap-northeast-2` (`.env`로 변경). 해당 계정·리전에서 모델 사용 가능 여부를 먼저 확인하세요.
- 같은 공고·모델·프롬프트 버전이면 `data/cache/bedrock`의 결과를 재사용하므로 다시 호출하지 않습니다.
- 모델 결과도 사전 기반 결과와 똑같이 ② 검증을 거칩니다.

## 지금 상태와 다음 단계

- [x] 합성 공고 8건·교육 7개로 ①~⑤ 연결
- [x] 하네스 0.1.0 (check.py, 실패·규칙·결정·작업지시서 노트), 테스트 31개
- [ ] **실제 공고 확보** (출처와 이용 범위 확인 후) → 사람이 만든 정답셋으로 사전 방식과 Bedrock 방식 비교
- [ ] 실제 교육과정 데이터 연결 (고용24 훈련과정 또는 AWS Skill Builder)
- [ ] 사전에 없는 기술(불확실) 처리: 임베딩 유사도로 후보만 제시하고 사람이 확정
- [ ] NCS 분류 연결
- [ ] AWS 배포 (S3·Lambda·Bedrock)

합성 데이터의 평가 점수는 사전과 정답을 같은 사람이 만들었으므로 정확도 근거가 아닙니다. 파이프라인이 끝까지 동작한다는 확인일 뿐입니다.
