# 오케퐁 공통 API·실행 계약 v0

각 담당자는 이 문서의 필드·응답·서비스 설정을 기준으로 구현한다. 기준대로 개발할 때는 별도 사전 협의가 필요 없다.
계약을 변경할 때만 [변경 절차](COORDINATION.md)를 따르며 공통 문서 수정은 오현님이 맡는다.
DB 구조는 [데이터·DB 기준](DATA-AND-DB.md), 역할·파일 소유권은 [팀 헌장](TEAM-CHARTER.md)을 따른다.

화면은 FastAPI만 호출하고, FastAPI는 세션으로 신원을 확인해 같은 oke-support를 호출한다. n8n은 검색·답변·검증·이관을 처리한다.
비밀값은 환경변수와 n8n Credential에만 둔다. 현재 구현·실행·시험은 진행 전이다.

## 1. 공통 웹훅 · FastAPI ↔ support (C02)

`POST /webhook/oke-support` 요청 필수: `request_id`, `user`, `question`. 선택: `channel`, `attempt`, `context`.

```json
{"request_id":"req-001","user":"박서연","channel":"web","question":"VPN이 계속 끊겨요","attempt":1}
```

응답은 `request_id`, `route`, `answer`, `sources`, `ticket`, `agents`, `security`를 포함한다. `route`는 `자동 답변`·`보완 질문`·`담당자 이관`·`권한 없음`·`차단` 중 하나다. 빈 질문·없는 직원·너무 긴 질문은 공통 계약의 HTTP 400과 `codes`를 따른다. 각 필드의 상세 형식과 시나리오 판정 기준은 [EVALUATION-GUIDE](EVALUATION-GUIDE.md) 3·4절을 기준으로 고정한다.

X-Team-Key 인증을 사용하고 user는 제공 직원 name과 일치시킨다.
공통 응답 필드·route는 표준 계약 그대로 유지한다. 웹과 공통 시험은 같은 support를 호출한다.
request_id는 한 논리 요청의 재시도에 재사용하며 새 보완 답변 차례에는 새 ID와 증가한 attempt/context를 전달한다.
웹 request_id 소유권은 FastAPI가 확인한다. 공통 직접 시험은 팀 웹훅 인증과 제공 직원 확인을 따른다.

## 2. 화면 ↔ FastAPI (C01)

| API | 요청 | 응답 | 권한 |
| --- | --- | --- | --- |
| `POST /api/auth/login` | `login_id`, `password` | `{user:{id,name,dept,role,must_change_password}}` + `oke_session` 쿠키 | 공개 |
| `POST /api/auth/logout` | 세션 쿠키 | `{ok:true}` | 로그인 |
| `GET /api/auth/me` | 세션 쿠키 | `{id,name,dept,role,must_change_password}` | 로그인 |
| `POST /api/auth/change-password` | `current_password`, `new_password` | `{ok:true,must_change_password:false}` | 로그인 |
| `POST /api/ask` | `question`, 선택 `request_id`, `attempt`, `context` | 공통 웹훅 응답 전체 | 로그인 |
| `GET /api/my-requests` | 세션 쿠키 | `{items:[...]}` (본인의 문의·답변·티켓 상태 목록) | 로그인 |
| `GET /api/admin/tickets` | 세션 쿠키 | `{items:[...]}` (이관 티켓·긴급도·담당자·상태 목록) | IT팀 관리자 |
| `PATCH /api/admin/tickets/{id}` | `status`, 선택 `assignee`, `reply` | 변경된 티켓 객체 (`{id}`는 내부 PK, `ticket_id`는 `T-2001` 표시 번호, `assignee`는 IT팀 직원 `app.employees.id` 정수 또는 `null`) | IT팀 관리자 |
| `GET /api/admin/employees` | 세션 쿠키 | `{items:[{id,name,dept,user_id}]}` (제공 6명 및 발급 연결 상태) | IT팀 관리자 |
| `GET /api/admin/users` | 세션 쿠키 | `{items:[{id,employee_id,login_id,name,dept,role,is_active,must_change_password}]}` | IT팀 관리자 |
| `POST /api/admin/users` | `employee_id`, `login_id`, `temporary_password` | 생성된 계정 요약 (HTTP 201) | IT팀 관리자 |
| `PATCH /api/admin/users/{id}` | `is_active` | 변경된 계정 요약 (본인·마지막 활성 관리자 비활성화 거절) | IT팀 관리자 |
| `POST /api/admin/users/{id}/reset-password` | `temporary_password` | `{ok:true,must_change_password:true}` | IT팀 관리자 |
| `GET /api/admin/alerts` | 세션 쿠키 | `{items:[{id,ticket_id,workflow,node,message,severity,created_at}]}` | IT팀 관리자 |

`POST /api/ask`에서 `request_id`가 없으면 FastAPI가 생성하고 로그인한 `user`를 넣어 n8n에 보낸다. 동일 요청 재시도에는 앞서 받은 `request_id`를 다시 보낸다. 첫 관리자 계정은 환경변수로 최초 1회 생성하고, 관리자가 나머지 계정을 발급한다. 공개 회원가입은 없다.

user·dept·role은 화면 입력을 믿지 않고 세션에서 서버가 정한다.
로그인 성공은 user 요약(id,name,dept,role,must_change_password)과 HttpOnly 세션 쿠키, 로그아웃은 ok=true로 한다.
웹 질문의 성공 응답은 공통 웹훅 응답 전체(request_id,route,answer,sources,ticket,agents,security 및 필요 시 reason/timings)를 보존한다.
목록은 {"items":[]} 형식, 단건 생성/변경은 해당 객체로 반환한다.
웹 오류 기본 형태는 {"error":{"code":"forbidden","message":"접근 권한이 없습니다."}}다.
공통 웹훅의 HTTP400 codes는 웹 오류 형태로 바꾸지 않고 그대로 유지한다.
실제 비밀번호는 응답/로그/캡처에 넣지 않는다.

## 3. support ↔ search (C03)

POST /webhook/oke-search, X-Team-Key 인증.
입력 예시:
```json
{"request_id":"req-001","query":"VPN 연결 오류","type":"network","access_levels":["all"],"top_k":3}
```
정상/검색 없음은 HTTP200, {"ok":true,"evidence":[{"doc":"remote-work-vpn","section":"접속 오류","text":"근거 청크 내용","score":0.82}],"reason":null}로 반환한다.
검색 없음은 evidence=[]이고 reason=no_evidence다. 예시 score는 실행 측정값이 아니다.
장애는 HTTP503, {"ok":false,"evidence":[],"reason":"search_unavailable"}로 반환하고 본체가 이관한다.
access_levels는 본체가 직원 부서 조회로 검증해 만든 all 또는 all+it 목록이다. 질문 본문 주장을 사용하지 않는다.
pgvector 저장·점수 정의는 [DATA-AND-DB](DATA-AND-DB.md)를 따른다.

## 4. support ↔ handoff (C04)

POST /webhook/oke-handoff, X-Team-Key 인증.
입력: request_id, requester(제공 직원 이름), title, category, priority(normal/high), reason. 선택 evidence_summary.
정상은 HTTP200:
```json
{"ok":true,"ticket":{"ticket_id":"T-2001","priority":"normal","duplicate":false},"reason":null,"alerted":true,"dlq":false}
```
티켓 장애는 처리 결과로 HTTP200, ok=false·ticket=null·reason=tickets_down·alerted/dlq는 실제 성공 여부를 적는다.
알림만 실패했으면 생성된 ticket을 유지하고 reason=alerts_down으로 표시한다. 재시도로 티켓을 다시 생성하지 않는다.
본체는 최종 route를 담당자 이관으로 유지하고 ticket/사유를 공통 응답에 매핑한다.
Error Workflow는 예상 밖 실행 실패를 별도로 처리한다.

## 5. handoff ↔ 저장 API (C05)

| API | 요청 핵심 값 | 응답 핵심 값 | 저장 |
| --- | --- | --- | --- |
| `POST /tickets` | `key`(=`request_id`), `title`, `requester`, `category`, `priority` | `ticket_id`, `duplicate` | PostgreSQL 티켓 |
| `POST /alerts` | `workflow`, `node`, `message`, `severity`, 선택 `ticket_id`, `event_key` | `stored`, `count` | PostgreSQL 알림 |
| `POST /dlq` | `request_id`(nullable), `workflow`, `node`, `reason`, `safe_payload`, 선택 `execution_ref` | `stored`, `count` | PostgreSQL DLQ |

중복 `key`는 새 티켓을 만들지 않고 기존 티켓을 반환한다. n8n 내부 호출은 별도 인증을 적용한다. 제공 data-api의 직원·기존 티켓·규정 조회는 정해진 계약을 사용한다.

신규는 HTTP201 {"ticket_id":"T-2001","duplicate":false}, 중복은 HTTP200에 같은 ticket_id와 duplicate=true.
handoff가 원래 priority를 ticket 객체에 붙인다. /tickets 응답에 priority가 항상 있다는 가정을 하지 않는다.
POST /alerts는 workflow,node,message,severity와 선택 ticket_id, event_key를 받고, 공통 호환 알림 저장 응답은 HTTP200 {"stored":1,"count":1}이며 count는 실제 누적 수다. 웹 관리자 목록은 C01의 /api/admin/alerts에서 제공한다.
FastAPI 내부 API는 X-Api-Key 인증을 사용하며 웹 로그인 쿠키와 구별한다.
운영 새 업무 기록은 PostgreSQL, 공통 고장 시험 모드는 data-api에 연결한다. 설정으로 선택하고 같은 티켓을 양쪽에 동시 생성하지 않는다.
fault/reset/ops와 실제 호출 대상이 맞는지 원민님이 확인한다.

## 6. RAG ↔ PostgreSQL+pgvector (C06)

[DATA-AND-DB](DATA-AND-DB.md)의 app/rag 테이블 기준을 따른다.
지혜님이 마이그레이션·확장·접속 설정을, 유빈님이 청킹·임베딩·색인·검색을 구현한다.
vector 차원·모델·메타데이터를 새로 협의하느라 시작을 기다리지 않고 기본안을 적용한다.
변경이 필요한 경우에만 C06으로 요청한다. 검색 신뢰도 임계값은 실측 후 기준에 반영한다.

## 7. 실행 환경 (C07)

Compose 파일 위치: develop/jihye/deploy/compose.yaml.
기본 서비스명 frontend/backend/postgres/n8n/data-api, 내부 주소는 backend:8000·postgres:5432·n8n:5678·data-api:8800.
브라우저는 frontend:3000이 아닌 localhost 또는 VM 공개 웹 주소를 사용하고 /api를 프론트 서버 프록시로 backend에 전달한다.
브라우저 코드에 Docker 내부 호스트명을 쓰지 않는다.
공개 웹 포트 기본 3000, 로컬 개발 backend 8000·n8n 5678·data-api 8800. postgres는 내부5432, 외부 공개를 기본으로 하지 않는다.
PostgreSQL은 pgvector를 포함한 이미지, named volume과 healthcheck를 사용한다. 이미지 실제 버전·digest는 지혜님이 설치 검증 뒤 고정한다.
Compose build context는 backend=.., frontend=../../sueon.
공통 환경변수 이름은 DATABASE_URL, N8N_WEBHOOK_URL, N8N_WEBHOOK_KEY, INTERNAL_API_KEY, DATA_API_URL, DATA_API_KEY, SERVICE_MODE, SESSION_SECRET, BOOTSTRAP_ADMIN_PASSWORD, BACKEND_ORIGIN이다.
SERVICE_MODE는 practice 또는 app이며 DB/관측 모드가 혼동되지 않게 README에 기록한다. BACKEND_ORIGIN은 프런트 서버 프록시가 호출할 백엔드 주소(로컬 http://127.0.0.1:8000, Compose http://backend:8000)이며 브라우저 공개 변수로 노출하지 않는다.
실제 환경값은 Git에 넣지 않는다. 기존 n8n/data-api를 재사용하면 동일 네트워크 연결과 충돌 포트를 지혜님이 조정해 기록한다.
전체 배포·VM 환경 반영은 오현님 담당이다.

## 8. 오류·인증·변경 원칙

| 상황 | 처리 |
| --- | --- |
| 잘못된 입력 | HTTP 400, 필드별 오류 코드 |
| 로그인하지 않음·로그인 실패 | HTTP 401 |
| 다른 직원의 문의·관리자 API 접근·첫 비밀번호 미변경(`password_change_required`) | HTTP 403, 데이터 노출 없음 |
| 없는 티켓·계정 | HTTP 404 |
| 중복 계정·동일 키 본문 충돌·마지막 관리자/본인 비활성화 거절 | HTTP 409 (또는 400 `error.code` 병행 안내) |
| n8n 시간 초과(`504`)·연결 장애(`503`) | 화면에 정해진 안내, 서버에는 개인정보를 가린 오류 기록 |

세션은 브라우저 스크립트가 읽지 못하는 `oke_session` 쿠키(`HttpOnly`, `SameSite=Lax`, `Path=/`, 기본 8시간)로 관리한다. `must_change_password=true`인 동안에는 `/api/auth/me`, `/api/auth/change-password`, `/api/auth/logout`만 허용하고 나머지 보호 API는 403 `password_change_required`를 반환한다. 비밀번호 변경·초기화·비활성화 시 기존 세션을 폐기한다.
비밀번호 필수 검증 범위(P0/P1)는 서버 기준 최소 12자, 영문 대/소문자·숫자·특수문자 중 3종 이상 조합, 본인 이름/로그인 ID 포함 금지로 고정한다(이력 테이블·잠금·외부 OTP는 P2 선택 범위로 분리).
초기 호출 시간 예산(실측 전 기본값)은 브라우저→FastAPI 35초(자동 재전송 금지), FastAPI→`oke-support` 연결 3초·전체 30초(자동 재시도 0회), `oke-support`→조회 2초·`oke-search` 4초·`oke-handoff` 5초(내부 티켓 저장 최대 2회·각 1초, 알림/DLQ 각 1회·0.6초)로 시작하고 실측 후 조정한다.

기준대로 구현하고 상대 서비스가 없으면 같은 계약의 Mock을 사용한다. 실제 연결은 제공자 준비 뒤 확인한다.
변경이 필요하면 자기 HANDOFF에 변경안·이유·영향·기존/새 입출력을 적고 지정 상대 검토 후 오현님이 공통 기준을 갱신한다.
실제 호출 대상과 fault/reset/ops 관측 대상의 일치를 원민님이 확인한다. 시험 모드와 FastAPI 저장 모드를 구별하고 양쪽에 같은 티켓을 동시 생성하지 않는다.
