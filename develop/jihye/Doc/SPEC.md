# 지혜님 · SPEC

[TODO](TODO.md) → **SPEC** → [IMP-PLAN](IMP-PLAN.md). 요구 명세이며 단계별 실제 구현·시험 결과는 IMP-PLAN에 구분한다. P0-1~7·P1-1~3의 로컬 확인은 기록 완료다. P1-4 로컬 재시작 유지·C02 Mock web-flow·별도 DB backup/restore는 확인했지만, 실제 RAG 문서/embedding이 없는 상태에서의 복원·검색, 정상 근거 답변을 포함한 전체 연결, 공식 공통 평가는 미완료다. 팀 VM에서 수행한 일부 인증·문의·티켓 API 확인은 루트 VM 기록을 출처로 표시하며 지혜님 직접 실행 결과로 취급하지 않는다. 예시 ID·응답은 기대값이며 실행 결과가 아니다. 기준 적용은 바로 진행하고 변경/누락 정책만 [HANDOFF](HANDOFF.md)로 요청한다.

## 1. 적용할 기준 · 새로 선정하지 않음

### 현재 기준과 구현 상태 · 2026-11-06 대조

개인 작업의 출발점은 본 SPEC과 IMP-PLAN이다. 아래 표는 지혜님이 필요한 공통 기준을 구현용으로 옮긴 것으로, 공통 계약을 새로 정하는 문서가 아니다. 현재 브랜치에 병합된 공통 기준의 확인 커밋은 `7afabdc`다. 해당 공통 문서가 바뀌면 이 절과 영향받는 계획을 다시 대조한다. 과거 H 제안과 다른 경우 이 현재 기준을 사용한다.

| 항목 | 현재 적용 기준 | 구현/확인 단계 | 출처 |
| --- | --- | --- | --- |
| 질문 입력 | question trim 후1~500자, request_id1~64자·비공백, attempt 엄격한 정수≥1·기본1 | P0-1~2 모델/Mock 확인 | API §1~2, 평가 §3.1 |
| context | 문자열 최대2,000자. 생략/null 호환 유지, 빈 문자열 허용. 공백 보존·묵시적 절단 없음 | P0-2 보완·모델/Mock 확인. 실행 결과는 IMP-PLAN 기록 | 평가 §3.1; null/생략은 기존 모델 호환 |
| 신원·API | 웹14 operation(13경로)·내부3 API. 화면 user/dept/role을 믿지 않고 세션에서 결정 | P0-2 모델, P1-1 인증 구현·로컬 PostgreSQL 시험 완료. VM API account checks는 루트 기록 참조 | API §1~2·5 |
| 세션 | oke_session, HttpOnly, SameSite=Lax, Path=/, 기본8시간. DB에는 token_hash만 저장 | P0-4 테이블·P1-1 구현 및 격리 PostgreSQL HTTP 시험 완료. VM 인증 API 점검은 팀 VM 보고에 기록 | API §8, DB §3 |
| 첫 변경·회수 | 미변경은 me/change-password/logout만 허용, 나머지403 password_change_required. 변경·초기화·비활성화 시 기존 세션 폐기 | P1-1 로컬 PostgreSQL 시험 완료. VM API 계정 확인 기록이 있으며 화면 상호작용은 별도 | API §8 |
| 비밀번호 | 최소12자·대소문자/숫자/특수문자 중3종·본인 이름/로그인ID 포함 금지. 이력·잠금·외부OTP는 P2 | P1-1 서비스·격리 DB 시험 완료 | API §8, ADR-001 §2 |
| 관리자 | 제공 IT직원만 admin, 본인·마지막 활성 관리자 비활성화 거절. 충돌409(또는400 안내) | P0-6 bootstrap·P1-1 구현/로컬 시험 완료. VM 관리자 API 시험은 루트 VM 기록 참조 | API §2·8, DB §3 |
| 시간 예산 | 브라우저35초, backend→support 연결3초·전체30초·자동 재시도0. 조회2초·search4초·handoff5초; 티켓 최대2회·각1초, 알림/DLQ 각1회·0.6초 | 구현된 timeout 및 Mock/로컬 경계시험과 실측 성능을 구분. 정상 VM 자동답변의 8초 평가는 미확인 | API §8, 워크플로우 §4~5 |
| 업무 저장 | app7테이블, request_key·ticket_id UNIQUE, T-2001~. 알림 실패가 commit한 티켓을 취소하지 않음 | P0-4 DDL·P1-3 로컬 저장 검증 완료. VM QA는 한 문의/티켓 연결과 관리자 처리 사례이며 전체 workflow/C05 장애 경계 검증은 아님 | DB §3, 워크플로우 §7 |
| 알림·DLQ | POST /dlq와 alerts.event_key는 확정. 알림 HTTP200 신규 stored=1/duplicate=false, 기존 key stored=0/duplicate=true. event_key 생략/null은 매번 신규. DLQ HTTP200 저장 ACK. practice 신규 ACK의 duplicate 생략은 consumer 호환 | 공통 기준 `7afabdc`에 반영. P1-3 app 로컬 DB 시험 완료; VM alerts/DLQ 전체 실연결은 미확인 | API §5, HANDOFF H07 |
| RAG | documents/chunks, vector(3072), text-embedding-3-large, all/it, cosine 정확검색·score=1-distance·top_k3 | 로컬 DDL·권한 시험 완료. VM snapshot의 8 documents/33 chunks는 기존 데이터 관측이지 신규 색인·품질시험이 아님. C03 정상 근거 답변은 미확인 | DB §4, RAG §3~4 |
| RAG 거래·복구 | 문서 교체 한 거래, 갱신 실패 시 이전 성공본 유지. 권한 축소/삭제는 이전 공개 청크 차단. named volume과 별도 백업·복원 구분 | 로컬 별도 DB backup/restore 구조 비교는 확인. 원본 RAG rows가 0건이라 실제 vector 복원·복원 후 권한별 검색은 미실행. P1-4 잔여 | RAG §4~5 |

출처: [API](../../../docs/API-CONTRACT.md), [DB](../../../docs/DATA-AND-DB.md), [평가](../../../docs/EVALUATION-GUIDE.md), [RAG](../../../docs/RAG-ARCHITECTURE.md), [워크플로우](../../../docs/WORKFLOW-DESIGN.md), [ADR](../../../docs/adr/ADR-001-project-decisions.md). 서비스별 인증은 구분한다: 웹=세션, support/search/handoff=X-Team-Key, FastAPI 내부 저장=X-Api-Key. 실제 data-api 읽기 응답/인증은 미확인으로 유지한다.

### 제안으로 남은 부분

- H01의 현재 브라우저 새 세션 발급·Origin 검증 등 추가 세부, H03의 미지 필드 거절/필드별 코드·목록 단건 DTO·patch 생략/null 해석은 초안이다.
- Security는 공통 필드 blocked_by/reason/masked를 유지한다. 현재 nullable 허용 등 세부 타입의 호환성은 다혁님과 대조한다.
- H04의 처리 중 응답·상태 전이·오류 request_id 필드·응답 캐시 세부는 제안이다. 같은 키 본문 충돌 거절과 타인 소유권 검사는 확정이므로 대기시키지 않는다. 캐시 응답이 WF-09의 재요청 duplicate=true 판정과 충돌하지 않도록 다혁님·원민님과 확인한다.
- H05의 비어 있지 않은 계정 집합에서 관리자 부재 복구 같은 운영 세부는 별도 검토다. 본인/최후 관리자 보호는 이미 확정이다.
- H07 알림 전용 duplicate ACK 확장·DLQ200은 공통 API 기준 `7afabdc`에 명문화됐고 P1-3 app 로컬 DB 구현/시험에 반영됐다. event_key 생략은 매번 신규 저장이고 count 단독은 ACK가 아니다. practice의 기존 신규 ACK에서 duplicate 누락은 consumer가 호환하지만 app 응답은 duplicate를 명시한다. live practice 및 VM workflow의 alert/DLQ 경계 연결은 별도 확인한다.

### 기준 상세

| 구분 | 적용 내용 | 원본 |
| --- | --- | --- |
| 인증 | 공개 가입 없음, 관리자 발급, 첫 관리자 환경변수 1회 준비, 첫 로그인 비밀번호 변경, 세션에서 id/name/dept/role 결정 | [TOPIC](../../../docs/TOPIC.md), [API C01·8](../../../docs/API-CONTRACT.md) |
| 공개/내부 API | C01의 14개 operation(13개 경로)(`GET /api/admin/employees`, `GET /api/admin/users` 포함), C02 공통 응답·route 전체 보존, C05 `/tickets`·`/alerts`(`event_key` 포함)·`/dlq`, X-Team-Key와 X-Api-Key 분리 | [API](../../../docs/API-CONTRACT.md) |
| 오류 | 입력 400, 미로그인/로그인 실패 401, 소유권/관리자 권한/미변경(`password_change_required`) 403, 없는 티켓·계정 404, 중복·충돌 409(또는 400). 웹은 error.code/message, 공통 웹훅 400 codes는 그대로 전달 | API 2·8절 |
| 업무 DB | PostgreSQL app, bigint identity PK·timestamptz·FK, 직원 6명 name/dept, 계정/세션/문의/티켓/알림/DLQ. request_id 1~64자, 질문 1~500자, attempt>=1 | [DB 1~3절](../../../docs/DATA-AND-DB.md) |
| 티켓 | request_key·ticket_id UNIQUE, T-2001부터 별도 시퀀스, open/in_progress/resolved↔접수/처리 중/완료, normal/high↔보통/긴급 | DB 3절 |
| RAG | rag.documents/chunks, vector(3072), text-embedding-3-large, cosine 정확 검색·score=1-distance·top_k=3, all/it 권한을 검색 전에 적용 | DB 4절 |
| 실행 | compose 위치 develop/jihye/deploy/compose.yaml; frontend/backend/postgres/n8n/data-api; 내부 8000/5432/5678/8800, 공개 웹 기본3000; backend context=.., frontend=../../sueon | API C07 |
| 모드 | app은 새 업무 PostgreSQL, practice는 공통 고장 시험 data-api. 같은 티켓을 두 대상에 동시 생성하지 않음 | API C05·C07, [COORDINATION](../../../docs/COORDINATION.md) |

이전의 ‘담당자가 새로 정할 것’ 중 API 경로·오류 외형·내부 인증·DB/테이블/고유키·모델/차원·포트는 위 적용 항목으로 옮겼다. Alembic·SQLAlchemy·psycopg·HTTPX는 본인 구현 도구로 계획한다. 버전은 설치 검증 후 본인 잠금 파일에 고정한다.

## 2. 요구 ID와 통과 기준

| ID / 우선 | 입력·사전 조건 | 예상 출력 | 오류·경계 / 통과 기준 |
| --- | --- | --- | --- |
| BE-01 / 필수 | 직원 원본 6명, 첫 관리자, 로그인·계정 관리 요청 | 세션 쿠키·계정 요약·첫 변경 상태 | 공개 가입 경로 없음, 직원 관리자 API 403, 미로그인 401, 비활성/만료/폐기 세션 거부. 첫 변경·초기화·비활성화와 최후 관리자 보호는 확정 기준으로 실제 시험 |
| BE-02 / 필수 | 세션 + question, 선택 request_id/attempt/context | 동일 support 공통 응답 전체 | 서버가 user를 설정. 빈/501자·attempt0은 400이며 support 미호출. n8n 400 codes 보존. 미유효 응답을 성공으로 저장하지 않음. 연결3초·전체30초·자동 재시도0·장애503/504는 확정, 추가 코드/필드는 H04 제안 |
| BE-03 / 필수 | 본인 문의·request_id 재시도·동시 요청 | 본인 목록, 같은 논리 요청의 저장 결과 | 타인 키 403·본문 미노출, 본인 목록에 타인 0건, 재시작 뒤 저장값 동일. 동일 키 동시 처리·변경 본문 처리 세부는 H04 |
| BE-04 / 필수 | X-Api-Key + 티켓/알림 입력, 관리자 세션 | 신규201/중복200 티켓, stored/count 알림, 관리자 목록/변경 | 동일 key 동시 생성에도 티켓 1건, 티켓 저장 후 알림 실패 시 티켓 보존, 잘못된 키401, 직원403, 없는 티켓404. practice/app 대상을 구별 |
| BE-05 / 필수 | 빈 DB·환경변수·명시한 직원/첫 관리자 선택 | revision head, 직원6명·첫 관리자1명, 준비 상태, 배포 설정 | 마이그레이션 재실행 무변경, bootstrap 재실행 비밀번호/역할 덮어쓰기 없음, 비밀값 미출력. 볼륨 유지 재시작 후 건수·관계 유지 |
| BE-06 / 필수 | pgvector·규정 메타데이터·3072차원 테스트 벡터 | rag 테이블·권한·정확 검색 기반 | 잘못된 차원/권한 거절, 업무/rag 분리, 일반 검색 all만·IT all+it, 재색인 후 중복 청크 없음·재시작 유지. 실제 임베딩/품질은 유빈님 결과로 별도 검증 |
| BE-07 / 필수 | 동일 질문 세트·버전·모드·실행 대상 | 품질/처리시간 원자료와 측정 절차 | 미측정 수치를 PASS로 쓰지 않음. 기준 미달·실패·반복 편차도 기록. 8절 참조 |

H01 등의 축약은 HANDOFF의 JH-H01 등을 뜻한다. 각 항목의 현재 상태는 1절 적용표를 따른다. 번호 전체를 미확정으로 취급하지 않는다. 남은 추가 정책만 HANDOFF에서 검토하며 확정 기능은 예정 단계에서 구현한다.

## 3. FastAPI 파일과 모델 책임 · P0-1~2 범위 구현, 나머지 예정

경로는 `develop/jihye/` 기준이다. API 라우터는 검증과 서비스 호출을, 서비스는 권한·거래를, repository는 DB 접근을 담당한다. n8n·data-api HTTP 호출을 라우터에 중복 작성하지 않는다.

| 예정 파일 | 책임 / 연결 요구 |
| --- | --- |
| app/main.py, app/core/config.py, app/api/errors.py | 앱/라우터 등록·환경변수 검증·검증 오류→400·마스킹 / BE-02·05 |
| app/api/deps.py, app/core/security.py | DB 세션·활성 직원·관리자 검사, 비밀번호 해시·세션 토큰 해시 / BE-01·03 |
| app/api/routes/auth.py, users.py | 로그인/me/로그아웃/변경·관리자 계정 생성/변경/초기화 / BE-01 |
| app/api/routes/ask.py, requests.py, tickets.py, alerts.py, health.py | 질문·본인 목록·내부 저장·관리자 조회/변경·liveness/readiness / BE-02~05 |
| app/schemas/common.py, auth.py, users.py, support.py, inquiries.py, tickets.py, alerts.py | Pydantic 요청/응답 모델, Literal 상태값, OpenAPI / BE-01~04 |
| app/services/auth.py, accounts.py, inquiries.py, tickets.py, alerts.py | 계정/세션 수명·소유권·문의 실행 제어·멱등 거래 / BE-01~04 |
| app/clients/support.py, data_api.py, app/services/storage_mode.py | HTTPX·키/URL 주입·응답 검증·practice/app 한 대상 선택 / BE-02·04 |
| app/db/base.py, session.py, models/*.py, repositories/*.py | app/rag 매핑·DB 거래. 실제 테이블은 공통 DB 구조 사용 / BE-03~06 |
| app/cli.py, app/services/bootstrap.py | 직원 seed·첫 관리자의 명시적 1회 생성, 비밀번호를 인자로 받지 않음 / BE-01·05 |

### 입력·출력 모델 작성 규칙

- 웹 요청은 엄격한 타입으로 검증한다. 정수 자리에 문자열·소수·boolean을 받지 않도록 한다. `question`은 앞뒤 공백 정리 후 1~500자, request_id는 1~64자 비어 있지 않은 문자열, attempt는 기본1·정수>=1이다. 원문과 검사값 처리 방식은 support의 글자 정리와 맞추고 원문 전체를 로그로 남기지 않는다.
- `AskRequest`는 question, 선택 request_id/attempt/context만 받는다. user/dept/role/channel을 신원으로 쓰지 않는다. 추가 필드 거절(400)과 필드별 코드 목록은 H03 제안이며, 채택 전에도 주입한 user로 n8n을 호출해서는 안 된다.
- 웹 입력 모델은 허용 필드만 사용한다. 내부 ORM 객체를 그대로 직렬화하지 않고 응답 모델로 password_hash/token_hash/원문 비밀번호·토큰을 제외한다. 비밀번호 검증 오류에도 입력값을 넣지 않는다.
- `SupportRequest`는 request_id/user/question + channel=web, attempt, context를 C02로 전송한다. user는 세션→users→employees의 제공 이름이다. context는 이전 보완 정보 문자열로 전달하며 공통 평가 §3.1의 최대2,000자를 검사한다. 생략/null 호환을 유지하고 값을 절단하지 않는다.
- `SupportResponse`는 request_id, route(정해진 5값), answer(str), sources(list[Source]), ticket(TicketRef 또는 null), agents(list[str]), security(Security)를 필수로 검증한다. `Source`는 doc/section(str), score(유한 float); `TicketRef`는 ticket_id(str), priority(normal/high), duplicate(bool)다. 예시 점수를 신뢰도 임계값으로 사용하지 않는다.
- `Security`의 blocked_by·reason(문자열 또는 null), masked(비음수 정수) 형식은 73일차 출력 예시와 호환하는 모델 초안으로 H03에 요청한다. 필드는 제거하지 않는다. 선택 reason, timings 및 추가 상위 응답 필드도 보존하며 응답 모델 기본 설정 때문에 소실시키지 않는다. timings의 값은 실제 단계별 ms다.
- 웹 목록은 `ItemsResponse[T]`의 `{"items":[]}`다. `UserSummary`는 id/name/dept/role, 로그인 user에는 must_change_password를 포함한다. 관리자 계정 응답의 login_id/is_active/employee_id는 공통 확정이다. 문의/티켓 목록 단건과 기타 미명시 세부만 H03 초안이며 관리자 알림 필드는 공통 API §2를 따른다.
- 웹 `ErrorResponse`는 `{"error":{"code":"forbidden","message":"접근 권한이 없습니다."}}` 외형을 따른다. FastAPI 기본 422/detail을 그대로 노출하지 않는다. 공통 웹훅 HTTP400의 codes 본문은 별도 passthrough로 유지한다.

## 4. C01 API별 검증 예시

아래는 **구현 후 실행할 예시**다. 직원/관리자 세션은 fixture 또는 실제 발급 계정으로 준비한다. `employee_id=2`, `user id=7`, `ticket id=3`, `assignee employee_id=5`(IT팀 직원 ID)는 설명용이며 seed 후 조회한 실제 ID로 치환한다. 비밀번호는 비밀 입력/시험용 런타임 생성으로 주고 문서·보고서에 값을 쓰지 않는다.

공통 계약(`docs/API-CONTRACT.md`)에 반영된 웹14개 operation(13개 경로)과 요청/응답 키를 그대로 적용한다.

| 경로 / 모델 / 요구 | 입력·사전 조건 | 예상 출력·정상 검증 | 오류·경계 검증 |
| --- | --- | --- | --- |
| POST /api/auth/login / LoginRequest→LoginResponse / BE-01 | login_id + password, 활성 계정 | 200, `{"user":{"id":7,"name":"박서연","dept":"재무팀","role":"employee","must_change_password":true}}` + `oke_session` HttpOnly 쿠키 | 없는ID/잘못된 암호401 같은 안내, 누락400·쿠키 없음, 비활성 로그인401 |
| POST /api/auth/logout / OkResponse / BE-01 | 세션 쿠키, 본문 없음 | 200 `{"ok":true}`, 세션 폐기·쿠키 삭제 | 이전 쿠키로 me401, 미로그인401 |
| GET /api/auth/me / UserSummary / BE-01 | 유효 쿠키 | 200 `{"id":7,"name":"박서연","dept":"재무팀","role":"employee","must_change_password":false}` | 미로그인/만료/폐기401, 다른 사용자의 요약 미노출 |
| POST /api/auth/change-password / ChangePasswordRequest→ChangePasswordResponse / BE-01 | current_password/new_password, 임시 암호 세션 | 200 `{"ok":true,"must_change_password":false}`, 저장된 해시 변경·기존 세션 폐기 | 현재 암호 오류401, 새 규칙(12자·3종 조합) 위반400 |
| POST /api/ask / AskRequest→SupportResponse / BE-02·03 | `{"question":"VPN이 계속 끊겨요","request_id":"web-vpn-001","attempt":1}` | 200, 아래 공통 응답 예시; Mock 수신 user=세션의 박서연, channel=web | 공백/501자/attempt0/ID65자400·support 호출0, 질문500자·ID64자 수락. 다른 직원 키403·조회/호출0 |
| GET /api/my-requests / ItemsResponse[InquiryView] / BE-03 | 서로 다른 두 직원의 문의를 준비 | 200, 본인 items만. 단건: request_id/question/attempt/result/ticket/created_at | 미로그인401, 타인 ID 필터를 보내도 타인 기록 반환0, 빈 목록 items=[] |
| GET /api/admin/employees / ItemsResponse[EmployeeAdminView] / BE-01 | 관리자 쿠키 | 200, `{"items":[{"id":1,"name":"이준호","dept":"영업팀","user_id":null}, ...]}` (제공 6명) | 직원403, 미로그인401 |
| GET /api/admin/users / ItemsResponse[AccountView] / BE-01 | 관리자 쿠키 | 200, `{"items":[{"id":7,"employee_id":2,"login_id":"...", "name":"박서연","dept":"재무팀","role":"employee","is_active":true,"must_change_password":true}]}` | 직원403, 미로그인401, 해시/비밀번호 미포함 |
| GET /api/admin/tickets / ItemsResponse[TicketView] / BE-04 | 관리자 쿠키·새 티켓 | 200, 단건: id/ticket_id/request_id/requester/title/category/priority/status/assignee/reply/created_at/updated_at | 직원403·본문 미노출, 미로그인401, 기존 T-100x 상태를 새 status enum으로 강제 변환하지 않음 |
| PATCH /api/admin/tickets/{id} / TicketPatch→TicketView / BE-04 | `{"status":"in_progress","assignee":5,"reply":"담당자가 확인 중입니다."}`; 경로 id는 내부PK, assignee는 IT팀 `app.employees.id` 또는 `null` | 200, 변경 단건·updated_at 갱신, 화면 ‘처리 중’ | 없는 티켓404, 직원403, 잘못된 status/없는 또는 비IT 담당자400, 생략한 reply/assignee는 기존값 유지 |
| POST /api/admin/users / CreateUserRequest→AccountView / BE-01 | 필드 `employee_id=2`, `login_id`(선택한 ID), `temporary_password`(런타임 비밀 입력); 식별키는 공통 확정이며, 제공 직원의 아직 미발급 계정 | 201 확정, id/employee_id/login_id/name/dept/role/is_active/must_change_password 단건; 일반직원 employee·IT팀 admin | 직원403, 없는 employee_id400 초안, 중복 직원/로그인ID409 초안. 임의 role/user/name으로 권한 상승 불가 |
| PATCH /api/admin/users/{id} / UserActivePatch→AccountView / BE-01 | `{"is_active":false}` | 200 로컬 시그니처, is_active=false 단건. 세션 폐기 API §8 확정 | 직원403, 문자열 false400, 없는 계정404 확정, 최후 관리자/자기 비활성화 거절 API §2·8 확정 |
| POST /api/admin/users/{id}/reset-password / ResetPasswordRequest→ResetPasswordResponse / BE-01 | temporary_password, 관리자 쿠키 | 200 로컬 시그니처 `{"ok":true,"must_change_password":true}`, 해시 갱신 | 직원403, 규칙 위반400, 없는 계정404 확정, 기존 세션 폐기 API §8 확정 |
| GET /api/admin/alerts / ItemsResponse[AlertView] / BE-04 | 관리자 쿠키·알림 | 200 로컬 시그니처, 공통 필드 id/ticket_id/workflow/node/message/severity/created_at | 직원403·미로그인401, message/로그/캡처에 연락처·비밀값 없음 |

HTTP200 support 응답 모델 예시(측정값이 아닌 Mock 입력):

```json
{"request_id":"web-vpn-001","route":"자동 답변","answer":"VPN 규정의 접속 오류 절차를 확인해 주세요.","sources":[{"doc":"remote-work-vpn","section":"접속 오류","score":0.82}],"ticket":null,"agents":["triage","retriever","writer","verifier"],"security":{"blocked_by":null,"reason":null,"masked":0}}
```

검증 시 이 응답과 함께 ‘보완 질문’(ticket=null), ‘담당자 이관’(ticket 객체/실패 시 null+reason), ‘권한 없음’, ‘차단’을 각각 Mock으로 주입한다. request_id 일치·모든 필드 보존·reason/timings 보존을 비교한다. 검색·검증 자체를 백엔드에서 다시 구현하지 않는다.

## 5. C05 내부 저장 API·거래

| 경로 / 모델 | 입력 | 예상 출력 | 오류·통과 기준 |
| --- | --- | --- | --- |
| POST /tickets / TicketCreate→TicketCreated | X-Api-Key, `{"key":"web-vpn-001","title":"VPN 연결 점검","requester":"박서연","category":"network","priority":"normal"}` | 신규201 `{"ticket_id":"T-2001","duplicate":false}`, 재시도200 같은ID·duplicate=true | 키 누락/오류401·쓰기0. key 빈값/65자·없는직원·priority 부정값400, 세부 오류코드만 초안. 소유자 불일치403·기존 티켓 미노출 |
| POST /alerts / AlertCreate→AlertStoredResponse | X-Api-Key, `{"workflow":"oke-handoff","node":"ticket","message":"티켓 저장을 확인해 주세요","severity":"high"}`, 선택 `ticket_id`(외부 T-번호), 선택 `event_key` | 200 신규 `{"stored":1,"count":N,"duplicate":false}`; 기존 event_key `{"stored":0,"count":N,"duplicate":true}`. key 생략/null은 매번 신규 저장. count는 단독 ACK가 아님 | 쿠키만 보낸 내부 호출401, 필수값 누락400. 외부 ticket_id→app.tickets PK 변환, 미존재 티켓은 거절. 티켓 거래와 알림 거래 분리 |
| POST /dlq / DlqCreate→StoredResponse | X-Api-Key, `{"request_id":"web-vpn-001","workflow":"oke-handoff","node":"Create Ticket","reason":"tickets_down","safe_payload":{"stage":"ticket"}}`, 선택 `execution_ref` | HTTP200, 저장 확인 `{"stored":1,"count":N}` | 쿠키만 보낸 내부 호출401, 필수값 누락400, 개인정보·비밀값 원문 저장 전 마스킹. 공통 명문화는 H07 |

- DB UNIQUE 제약과 하나의 거래로 티켓 발급/문의 연결을 묶는다. 충돌 시 rollback 후 기존 request_key 소유자를 검사해 같은 직원에게만 반환한다. 시퀀스의 번호 공백은 허용하되 번호를 재사용하지 않는다.
- 일반 웹 요청은 inquiries를 먼저 저장하고 같은 request_key의 티켓은 inquiry_id에 연결한다. 직접 웹훅 시험 요청은 inquiry_id=null을 허용한다. SQL 트랜잭션을 n8n HTTP 호출 동안 잡아 두지 않는다.
- 티켓 저장과 알림 저장은 분리한다. 알림 실패가 이미 commit한 티켓을 지우지 않는다. 재시도에서 티켓은 기존ID를 받고 알림만 복구할 수 있어야 한다.
- 동시 동일 key 두 호출의 신규/중복 응답과 DB 건수1을 확인한다. 단순 메모리 dict나 ‘조회 후 insert’만으로 멱등을 보장하지 않는다.
- DLQ 테이블과 `POST /dlq` 내부 API는 공통 계약(`docs/API-CONTRACT.md` §5, `docs/DATA-AND-DB.md` §3)대로 구현한다.

## 6. 직원 seed·첫 관리자·권한

1. `GET /employees`에서 제공 name/dept 6명을 조회한다. 이준호/영업팀, 박서연/재무팀, 최유진/인사팀, 한지훈/개발팀, 김민지·정우성/IT팀을 검증한다. 누락/추가/부서 변경이면 원본 불일치를 기록하고 seed 중단한다. 이메일·입사일을 만들지 않는다.
2. 직원 seed는 name 기준 중복 방지로 실행한다. 기존 이름의 dept가 다르면 자동 덮어쓰기하지 않고 보고한다. employees 적재는 users 6계정을 일괄 만드는 절차가 아니다.
3. 첫 관리자 CLI는 `--employee-name`(제공 IT팀 중 1명)과 `--login-id`를 명시한다. 비밀번호는 기존 `BOOTSTRAP_ADMIN_PASSWORD`에서만 읽는다. SESSION_SECRET 등 비밀값 누락이면 실패하고 로그에 값을 넣지 않는다. 김민지로 선택하는 예시는 고정된 첫 관리자 정책이 아니다.
4. 첫 관리자가 없는 빈 환경에서만 role=admin·is_active=true·must_change_password=true로 생성한다. 해시는 Argon2id를 사용하는 구현안이며 세션은 난수 원문을 쿠키에, 해시만 app.sessions에 저장한다. 재실행은 기존 계정 비밀번호/role을 바꾸지 않고 생성0건을 알린다. 관리자가 없는 비어 있지 않은 계정 집합의 복구는 H05 제안으로 구별한다.
5. 첫 관리자는 임시 비밀번호를 변경한 뒤 C01 관리자 API로 나머지 5명 계정을 발급한다. IT팀 직원은 admin, 나머지는 employee다. 발급 후 합계 users6명, admin2명·employee4명을 확인한다. 원문 비밀번호의 전달은 저장소·문서·캡처에 남기지 않는다.
6. bootstrap 완료 후 배포 비밀 저장소의 일회성 암호를 제거한다. 이후 서버 시작이 bootstrap 암호 존재를 매번 요구하지 않도록 명령 전용 필수값으로 검사한다. 첫 변경 차단·8시간 만료·회수·본인/최후 관리자 보호는 API §8 확정 기준으로 적용한다. 비밀번호 이력·잠금·외부OTP는 P2이며 추가 운영 제안의 상태만 구분해 전달한다.

세션 신원으로 app.users.is_active와 employees 관계를 매 요청 확인한다. `require_employee`/`require_admin` dependency를 모든 보호 경로에 적용한다. request_id의 소유자는 requester_id로 확인하며 UI에서 숨기기만 해서는 통과가 아니다. 서버의 내부 API 키는 직원 세션을 대체하지 않으며, 쿠키는 내부 API 인증을 대체하지 않는다.

## 7. DB·실행 환경 검증 요구

- 상세 생성 순서와 NULL/기본값/관계/권한은 [migrations 안내](../migrations/README.md)를 따른다. 마이그레이션은 빈 DB 적용→현재 head 확인→동일 head 재실행 무변경→볼륨 유지 재시작 검증 순이다. 데이터 seed와 DDL 이력을 분리한다.
- rag의 권한 없는 문서는 색인을 거부한다. exact cosine 조회의 WHERE 대상은 all 또는 all+it를 먼저 제한한다. 검색 후에만 걸러 LLM에 먼저 넘기지 않는다. 3071차원 삽입은 실패, 3072차원 삽입/조회는 성공해야 한다. 테스트 벡터로 DB 동작을 확인한 결과와 실제 모델 임베딩 품질을 혼동하지 않는다.
- [deploy 안내](../deploy/README.md)의 Docker/Compose 작업은 모두 예정이다. DB는 외부 기본 포트 공개 없음·healthcheck·named volume, 프록시는 브라우저 /api→backend:8000, 내부 서비스 주소를 브라우저 코드에 넣지 않는다.
- liveness는 프로세스 상태, readiness는 DB 접속·마이그레이션 head·vector 확장 적용을 검사하는 구현안이다. n8n 미연결은 외부 의존 장애로 별도 표시하고 DB 준비 완료와 혼동하지 않는다. 응답에 실제 접속 문자열/암호를 노출하지 않는다.

## 8. 검색 품질·처리시간 측정 절차 · BE-07

1. 유빈님은 기대 문서/절·권한·정상/근거없음/관리자전용을 표시한 동일 질문10개 이상을 준비한다. 백엔드는 확장 버전·schema head·모델3072·원본 hash·모드·대상 주소(비밀 제외)를 함께 기록하도록 지원한다.
2. 기본 정확 cosine/top_k=3을 고정하고 청킹 두 방식의 hit@3=기대 문서가 상위3개에 포함된 질문 수/정답 문서가 있는 질문 수를 비교한다. 근거 없는 질문은 별도 오답 수로 센다. 일반직원에게 it 청크가 나온 건수는 0이어야 한다.
3. 점수 임계값은 정상·근거없음 질문의 score 분포/잘못된 자동답변 사례를 보고 유빈님·다혁님이 제안하고 오현님이 공통 반영한다. `0.82` 예시나 임의 소요시간을 PASS 기준으로 정하지 않는다.
4. 서버는 동일 request_id에 대해 요청 수신/DB 저장/support 호출 시작·끝/응답 시각을 단조시계 ms로 측정한다. 전체 지연·HTTP 상태·route·재시도 수를 기록하고 질문·비밀번호·쿠키·키는 기록하지 않는다.
5. 실제 연결 후 동일 정상 요청을 최대5회로 측정해 표본수·개별시간·p50/p95와 계산 방식을 남긴다. 작은 표본 p95는 상위 관측값임을 밝힌다. 개발 중 호출 예산은 공유 키 한도에 맞춰 별도로 관리하며, Mock 지연과 실연결 지연을 분리한다. 최종 제출용 LLM 시나리오는 `--repeat 3`으로 **3회 반복**하고 회차별 결과를 모두 남긴다. 개발 중 호출 예산을 이유로 최종 반복 횟수를 줄이거나 일부 회차만 성공으로 집계하지 않는다. 400/401/403은 LLM 호출0도 확인한다.
6. 원민님이 제공 공통 사례의 `max_seconds` 등 원본 판정을 적용한다. 웹35초·support 연결3초/전체30초는 확정 초기 예산이며 관측된 성능 보장이 아니다. 실패는 원인·수정·같은 조건 재시험을 모두 남긴다.

## 참고

[전체 아키텍처](../../../docs/ARCHITECTURE.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [데이터·DB 기준](../../../docs/DATA-AND-DB.md) · [평가·검증 가이드](../../../docs/EVALUATION-GUIDE.md).
