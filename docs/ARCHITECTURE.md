# 오케퐁(OKE-Pong) 전체 시스템 아키텍처

> 상태: 구현 전 설계 기준. Compose·서비스·연결선의 실제 기동·게시·시험은 담당자 구현 후 확인한다.

본 문서는 **프런트엔드(Next.js) · 백엔드(FastAPI) · 워크플로우(n8n 5종) · 저장소(PostgreSQL+pgvector & data-api)**의 전체 연결 구조와 네트워크·폴더 경계를 한눈에 보여주는 기준 구성도다. 세부 필드는 [API-CONTRACT.md](API-CONTRACT.md), 테이블 구조는 [DATA-AND-DB.md](DATA-AND-DB.md), 의사결정 배경은 [adr/ADR-001-project-decisions.md](adr/ADR-001-project-decisions.md)를 따른다.

---

## 1. 전체 계층 및 컨테이너 연결 구조

```mermaid
flowchart TB
    subgraph Client["브라우저 (사용자 / IT팀 관리자)"]
        Browser["Web Browser\n(http://localhost:3000 또는 VM 공개 주소)"]
    end

    subgraph Compose["Docker Compose 내부 네트워크 (develop/jihye/deploy/compose.yaml)"]
        subgraph FE["프런트엔드 계층 (수언님 · develop/sueon)"]
            NextJS["frontend (Next.js :3000)\n- 화면 렌더링 및 상태 표시\n- /api/* 서버 프록시 (BACKEND_ORIGIN)"]
        end

        subgraph BE["백엔드 · 인증 · 업무 저장 계층 (지혜님 · develop/jihye)"]
            FastAPI["backend (FastAPI :8000)\n- 세션 쿠키(oke_session) 인증·권한 확인\n- 웹 API (/api/*)\n- 내부 저장 API (/tickets, /alerts, /dlq)"]
        end

        subgraph WF["AI 워크플로우 계층 (n8n :5678)"]
            Support["oke-support (다혁님)\n문의 분류·보완질문·답변·검증·라우팅"]
            Search["oke-search (유빈님)\n권한 선필터 + pgvector 검색"]
            Index["oke-index (유빈님)\n규정 청킹·임베딩·재색인"]
            Handoff["oke-handoff (원민님)\n티켓 생성·알림·DLQ 수습"]
            Errors["oke-errors (원민님)\nError Trigger 최종 안전망"]
        end

        subgraph Storage["데이터 · 저장소 계층"]
            PG[("postgres (PostgreSQL + pgvector :5432)\n- app 스키마: employees, users, sessions,\n  inquiries, tickets, alerts, dlq\n- rag 스키마: documents, chunks(vector 3072)")]
            DataAPI["data-api (:8800)\n- 제공 직원 6명 (/employees)\n- 규정 8종 (/docs)\n- FAQ 6종 (/faq)\n- 기존 티켓 4건 (/tickets/{id})"]
        end
    end

    Browser -->|"/api/* (동일 출처 쿠키)"| NextJS
    NextJS -->|"BACKEND_ORIGIN\n(http://backend:8000)"| FastAPI
    FastAPI -->|"app.* 읽기/쓰기"| PG
    FastAPI -->|"POST /webhook/oke-support\n(X-Team-Key)"| Support

    Support -->|"직원·FAQ·기존티켓 조회"| DataAPI
    Support -->|"POST /webhook/oke-search"| Search
    Support -->|"POST /webhook/oke-handoff"| Handoff

    Index -->|"규정 원본 조회 (/docs)"| DataAPI
    Index -->|"청크·임베딩(3072) 저장"| PG
    Search -->|"access_level 선필터 + cosine 검색"| PG

    OpenAI["OpenAI API · Credential\nLLM / 임베딩"]
    Support -->|"분류·작성·검증"| OpenAI
    Index -->|"문서 임베딩"| OpenAI
    Search -->|"질의 임베딩"| OpenAI
    Support -.->|"부모 오류 설정"| Errors
    Index -.-> Errors
    Search -.-> Errors
    Handoff -.-> Errors
    Handoff -->|"app: /tickets, /alerts, /dlq · X-Api-Key"| FastAPI
    Handoff -->|"practice: /tickets, /alerts, /dlq · X-Api-Key"| DataAPI
    Errors -->|"app: 알림·DLQ"| FastAPI
    Errors -->|"practice: 알림·DLQ"| DataAPI
```

---

## 2. 핵심 네트워크 · 호출 불변식 (바이브 코딩 주의사항)

1. **브라우저 ↔ 백엔드 (CORS 및 내부 호스트명 문제 방지)**
   - 브라우저는 Docker 컨테이너 내부 이름(`http://backend:8000`, `http://n8n:5678`)을 알지 못한다.
   - 따라서 브라우저 코드는 항상 같은 출처의 `/api/...`만 호출하고, Next.js 서버가 `BACKEND_ORIGIN` 환경변수(로컬 개발 시 `http://127.0.0.1:8000`, Docker 실행 시 `http://backend:8000`)를 통해 FastAPI로 프록시한다.
   - 브라우저에서 DB, `n8n`, `data-api`를 직접 호출하거나 `NEXT_PUBLIC_*`에 내부 비밀키를 노출하지 않는다.

2. **컨테이너 기동 순서 및 영속 볼륨 (`compose.yaml`)**
   - `postgres` 컨테이너는 `pg_isready` 기반 `healthcheck`와 `named volume`을 사용한다.
   - `backend`는 `depends_on: postgres: { condition: service_healthy }` 설정으로 DB 준비 완료 후 기동한다.
   - `docker compose down -v`는 DB 및 n8n 볼륨 데이터를 모두 삭제하므로 일상 재시작 시 `-v` 옵션을 사용하지 않는다.

3. **단일 공통 진입점과 모드 분리 (`SERVICE_MODE`)**
   - 웹 요청(`FastAPI` → `oke-support`)과 공통 시험 스크립트(`flow.py` → `oke-support`)는 모두 동일한 `POST /webhook/oke-support` 계약을 사용한다.
   - `SERVICE_MODE=app`일 때는 FastAPI 내부 API(`/tickets`, `/alerts`, `/dlq`)를 통해 PostgreSQL(`app` 스키마)에 기록하고, `SERVICE_MODE=practice` 고장 주입 시험일 때는 제공 `data-api`를 사용한다.

---

## 3. 독립 제출본 폴더 구조

```text
Aio-4pj-1team/
├─ backend/       # FastAPI·DB 모델·마이그레이션·검증
├─ frontend/      # Next.js 직원·관리자 화면
├─ rag/           # 색인·검색 서비스·config·권한 매핑
├─ data-api/      # 제공 API 서버
├─ data/          # 가상 초기 JSON·schemas
├─ knowledge/     # 사내 규정 8종
├─ prompts/       # 제공 프롬프트 3종
├─ workflows/     # n8n 본체·색인·검색·이관·오류 5종
├─ cases/         # 공통·팀·RAG 시나리오와 합성 fixture
├─ requests/      # 시연·측정·오류 입력
├─ eval/          # 실서버 검사·오프라인 평가·Mock 회귀 검사
├─ runs/          # 실제 시험·측정 영수증
├─ deploy/        # VM·격리 로컬 Compose·Dockerfile·초기화
├─ .github/       # CI·PR 양식
└─ docs/          # 계약·설계·실행 결과
   ├─ daily/      # DAY80·81·82 기록
   └─ images/     # 화면·설계 그림
```

현재 실행·검증 경로는 [SUBMISSION](../SUBMISSION.md)을 따른다. 과거 개발 당시 경로는 일일 기록과 영수증의 이력이며 런타임 의존성이 아니다.
