# 개발 연결 기본안 v0

> 이 문서는 팀 공통 연결 기준 v0이다. 각 담당자는 아래 요청·응답·DB·실행 설정대로 구현한다. 변경할 때만 COORDINATION.md의 담당자와 검토 후 오현님에게 반영을 요청한다.

## C01 · 화면 ↔ FastAPI

기존 [API-CONTRACT](API-CONTRACT.md)의 경로와 필드명을 유지한다.
로그인 입력은 login_id/password, /api/ask 입력은 question/request_id/attempt/context다.
user·dept·role은 화면 입력을 믿지 않고 세션에서 서버가 정한다.
로그인 성공은 user 요약(id,name,dept,role,must_change_password)과 HttpOnly 세션 쿠키, 로그아웃은 ok=true로 한다.
웹 질문의 성공 응답은 교사 공통 응답 전체(request_id,route,answer,sources,ticket,agents,security 및 필요 시 reason/timings)를 보존한다.
목록은 {"items":[]} 형식, 단건 생성/변경은 해당 객체로 반환한다.
웹 오류 기본 형태는 {"error":{"code":"forbidden","message":"접근 권한이 없습니다."}}다.
교사 웹훅의 HTTP400 codes는 웹 오류 형태로 바꾸지 않고 그대로 유지한다.
관리 API 경로: PATCH /api/admin/users/{id}(is_active), POST /api/admin/users/{id}/reset-password(temporary_password), GET /api/admin/alerts.
실제 비밀번호는 응답/로그/캡처에 넣지 않는다.

## C02 · FastAPI ↔ support

POST /webhook/oke-support, X-Team-Key 인증, user는 제공 직원 name과 일치시킨다.
예시: {"request_id":"req-web-001","user":"박서연","question":"VPN이 끊겨요","channel":"web","attempt":1}
공통 응답 필드·route는 교사 계약 그대로 유지한다. 웹과 공통 시험은 같은 support를 호출한다.
request_id는 한 논리 요청의 재시도에 재사용하며 새 보완 답변 차례에는 새 ID와 증가한 attempt/context를 전달한다.
웹 request_id 소유권은 FastAPI가 확인한다. 공통 직접 시험은 팀 웹훅 인증과 제공 직원 확인을 따른다.

## C03 · support ↔ search

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

## C04 · support ↔ handoff

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

## C05 · handoff ↔ 저장 API

수업 data-api 호환 POST /tickets 입력은 key,title,requester,category,priority.
신규는 HTTP201 {"ticket_id":"T-2001","duplicate":false}, 중복은 HTTP200에 같은 ticket_id와 duplicate=true.
handoff가 원래 priority를 ticket 객체에 붙인다. /tickets 응답에 priority가 항상 있다는 가정을 하지 않는다.
POST /alerts는 workflow,node,message,severity와 선택 ticket_id를 받고, 수업 호환 알림 저장 응답은 HTTP200 {"stored":1,"count":1}이며 count는 실제 누적 수다. 웹 관리자 목록은 C01의 /api/admin/alerts에서 제공한다.
FastAPI 내부 API는 X-Api-Key 인증을 사용하며 웹 로그인 쿠키와 구별한다.
운영 새 업무 기록은 PostgreSQL, 공통 고장 시험 모드는 data-api에 연결한다. 설정으로 선택하고 같은 티켓을 양쪽에 동시 생성하지 않는다.
fault/reset/ops와 실제 호출 대상이 맞는지 원민님이 확인한다.

## C06 · RAG ↔ PostgreSQL+pgvector

[DATA-AND-DB](DATA-AND-DB.md)의 app/rag 테이블 기준을 따른다.
지혜님이 마이그레이션·확장·접속 설정을, 유빈님이 청킹·임베딩·색인·검색을 구현한다.
vector 차원·모델·메타데이터를 새로 협의하느라 시작을 기다리지 않고 기본안을 적용한다.
변경이 필요한 경우에만 C06으로 요청한다. 검색 신뢰도 임계값은 실측 후 기준에 반영한다.

## C07 · 실행 환경

Compose 파일 위치: develop/jihye/deploy/compose.yaml.
기본 서비스명 frontend/backend/postgres/n8n/data-api, 내부 주소는 backend:8000·postgres:5432·n8n:5678·data-api:8800.
브라우저는 frontend:3000이 아닌 localhost 또는 VM 공개 웹 주소를 사용하고 /api를 프론트 서버 프록시로 backend에 전달한다.
브라우저 코드에 Docker 내부 호스트명을 쓰지 않는다.
공개 웹 포트 기본 3000, 로컬 개발 backend 8000·n8n 5678·data-api 8800. postgres는 내부5432, 외부 공개를 기본으로 하지 않는다.
PostgreSQL은 pgvector를 포함한 이미지, named volume과 healthcheck를 사용한다. 이미지 실제 버전·digest는 지혜님이 설치 검증 뒤 고정한다.
Compose build context는 backend=.., frontend=../../sueon.
공통 환경변수 이름은 DATABASE_URL, N8N_WEBHOOK_URL, N8N_WEBHOOK_KEY, INTERNAL_API_KEY, DATA_API_URL, DATA_API_KEY, SERVICE_MODE, SESSION_SECRET, BOOTSTRAP_ADMIN_PASSWORD다.
SERVICE_MODE는 practice 또는 app이며 DB/관측 모드가 혼동되지 않게 README에 기록한다.
실제 환경값은 Git에 넣지 않는다. 기존 수업 n8n/data-api를 재사용하면 동일 네트워크 연결과 충돌 포트를 지혜님이 조정해 기록한다.
전체 배포·VM 환경 반영은 오현님 담당이다.

## 변경·검증

기본안을 그대로 적용하는 구현은 상대의 사전 동의를 기다리지 않는다.
실제 상대 기능이 아직 없으면 위 예시 Mock으로 구현하고 실제 연결 검증은 제공자 준비 뒤 수행한다.
기본안과 다른 이름·필드·스키마·모델·포트가 필요할 때만 자기 HANDOFF→지정 상대 검토→오현님 기준 갱신을 거친다.
키트 업데이트의 계약 차이·설치 불가능·호환 오류는 근거를 첨부해 변경 요청한다.
