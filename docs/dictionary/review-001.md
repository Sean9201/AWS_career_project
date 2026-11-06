---
type: dictionary_review
id: review-001
status: approved
date: 2026-11-06
approved_at: 2026-11-07
approved_by: user
source: "Techmap 백엔드 29건: 제공자 태그 48개 + 본문 토큰(2건 이상) 37개"
---
# 사전 보강 1차 검토안

AI가 분류한 초안입니다. 승인된 항목만 `data/skills.json`에 반영합니다. 공고 수는 29건 중 등장한 공고 수입니다.

## A. 판단이 필요한 것 (기존 표준명에 합치거나, 포함 여부가 애매함)

| 후보 | 공고 | 제안 | 왜 판단이 필요한가 |
|---|---|---|---|
| Continuous Integration | 6 | **CI/CD의 별칭** + "지속적 통합" | 두 글자 "CI"는 디자인 공고의 CI(기업 이미지)와 충돌할 수 있어 IT 공고 한정 전제로만 추가 |
| GitHub / GitHUB | 2+2 | **Git의 별칭** | 플랫폼이지만 수요 집계에서는 Git 능력과 같은 뜻 |
| Spring Security, Spring Batch | 1, 1 | **Spring의 별칭** | Spring Boot처럼 하위 모듈. 세부 수요가 필요해지면 분리 |
| Amazon EKS / EKS | 2+2 | **새 표준명 "Amazon EKS"** (Kubernetes와 별도) | Kubernetes 별칭으로 합치면 "EKS 요구 = K8s 요구"가 되는데, 관리형 서비스 경험은 구별되는 요구라 분리 제안 |
| RDBMS / RDB | 5+2 | **새 표준명 "RDBMS"** (관계형 데이터베이스) | 특정 제품이 아니라 범주. "RDBMS 경험" 자체가 요구로 자주 등장해 집계 가치 있음 |
| Artificial Intelligence | 4 | 제외 | 너무 일반적. 대신 딥러닝·LLM·TensorFlow 같은 구체 항목만 넣음 |
| Internet of Things / IoT | 4+4 | 제외 (도메인) | 기술이 아니라 산업 분야. 나중에 "도메인" 축을 따로 만들면 그때 사용 |
| Jira, Confluence, Notion | 2, 1, 2 | **새 표준명, category "tool"** | 개발 기술이 아니라 협업 도구. 넣되 화면에서 구분 표시 |
| MCP | 2 | 보류 | Model Context Protocol인지 다른 뜻인지 원문 확인 전 |

## B. 새 표준명으로 추가 (기존 집계에 영향 없음)

| 분류 | 표준명 (별칭) | 공고 |
|---|---|---|
| database | MariaDB | 5 |
| database | Oracle DB (Oracle, 오라클) | 3 |
| database | MS SQL Server (MSSQL, Microsoft SQL Server, SQL Server) | 2+1 |
| database | MongoDB | 2 |
| database | OpenSearch | 2 |
| database | NoSQL (NoSQL database management system) | 2 |
| database | PL/SQL (PL / SQL) | 1 |
| framework | MyBatis | 2 |
| framework | QueryDSL | 2 |
| framework | Next.js | 2 |
| framework | Express.js (별칭에 "Express" 단독은 넣지 않음: 영어 단어와 충돌) | 2 |
| framework | NestJS | 1 |
| framework | Vue (Vue.js, 뷰) | 1 |
| api | gRPC | 2 |
| architecture | MSA (Microservices, 마이크로서비스) | 5 |
| devops | Jenkins | 2 |
| devops | Prometheus | 1 |
| devops | TDD (Test Driven Development) | 1 |
| protocol | MQTT | 2 |
| ai | LLM (대규모 언어 모델) | 2 |
| ai | 딥러닝 (Deep Learning) | 1 |
| ai | TensorFlow | 1 |
| language | PHP | 1 |
| language | C++ | 1 |
| language | Rust | 1 |
| language | HTML | 1 |
| mobile | Android (안드로이드) | 1 |

## C. 제외 (사전에 넣지 않고, 다시 후보로 뜨지 않게 `_ignore`에 기록)

- 성향·태도: 성실성, 협동심, 적응성, 꼼꼼함, 계획성, 성장지향성, 창의성, 윤리의식
- 너무 일반적이거나 직무·범주 단어: process data, use databases, algorithms, operating systems, system design, computer science, CS, Structured-data, operations management, Customer Relationship Management, control systems, design hardware, semiconductors, Windows 10, JSON, Backend, Back end, Frontend, Cloud, Infra, Infrastructure, Architecture, Engineering, Engineer, Tools, Stack, Model, Culture, Why, Us
- 뜻이 불분명한 단독 단어: Batch (Spring Batch는 A에서 처리)

## 승인 결과 (2026-11-07)

사용자가 A~C를 그대로 승인했다. 초안과 다르게 반영한 것:
- **MCP**: 원문 확인 결과 "MCP(Model Context Protocol) 서버·클라이언트를 직접 구현해본 경험"(요구 사항으로 명시) → 표준명 "MCP", 분류 ai, 별칭 "Model Context Protocol"로 추가. 다른 1건은 본문 없는 공고의 태그였다.
- **Vue의 한글 별칭 "뷰"는 넣지 않음**: 한글은 경계 검사가 없어 "리뷰", "인터뷰" 안의 "뷰"에 붙는다. 두 글자 한글 별칭은 앞으로도 넣지 않는다(사전 `_comment`에 기록).
- 철자 변형만 추가: LLM에 "Large Language Model", TDD에 "Test-Driven Development".
- 제외(A의 Artificial Intelligence·IoT, C 전체 41개)는 `skills.json`의 `_ignore`에 넣어 후보로 다시 뜨지 않는다.

## 반영 전후 비교 (실제 공고 29건, 본문 있는 22건 기준)

| 항목 | v1 (2026-11-06) | v2 (2026-11-07) |
|---|---|---|
| 표준명 수 | 29 | 62 |
| 확인된 근거(claim) | 210 | 295 |
| 수요 표 행 | 25 | 57 |
| 사전 후보 큐 | 30개 표시 (한도) | 0개 (제외 25, 1건짜리 1 — 숨긴 수를 화면에 표시) |

기존 행 중 숫자가 바뀐 것은 둘뿐이다.
- Git 언급 6 → 7: GitHub 별칭.
- **JavaScript 우대 3 → 1, 언급 6 → 3**: 늘어난 게 아니라 **오탐이 빠졌다**. "Vue.js"의 ".js"가 JS 별칭에 붙어 JavaScript로 세고 있었다. [[F-009]]로 기록하고 경계 규칙을 고쳤다.
- CI/CD는 변화 없음: "Continuous Integration" 6건은 제공자 태그였고 본문 문장에는 없었다(태그는 근거로 쓰지 않음). Spring도 변화 없음(Spring Security·Batch 공고는 이미 Spring을 언급).

새로 집계된 행 중 필수 1건 이상 (필수/우대/언급): RDBMS 5/0/10, MariaDB 3/0/5, Oracle DB 1/1/3, Vue 1/1/3, Amazon EKS 1/0/2, MS SQL Server 1/0/2, NoSQL 1/0/2, gRPC 1/1/2, NestJS 1/0/1. 우대만: MSA 0/3/6, Jira·LLM·MQTT·MyBatis·Next.js·Notion·OpenSearch 각 우대 1. 나머지 16개는 언급 1~2건.

합성 정답셋 변경: syn-b1 문장 "MySQL 등 RDBMS 설계 및 쿼리 작성 경험"이 필수 섹션에 있어 gold에 RDBMS를 추가했다(사전 v1 때는 RDBMS가 없어 빠져 있었음). 실제 공고 정답셋이 생기면 사전 v1과 v2의 재현율을 같은 정답셋에서 비교한다.
