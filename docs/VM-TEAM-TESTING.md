# 팀 VM 사용·시험 안내 · 2026-11-06 11:55 KST 갱신

이 문서는 현재 확인된 팀 VM 접속점과 시험 전 인계사항을 안내한다. 안내는 VM 배포나 서비스 변경을 허가하지 않는다.

## 접속 위치

| 대상 | 주소/경로 | 의미 |
|---|---|---|
| 직원 FE | <https://aio-t1.isitsoft.kr/login> | 공개 로그인 페이지. 로그인 페이지가 열리는 것과 계정 로그인·업무 수행 성공은 별도다. |
| FastAPI 공개 origin / prefix | `https://aio-t1.isitsoft.kr` / `/api` | FE의 `/api/:path*`가 FastAPI로 전달된다. 확인된 시험 경로: `GET https://aio-t1.isitsoft.kr/api/auth/me`. cookie가 없으면 401(로그인 필요). |
| FastAPI 내부 origin | `http://backend:8000` | Compose 내부 service DNS만 사용한다. 팀원 PC에서 직접 접속할 수 있는 주소가 아니다. |
| Swagger / OpenAPI | <https://aio-t1.isitsoft.kr/docs> · <https://aio-t1.isitsoft.kr/openapi.json> | 공개 origin에서 Swagger UI와 OpenAPI JSON 제공. `/api/docs`, `/api/openapi.json`은 지원 주소가 아니다. API 실행에는 해당 세션/키가 별도로 필요하다. |
| n8n UI / webhook origin | <https://aio-t1.isitsoft.kr:5678/> | 팀 VM의 기존 n8n 경로. 사용자에게 부여된 편집 권한과 workflow별 키는 팀장이 안전하게 인계한다. |
| 웹 터미널 | <https://aio-t1.isitsoft.kr/ssh/> | 운영·배포 담당이 사용하는 VM 터미널. 팀원이 임의로 변경/재배포하지 않는다. |
| VM 저장소 | `/home/toor/Aio-4pj-1team/` | VM의 배포 checkout. 팀원 개인 브랜치의 작업공간이 아니다. |

`backend`, `postgres`, `data-api`, `rag-search`, `n8n` 등 Compose service DNS는 VM 내부 네트워크용이다. VM 서비스 포트를 각 팀원 PC의 `localhost`로 추정하거나 직접 노출하지 않는다.

### 현재 공개 HTTP 검증

| 요청 | 결과 | 해석 |
|---|---:|---|
| `GET http://aio-t1.isitsoft.kr/login` | 301 → HTTPS, 최종 200 | 로그인 HTML route 정상 |
| `GET https://aio-t1.isitsoft.kr/login` | 200 `text/html` | FE 로그인 HTML 응답 |
| FE HTML에서 발견한 Next static JS asset (HEAD) | 200 `application/javascript` | 공개 정적 자산 전달 확인 |
| `GET https://aio-t1.isitsoft.kr/api/auth/me` (cookie 없음) | 401 `application/json` | 인증 필요한 API의 정상 비로그인 응답; 로그인 성공 시험은 아님 |
| `GET https://aio-t1.isitsoft.kr/docs` | 200 `text/html` | SwaggerUIBundle와 같은 origin의 `/openapi.json` 참조 확인 |
| `GET https://aio-t1.isitsoft.kr/openapi.json` | 200 `application/json` | 유효 OpenAPI 3.1.0; 18개 paths, 인증·ask·티켓 경로 존재 |
| `GET https://aio-t1.isitsoft.kr/api/docs`, `/api/openapi.json` | 404 | 이 prefix의 문서 경로는 추가하지 않음 |
| `GET https://aio-t1.isitsoft.kr:5678/healthz` | 200 | 기존 n8n health route |

## 초기 VM 기준선 · 2026-11-06 10:01 KST snapshot

읽기 전용 VM 관제 snapshot: 2026-11-06 01:01 UTC (10:01 KST), repository `a3dd276`; runtime 구현 커밋 `c1a4c8b`. Repo `main=997ea60`은 VM에 적용된 버전으로 간주하지 않는다.

| 항목 | 현재 확인값 |
|---|---|
| Compose project / 컨테이너 | project `oke`; 9개 컨테이너 실행: `oke-n8n-1`, `oke-runners-1`, `oke-sandbox-api-1`, `oke-sandbox-runner-1-1`, `oke-postgres-1`, `oke-data-api-1`, `oke-backend-1`, `oke-frontend-1`, `oke-rag-search-1`. 주요 health 상태: PostgreSQL, sandbox API, backend, frontend, RAG search healthy. |
| 실행 모드 / DB | backend/n8n/runners `SERVICE_MODE=app`; backend readiness `ready`; Alembic `0005`. |
| 저장 행수 | employees/users/tickets/alerts/DLQ = `6/1/3/4/1`; `rag.documents/chunks=8/33`. 값은 위 snapshot 시점으로 고정된 관측이다. |
| 자원 | RAM `2646 MiB` total / `1436 MiB` available; swap `2965 MiB` total / `224 MiB` used. 이 수치는 snapshot 시점이며 이후 상태를 보장하지 않는다. |
| FE / 외부 라우팅 | 외부 `/login`: HTTP 200 HTML; HTTP `/login`은 HTTPS로 301; no-cookie `/api/auth/me`: 401; n8n `:5678/healthz`: 200. 공개 FE 라우팅은 정상 관측됐다. 인증 후 사용자 흐름은 미검증이다. |
| 관리자 / 사용자 | 활성 admin `minji.admin` 1명, `must_change_password=true`; 일반 직원 로그인 계정은 0명. 암호변경·재생성은 하지 않았다. |
| n8n workflows | 5개 보존. active 4: `oke-support` (`okeSupportFlow01`, activeVersion `ece576c6-9c22-4243-9d18-68ba93a7a167`), `oke-search` (`okeSearchFlow01`, `272b0845-6236-494c-a090-aca2c70a025b`), `oke-handoff` (`okeHandoffFlow01`, `1cd11549-76aa-473d-945b-158c7ac0f8a0`), `oke-errors` (`okeErrorsFlow01`, `8bab332b-8ca5-44f7-98d7-c824a75dd803`). `oke-index` (`okeIndexFlow01`) inactive/manual. `activeVersion` values are n8n runtime metadata, not Git commit hashes. |
| Credentials | credential records 6개 존재. 실제 비밀값·credential IDs·사용자별 접근권한은 이 문서에 싣지 않는다. |

주요 Compose 컨테이너 이름과 서비스명은 `oke-<service>-1` 형식으로 유지된다. `rag-index`는 indexing profile의 수동 작업 대상이며 기본 상시 서비스가 아니다. SearXNG는 `optional-search` profile로 보존되어 있으나 이번 확인에서 기동하지 않았다. 색인/검색 환경을 바꾸는 작업은 예약·승인된 배포 담당이 수행한다.

### Workflow / 인증 사용 원칙

- n8n runtime workflow stable IDs는 위 표를 참조한다. 활성본을 덮어쓰거나 같은 ID의 새 workflow를 임의 생성·활성화하지 않는다. `oke-index` 수동 색인도 별도 예약 없이 실행하지 않는다.
- VM에는 목적별 credential 6개 레코드가 보존되어 있다. 이전 runtime cleanup inventory의 구분은 OpenAI, team webhook, RAG search, RAG index, backend internal, legacy Header Auth account였다. 현재 snapshot은 레코드 수만 재확인했으므로 credential ID/값 및 각 노드 매핑을 본 문서에서 보증하지 않는다.
- 팀장 또는 지정 관리자는 팀원에게 필요한 사용자 권한, workflow 실행 경로, 해당 용도의 자격 증명 사용 방법만 비공개로 인계한다. key/password/header value를 Git·이슈·채팅·보고서·화면 캡처에 붙이지 않는다. 여러 용도의 키를 이름이 비슷하다는 이유로 공유하지 않는다.
- 팀원은 개인 계정을 사용하거나 아래 공유 시험 계정을 사용한다. 최신 계정 기준선은 아래 “팀원 공용 시험 계정 및 접속 안내” 절을 참조한다.
- 현재 VM n8n owner 사용자는 1명이다. owner 로그인 ID는 팀장이 비공개로 인계한다.
- 관리자/직원 시험 계정 정보는 팀원 전체의 원활한 UI/API 기능 테스트를 위해 아래 문서에 투명하게 공개하여 공유한다.
- 공개 API는 `/api/auth/me` 외부 401을 확인했다. API 경로/스키마는 repo의 [API-CONTRACT](API-CONTRACT.md)와 versioned backend source를 따른다. Swagger UI는 <https://aio-t1.isitsoft.kr/docs>, 스키마는 <https://aio-t1.isitsoft.kr/openapi.json>을 사용한다. UI 열림과 인증 API 실행 권한은 별개다.

## 팀 작업 순서

1. 각 담당자는 자기 소유 폴더/브랜치에서 구현·검증하고 commit SHA, 실제 입력, 기대/실제, test 범위와 남은 문제를 기록한다. 다른 담당자의 폴더·공통 workflow를 직접 편집하지 않는다.
2. 변경은 feature branch → 담당자 보고/검토 → 팀장 main 통합·VM 배포 순서로 진행한다. `main` commit이 VM 반영을 뜻하지 않으므로 배포 뒤 실제 VM repo/runtime version을 확인한다.
3. 팀원은 예약된 시험만 실행한다. VM workflow를 UI에서 덮어쓰거나 import/publish, Compose up/down/restart, `SERVICE_MODE` 변경, DB 초기화, fault/reset, index, restore를 독자 실행하지 않는다.
4. 쓰기/장애/중복/복구 시험은 시간대를 정하고 시작 전 환경과 DB 행수·fault 대상·종료 후 정상복귀 조건을 기록한다. 기존 PostgreSQL/n8n volume, course data-api 원본과 마운트를 유지한다. 동일 운영 DB를 동시에 수정하지 않는다.

## 공통 14 테스트 출발점

공통 기준은 [EVALUATION-GUIDE](EVALUATION-GUIDE.md)의 WF-01~WF-13 및 WF-02b 14유형이다. 저장소 및 `Last3Mon/79` checkout에서 공식 80일차 `cases/common.json`을 확인하지 못했다. 확인 가능한 `Last3Mon/79/tools/flow.py`는 SHA-256 `6b0059cb3af135b08954559d0e6b757991fc2fc42a0624244d129e618284fb6f`이며 HTTP helper가 JSON content type만 보내고 custom `X-Team-Key` header를 지원하지 않는다. `develop/dahyeok/tools/flow.py`는 Mock checker이므로 공식 시험 runner로 대체하지 않는다.

따라서 현재 공통 14의 execution coverage/pass/total/raw는 **미실행·N/A**다. 이를 실패 0/14 또는 성공 14/14로 바꾸지 않는다. 공식 원본과 인증을 지원하는 공식 runner/절차를 팀장·시험 담당이 인계한 뒤 실제 입력·기대값을 그대로 사용한다. 상태변경/fault/restore가 필요한 케이스는 격리 대상과 예약된 시간에서만 실행한다. 기대값을 완화하거나 인증을 제거하지 않는다.

## 기록 양식

사례마다 아래 항목을 run report에 기록하고 key, cookie, 개인 연락처, 원문 민감정보는 포함하지 않는다.

| 필드 | 기입 내용 |
|---|---|
| 환경 | `team VM`; service/workflow 이름 |
| 실행 버전 | repository commit, runtime deployment commit, workflow stable ID/version; 서로 구분 |
| 사례 / 요청 | official case ID와 고유 `request_id`; 입력은 공용 시험 입력 또는 최소한의 비민감 요약 |
| 판정 | 기대 route/status/sources/ticket 조건과 실제 결과, pass/fail/not-run 사유 |
| 저장·권한 | 필요한 경우 실행 전/후 안전한 행수, 본인/타인 결과, duplicate·alert·DLQ. 민감 row 내용은 기록하지 않음 |
| 추적 | 시작 시각과 timezone, n8n execution ID(있을 때), 응답 시간/HTTP, raw JSON/log 파일의 repository-relative 경로 |
| 복구 | fault/index/restore를 한 경우 예약·대상·정상화 확인과 책임자 |

독립 반복은 매회 새 request ID를 쓰고, 멱등성 재요청은 같은 request ID를 쓴다. 기대값, 원 raw, 실패 및 동일 조건 재시험을 보존한다. 실행하지 않은 사례에는 raw 경로를 만들어 적지 않는다.

## 팀장에게 필요한 추가 인계

- 일반 직원/IT 역할 시험계정의 발급 절차, 담당자, 첫 비밀번호 변경 시점과 비공개 전달 방식. 기존 `minji.admin`은 수정하지 않는다.
- team member별 VM/n8n access level과 feature-specific workflow/webhook credential 사용 경로. 비밀값을 저장소에 기록하지 않는다.
- 공식 14 case file/원본 hash, 공식 runner version, custom header authentication을 지원하는 명령/방법, run output 저장 위치.
- 오늘 필수 VM 시험의 버전 pin·시간 slot·초기 행수·격리/fault 대상·복구 담당. 점수 threshold는 실제 측정/승인 전 임의 지정하지 않는다.
- 유빈님의 RAG 주말 후속 인계와 담당 산출물. 이는 오늘의 WF-01/기타 필수 실측을 대체하거나 연기하지 않으며, 오늘 대체 측정 담당·마감은 별도 결정이 필요하다.

## Swagger 공개 경로 추가

검증 시각: 2026-11-06 10:24:37 KST.

- TASK `vm-public-swagger-1`, FE 코드 `e7f5161`. 기존 `/api/:path*` rewrite를 유지하고 정확히 `/docs`, `/openapi.json`을 backend 기본 경로로 프록시했다. 공개 포트/ingress·backend·계정·DB·workflow는 바꾸지 않았다.
- VM은 이전 repo `a3dd276`에서 ff-only로 FE 커밋을 받았고, `BACKEND_ORIGIN=http://backend:8000`으로 frontend만 build 및 `up -d --no-deps frontend` 했다. 기존 runtime `c1a4c8b`의 나머지 서비스와 FE 추가 커밋을 구분한다. 아래 최신 FE 관측은 위 1교시 baseline의 이후 기록이다.
- 외부 curl로 docs200/Swagger HTML·schema URL, openapi200/유효 JSON·인증/ask/티켓 paths, login200/Next static JS200, no-cookie me401, n8n health200을 확인했다. 스키마 보안 유형은 cookie/header API key이며 OAuth callback은 필요하지 않아 추가하지 않았다.
- POST/삭제/DB변경 시험·로그인/암호변경은 실행하지 않았다. Try it out의 성공은 인증/권한에 달려 있으며 이번 범위의 검증이 아니다.

- 브라우저 렌더 확인을 시도했으나 CUA browser host unavailable로 탭을 만들 수 없었다. HTML/JSON의 외부 HTTP 검증은 통과했으며 시각적 렌더는 미확인이다.

## FE/BE 배포 및 실제 QA 후속 · 2026-11-06 11:55 KST

- main `99fff9c`에서 backend/frontend만 배포했고, FE guard 수정 `3ff836a`는 frontend만 추가 배포했다. 최종 VM repo는 `3ff836a`; backend/frontend healthy. n8n, runners, PostgreSQL, data-api, RAG search와 기존 volumes는 이 작업 중 재기동·변경하지 않았다. workflow 4개 active 및 index manual 상태를 유지했다.
- 계정 metadata: `minji.admin` active admin / `must_change_password=false`; `teamtest.employee1` active employee / `must_change_password=false`. 직원 계정은 공식 roster entry에서 발급했고, 첫 암호 변경·재로그인·내 문의 200·admin API 403·로그아웃/세션 종료를 공식 API로 검증했다. 비밀은 팀장 전용 private handoff에만 있다.
- 공개 read-only: `/login` 200, no-cookie `/api/auth/me` 401, `/docs` 200, `/openapi.json` 200, n8n `:5678/healthz` 200. FE 브라우저 시각/클릭 검증은 자동화 host unavailable로 미실행이다.
- QA attempt 1, 고유 request ID `real-qa-36352d26c53e48eab65a42c4a0c5ec85`: API sequence `PASS_API_SEQUENCE`; route는 `담당자 이관`, elapsed 7.341초, sources는 빈 목록. 직원 문의 목록 및 로그아웃 후 재로그인 조회, admin 처리 상태/답변 재조회, 직원 admin API 403을 확인했다. 빈 sources이므로 C03 검색 또는 WF-01 정상 자동답변 성공으로 해석하지 않는다.
- 별도 read-only PostgreSQL 대조에서 해당 request ID의 `app.inquiries` 1행, `app.tickets.request_key` 1행, `ticket_id=T-2005`; inquiry/ticket/requester 연결키 일치 및 상태 `in_progress`를 확인했다. 과거 전체 행수와의 차이는 동시 변경 가능성이 있어 이 QA 고유 키/연결행 외의 변화를 단정하지 않는다. 기존/타인 행 삭제·초기화는 하지 않았다.
- 브라우저 화면, 정상 자동답변/8초 기준, RAG evidence 검색, 동일 request ID 중복 재요청, alert/DLQ 관계, 공식 common-14는 미실행이다.

## 팀원 공용 시험 계정 및 접속 안내 (2026-11-06 공유)

팀원 전체가 브라우저 및 API에서 실제 서비스 플로우를 테스트할 수 있도록 검증이 완료된 공용 계정 정보를 공유합니다.

### 1. 주요 접속 엔드포인트
* **웹 프론트엔드 (로그인)**: <https://aio-t1.isitsoft.kr/login>
* **FastAPI Swagger UI**: <https://aio-t1.isitsoft.kr/docs>
* **OpenAPI 스키마**: <https://aio-t1.isitsoft.kr/openapi.json>
* **n8n 웹 콘솔**: <https://aio-t1.isitsoft.kr:5678/> (Owner 계정은 팀장에게 비공개 인계)

### 2. 공용 테스트 계정 정보

| 구분 | 로그인 ID | 비밀번호 | 이름 / 소속 | 역할 | 상태 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **관리자** | `minji.admin` | <팀장 비공개 인계> | 김민지 (IT팀) | `admin` | `must_change_password=false` 검증 완료 |
| **직원 (테스트용)** | `teamtest.employee1` | <팀장 비공개 인계> | 이준호 (영업팀, 사번 1) | `employee` | 첫 비밀번호 변경 및 권한 검증 완료 |

### 3. 브라우저 실서비스 테스트 방법
세션 충돌 방지를 위해 **일반 창과 시크릿 창(또는 다른 브라우저)**으로 분리하여 로그인합니다:
1. **직원 창 (`teamtest.employee1`)**:
   - 로그인 후 새 문의(Ask/Inquiry) 작성 및 전송
   - '내 문의' 페이지에서 티켓 번호 생성 확인
2. **관리자 창 (`minji.admin`)**:
   - 로그인 후 `/admin/tickets` 접속
   - 직원이 등록한 문의 티켓 확인 후, 티켓 상태(예: `in_progress` 또는 `resolved`) 및 관리자 답변(Reply) 입력/저장
3. **직원 창 (`teamtest.employee1`)**:
   - '내 문의' 페이지 새로고침
   - 관리자가 입력한 상태와 답변이 정상 반영되어 저장된 것을 확인

