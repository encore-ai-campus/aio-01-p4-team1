# 지혜님 · 변경 제안·전달 기록

[README](../README.md) → [TODO](TODO.md) → [SPEC](SPEC.md) → [IMP-PLAN](IMP-PLAN.md)을 기준으로 바로 개발한다. 이 파일은 **공통 기준의 누락 정책/변경 제안과 연결 검토·전달 결과**를 기록한다. 기존 기준을 적용하기 위한 사전 승인 목록이 아니다.

초안 작성: 2026-11-03. 현재 상태 갱신: 2026-11-05. 현재 적용 기준은 SPEC 1절, 작업 범위는 IMP-PLAN을 따른다. 사용자에게 전달받은 상대 회신·로컬 검증·공통 문서 반영·실연결은 구분한다. 에이전트의 외부 메시지 전송은 없으며, 답변 없음은 동의가 아니다. 아래 과거 제안의 당시 상태는 현재 기준을 덮어쓰지 않는다.

## 연결과 상태

### 팀장 요청 · VM 0004 및 RAG 로그인 인계

사용자가 전달한 오현님 요청: 팀 VM PostgreSQL에 마이그레이션0004 적용, LOGIN `oke_rag_user` 생성 후 유빈님에게 연결 정보 인계. VM 작업 위임으로 수신했으며 실제 적용/계정 생성/외부 인계는 아직 미실행이다. 로컬 P0-7 커밋은 f7b81da이고 로컬 최신 revision0005(readiness SELECT grant)는 이번 요청0004와 구분한다. VM이 이미0005라면 downgrade하지 않고 보고한다.

진행 전 필요한 정보는 VM SSH 주소·사용자·포트/키 위치 또는 승인된 실행 터미널, 대상 PostgreSQL 컨테이너/DB와 관리자 설정 위치, 유빈님 접속 비밀 전달 경로다. 현재 조회한 문서에 해당 접속 정보가 없고 로컬 SSH config도 없어 사용자에게 요청했다. 비밀 원문을 채팅에 요구하지 않는다. 대상 확인 후 기존 revision/객체·백업 필요 여부 확인→0004 적용/대조→LOGIN과 RAG 색인 역할 연결→실제 로그인/허용·거절 검증→접속 경로를 승인된 비밀 전달 방식으로 인계한다. 별도 검색 LOGIN의 조회 전용 분리와0005 적용 여부는 후속 인계에 구분해 남긴다.

P0-7 인계: 로컬 DB/backend 이미지 빌드·UID10001·별도LOGIN·readiness를 확인했다. 전체188개 통과·기존 경고1건, 실제 DB중지ready503/live200·재기동ready200. 0005에서 oke_app의 Alembic 이력 SELECT만 추가했으므로 기존 P0-5 인계0004에0005를 더해 적용해야 한다. 기존 DB와 n8n/data-api는 변경하지 않았고 frontend는 빌드파일 미준비다. 오현님께 VM 네트워크/LOGIN/비밀 주입·0005·기동순서·database health 범위를, 유빈님께 RAG LOGIN/실원본 준비 후 연결을, 수언님께 frontend/프록시 준비 후 연결을 인계한다. 다혁님 C03 경로/신원 회신은 전달 근거이며 실제 HTTP 검증으로 바꾸지 않는다. VM 배포·AI 실통합·로그인은 미실행이다. 상세 재현은 deploy/README의 P0-7 절이다. 외부 전송 없음.

P0-6 인계: 직원6명 검증/적재와 IT직원 첫 관리자 CLI를 구현하고 전체180개·실제 bootstrap DB6개 검증을 통과했다. 실제 DB 검증 자료는 rollback했으며 실원본 수집·상시 계정 생성·VM 실행은 미실행이다. 오현님께 VM 대상/원본 employees 응답 및 인증 확인 뒤 seed→6명대조→선택 IT직원 bootstrap→일회성 암호 제거 순서를 전달한다. 현재 직원 어댑터의 `{employees:[...]}`는 Mock 지원 형태이며 실제 계약으로 확정하지 않는다. 세션·로그인·첫 변경·나머지 계정 발급은 P1-1이다. 이전 VM 인계 문서 변경은 보존했으며 외부 전송·상대 동의는 주장하지 않는다.

VM 인계 보완: 사용자가 전달한 팀장 로드맵은 팀 VM에서 RAG 실통합을 진행하는 방향이다. 유빈님 회신은 VM Python 색인/검색의 DB 직접 접속, n8n의 Python HTTP 호출 구조다. 실제 VM DB·LOGIN 계정·접속 경로·문서 최종 범위·OpenAI 승인 확인은 대기 중이며 VM 적용으로 처리하지 않는다. 적용 전 확인·명령·권한/비밀 인계·시험 순서를 [deploy VM 인계](../deploy/README.md#vm-인계--오현님-수행)에 보완했다. 기존 IMP-PLAN 단계의 요구사항은 유지하고 실통합 순서만 연결한다.

P0-5 갱신(2026-11-05): 전용 DB에 `0004 (head)` 적용, RAG 문서/청크와 `vector(3072)`, 0부터 시작하는 청크 번호, JSONB metadata 및 역할별 ACL을 실측했다. 전체158개 통과·기존 경고1건. 유빈님에게는 실제 DDL·NOLOGIN 역할 이름·권한 경계와 가상 벡터 정확 검색 결과를 전달할 수 있다. 실제 Index/Search 연결에는 별도 LOGIN 자격증명(오현님 비밀 관리), 실제 원본 API 응답·인증, 임베딩/재색인 검증이 남는다. 다혁님 C03 권한 전달·입력 오류 계약은 유빈님 제안과 오현님 공통 확정 뒤 대조한다. 상대 보고를 실연결 증거로 바꾸지 않았으며 외부 전송은 하지 않았다.

P0-4 갱신(2026-11-05): 전용 검증 DB에 `0002 (head)`를 적용해 vector 확장·app/rag 스키마·업무 테이블 7개와 제약을 확인했다. 아래 P0-3 당시의 'DDL 없음' 표기는 실행 이력이다. RAG 테이블/권한·업무 API 실제 저장은 아직 후속이다. 유빈님이 전달한 P0-2 청크 필드(`doc_key`, 0부터 시작하는 `chunk_no`, `section`, `content`, `content_hash`, 길이 및 `metadata`)는 P0-5 매핑 입력이며, `complete/partial/rejected`는 청킹 준비 상태로 DB 필수 컬럼이 아니다. 유빈님께 P0-5 완료 뒤 실제 DDL/접속 권한과 검증 결과를 전달한다. 원민님께는 `tickets.request_key`, `alerts.event_key` 고유 제약과 nullable inquiry, DLQ 구조를 전달하되 API ACK/동시 저장은 실제 연결 후 확인한다. 오현님께는 적용 revision·격리 DB 검사 결과를 전달한다. 외부 메시지 전송·상대 확인은 수행하지 않았다.

| 연결 | 검토 상대 | 상태 |
| --- | --- | --- |
| C01 | 수언님·오현님 | H01·03·05 핵심(세션 쿠키·관리자 목록·assignee=employees.id·최후 관리자 보호) 공통 반영 완료, H02 세부 제안 유지·실연결 미실행 |
| C02 | 다혁님·오현님 | 시간 예산·503/504 확정. 응답 캐시/상태·추가 오류코드 등 H04 세부와 H03 nullable 타입은 미확정, 실제 연결 미실행 |
| C05 | 원민님·오현님 | 기존4bbbf49 요청7/7 적합 회신 수신. H07 알림 duplicate 유지·DLQ200 팀장 승인 전달받음. 공통 반영 커밋·모델 확장·실제 저장/동시성은 미확인/후속 |
| C06 | 유빈님 | P0-3 실제 DB 접속·vector 가용성 확인. DDL·활성화·grants·실제 색인은 P0-4~5 이후. data-api 응답/인증 및 청크 상태의 DB 저장 필요 여부 추가 확인 |
| C07 | 오현님·영향받는 담당 | 전용 Compose DB 기동·health·접속·Alembic 기반 확인. 기존 서비스 미변경·호스트 DB포트 미공개. backend/전체Compose/VM은 미실행 |

## 현재 확정 기준과 옛 제안의 관계

로컬 공통 기준 대조 커밋은db14b79이며 [SPEC 1절](SPEC.md#1-적용할-기준--새로-선정하지-않음)에 구현용 기준을 모았다. 공통 원문은 읽기만 했고 원격 최신 조회는 하지 않았다.

| 과거 항목 | 현재 기준 | 남은 제안 |
| --- | --- | --- |
| H01 | 쿠키 oke_session/HttpOnly/SameSite=Lax/Path=/·8시간, 첫 변경 제한·세션 회수 확정 | 새 세션 재발급·Origin 검사 등 추가 운영 세부. 옛 Path=/api는 적용하지 않음 |
| H02 |12자·3종·본인 이름/로그인ID 포함 금지는P0/P1, 이력·잠금·외부OTP는P2 | 옛 회사명 금지·90일·이력/잠금 컬럼을 필수 스키마에 추가하지 않음 |
| H03 | 계정 생성201·목록·직원ID·assignee·context최대2000 확정 | 목록 DTO·patch 생략/null·추가 입력 거절/코드·Security nullable 세부 |
| H04 | 연결3초·전체30초·재시도0, 장애503/504·같은키 본문 충돌 거절 확정 | 처리중 응답·상태·캐시/복구·추가 오류 필드. 캐시와WF-09 duplicate 판정은 대조 필요 |
| H05 | 본인/마지막 활성 관리자 비활성화 거절 확정 | 관리자 부재 계정집합 복구 등 추가 운영 세부 |
| H06 | POST /dlq·alerts.event_key 확정 | DLQ 기본 API 구현을 승인 대기로 남기지 않음. ACK 세부는H07 |

## 현재 인계 패키지 · 2026-11-05

P0-2 보완 기준은 fdcd265이며 origin/feat/jihye-p0와 같은 해시임을 직접 원격 조회했다. 이번 P0-3은 아직 로컬 변경이며 새 커밋 생성 후 공유 기준을 갱신한다. 아래는 전달 가능한 자료를 정리한 것이며, 실제 메시지 전송이나 이번 단계의 상대 재확인은 수행하지 않았다.

| 대상 | 전달 파일·내용 | 확인 요청 / 현재 경계 |
| --- | --- | --- |
| 수언 C01 | `/openapi.json`·`/docs`, `tests/test_api_models.py`의 웹14개 요청/응답 | 목록 단건·관리자 답변/상태가 내 문의에 표시되는 DTO·patch 의미 대조. 실제 로그인/저장501, Mock은tests 내부 |
| 다혁 C02 | `app/schemas/support.py`, `tests/conftest.py`, `tests/test_support_contract.py` | fixture 신원→user·web 채널·5 route·400codes·context≤2000·nullable security 대조. 실제세션/HTTP는P1 |
| 원민 C05 | `app/schemas/tickets.py`·`alerts.py`, `tests/test_api_models.py`, 아래 저장 예시 | 기존요청7/7 회신 수신. 알림duplicate·DLQ상태 명문화는H07, 신규/중복/동시·부분실패는 실제DB 후 확인 |
| 유빈 C06 | SPEC DB기준, migrations/README와 IMP-PLAN P0-3~5 | 원본 API구조/인증 미확인. DB준비 뒤head·3072차원·grants·거래/복원검증 공유. 현재는DDL/DB없음 |
| 오현 C07/C09 | 본 계획/실행기록·H07·DAY80 반영안 | data-api 키트/인증 설정 위치·공통ACK 반영 요청. 비밀값은 문서로 전달하지 않음 |

세션→user 예시(시험 fixture): 웹 요청 `{"question":"문의","request_id":"req-fixture"}`와 fixture 직원 박서연을 `{"request_id":"req-fixture","user":"박서연","question":"문의","channel":"web","attempt":1}`로 변환한다. 화면이 넣은 이름/부서/역할은 사용하지 않는다. 실제 로그인 세션 구현 증거가 아니다.

공통 정상 fixture는 `tests/conftest.py`의 support_payload를 사용한다. 필수request_id/route/answer/sources/ticket/agents/security를 모두 포함하고, 시험에서5 route·선택reason/timings·추가필드 보존과 `{"codes":["question_required"]}`400 전달을 확인한다. 티켓 번호는 합성값이며 접수 사실이 아니다.

저장 API 예시(모두 시험용 형식, 인증 키 값은 포함하지 않음):

```json
{"key":"req-fixture","title":"합성 문의","requester":"박서연","category":"network","priority":"normal"}
```

위 `/tickets` 신규 응답은201 `{"ticket_id":"T-2001","duplicate":false}`, 중복은200과 같은ticket_id·duplicate=true다. priority는 응답에 없어도 원민님이 원래 값을 유지한다.

```json
{"workflow":"oke-handoff","node":"ticket","message":"합성 저장 확인","severity":"high","event_key":"evt-fixture"}
```

위 `/alerts`의 현재 공통 응답은200 `{"stored":1,"count":1}`다. 아래H07의 duplicate 확장은 아직 적용하지 않았다. `/dlq`는 request_id 키 필수·null 허용, workflow/node/reason/safe_payload 필수·execution_ref 선택이며 현재 로컬200+StoredResponse다. safe_payload는 비밀/개인정보 제거가 필요하고 실제 저장 검사는P1이다.

## JH-H07 · C05 알림 ACK·DLQ 상태 명문화 검토

**현재 상태: 사용자 전달로 팀장 승인 수신(알림 duplicate 필드 유지·DLQ HTTP200).** 로컬 공통 API의 명문화 커밋은 아직 확인되지 않았고 모델/실제 저장 반영은 후속이다. 프론트 최종 연결은 팀장이 맡으며 지혜님은 P0-3 DB 기반에 집중하라는 방향도 전달받았다. 아래 제안 설명은 승인 전 검토 배경으로 보존하며 ‘미확정’은 승인 전 당시 상태로 읽는다.

- 출처: 사용자가 전달한 원민님 회신. 대조 대상4bbbf49, 요청 표본7/7 적합(티켓3·알림2·DLQ2). 직접 상대코드 조회/재실행은 하지 않았다.
- 발견: StoredResponse는 duplicate를 직렬화하지 않아 원민님이 중복알림 성공을 확인하지 못하고 alerts_down으로 판정할 수 있다. DLQ의 현재로컬200과 원민SPEC 신규201 기대가 다르며 공통API§5는DLQ상태코드를 명시하지 않았다.
- 검토 의견/제안: 알림 전용 AlertStoredResponse로 분리해 duplicate:bool=False를 추가하고, DLQ는HTTP200+저장ACK검증으로 명문화하는 방향. 모델기본값이 중복확인 증거는 아니며 실제DB가 같은event_key의 기존저장을 확인할 때만duplicate=true다.
- ACK 제안: 신규 `{"stored":1,"count":5,"duplicate":false}`, 같은event_key기존저장 `{"stored":0,"count":5,"duplicate":true}`를 alerted=true로 해석. 누적count만으로 성공추정 금지. event_key없는요청·동일키변경본문·practice저장소ACK호환성은 함께 확인해야 한다.
- 반영 상대/순서: 원민님·지혜님 C05검토 → 오현님 공통계약 명시 → 지혜님 P0-2모델/Mock 보완 및 P1-3실제저장 → 원민SPEC/신규·동일키·동시 재시험. 공식공통반영·실연결은 미확인이다. 현재모델/코드는 확장하지 않았다.
- 차단 범위: ACK확장에 의존하는 성공판정만 미확정이다. P0-3~5확정DB기반과 기본DLQ구현은 이 제안 때문에 중단하지 않는다.

## P0-3 인계·확인·공유 · 2026-11-05

### 공통으로 전달할 현재 상태

전용 PostgreSQL 기동·접속·Alembic 기반은 준비됐다. PostgreSQL16.15·사용 가능한 vector0.8.6, digest 고정 이미지·named volume·health·호스트 포트 미공개를 확인했다. 전체114개 통과 중 실제 DB 시험은5개이며 나머지는 모델/Mock/기반 시험이다. app/rag 스키마·vector 활성화·업무/RAG 테이블·계정/grants·업무 API 저장은 아직 없다. P0-4→P0-5가 실제 저장 연결의 다음 전제다.

초기 호스트 접속 시간 초과와 검증 컨테이너의 /tmp 누락은 수정 후 재시험했다. 첫 traceback에 나온 자동생성 검증용 암호는 교체했고 이후 출력 마스킹과 회귀 시험을 추가했다. 비밀값을 공유 자료에 넣지 않는다. 전용 DB는 healthy로 남기고 볼륨을 유지했으며 기존 DB/n8n/data-api는 변경하지 않았다.

### 상대별 전달 자료와 확인 요청

| 대상 | 지금 전달할 것 | 상대에게 확인할 것 | 후속 연결 시점 |
| --- | --- | --- | --- |
| 오현님 | compose.yaml/check.yaml, deploy/README, IMP-PLAN의 실제 명령·실패/재시험·버전. 기존5432/55432 충돌 회피 및 포트 미공개 | 기존 n8n/data-api와 이후 네트워크 연결 방식, 실제 data-api 키트/읽기 인증 설정 위치, C05 승인 내용 공통 반영 커밋 | P0-4/5와 전체 배포 전. 팀 VM/프론트 최종 연결은 오현님 |
| 유빈님 | DB 접속 기반 완료·vector0.8.6 가용, migrations/README의 rag DDL/3072차원/권한 계획 | 청크 매핑·문서 단위 거래 요구, complete/partial/rejected의 DB 저장 필요 여부, 재색인 실패/권한 축소와 복원 후 대조 방법 | RAG 테이블·index/search 권한은 P0-5 이후. 현재 migration 관리자 접속을 RAG 런타임에 공유하지 않음 |
| 다혁님 | fdcd265 C02 모델/fixture와 P0-3 접속 기반 완료 상태. 아직 업무 API501임을 함께 안내 | 공통 응답·nullable security·context2000자·timeout/400 대응, 원민님 C04 응답과의 대조 결과 | 실제 support 클라이언트는 P1-2, 저장은 원민 C05 경유. 다혁님에게 직접 DB 접근을 새로 요구하지 않음 |
| 원민님 | 요청7/7 회신·C05 승인 수신 기록, 실제 저장은 미구현이라는 상태 | 승인된 duplicate ACK의 신규/동일키/동시·event_key없는 요청·practice 호환성, DLQ200의 저장ACK 판정 | 모델 확장 보완을 별도로 연결하고 P1-3에서 실제 DB UNIQUE·건수·티켓보존을 재시험 |
| 수언님 | fdcd265 OpenAPI/웹 예시. 팀장 최종 프론트 연결 방향 | 업무 API가 아직501임을 인지하고 화면 모델/예시의 차이만 전달 | 실제 로그인P1-1·문의P1-2·관리자처리P1-3 뒤 오현님 통합 |

### 팀장에게 전달할 문안

> P0-3 DB 컨테이너·실제 접속·마이그레이션 기반까지 확인했습니다. PostgreSQL16.15·pgvector0.8.6 가용성을 확인했고 기존 DB 포트는 건드리지 않았습니다. 전체114개 시험이 통과했고 그중 실제 DB 시험은5개입니다. 아직 테이블은 없어서 다음 P0-4에서 업무 테이블·확장, P0-5에서 RAG 테이블·권한을 준비해야 합니다. 현재 인계 가능한 것은 DB 접속 기반이며, 유빈님 실제 저장과 다혁님/원민님 실제 API 연결 준비 완료는 아닙니다. C05 승인도 확인했고 공통 반영 커밋에 맞춰 모델 보완을 별도로 연결하겠습니다.

준비 예상 시각은 P0-3은 현재 완료로 공유하고, P0-4/5는 착수·실제 장애 조건 확인 후 단계별로 공유한다. 위 문안/자료는 본인 문서에 준비했으며 외부 전송·상대 확인은 아직 수행하지 않았다. 새 P0-3 커밋·push도 아직 없다.

## 과거 제안 이력 · JH-H01~06

아래는 원문 이력을 보존한 것이다. 당시의 ‘미채택/미정’·수치·경로는 현재 적용 지시가 아니며 위 현재표와 SPEC을 우선한다. H01은 Path=/로, H02는 공통P0/P1·P2구분으로, H03 context는확정2000자로 정정한다. 별도 공통 반영 커밋을 확인한 경우만 해당 근거로 추가한다.

## JH-H01 · 세션·쿠키·첫 변경 제한

- 연결/요구: C01·C07 / BE-01·05. 상태: **제안, 미채택**.
- 기존: API 2·8절은 HttpOnly 세션·첫 암호 변경·로그아웃을 정했지만 쿠키 이름/기간/SameSite/Secure·회수 범위·첫 변경 전 허용 API가 없다.
- 제안: 쿠키 이름 `oke_session`, Path=/api, HttpOnly, SameSite=Lax, 운영 HTTPS에서 Secure=true·로컬 HTTP에서만 false. 절대 만료8시간으로 시작하며 매 요청 활성 계정/만료/폐기를 검사한다. 로그인 때 새 난수 토큰을 발급하고 DB에는 해시만 둔다. 첫 변경 전 me/change-password/logout만 허용하고 다른 보호 API는403 `password_change_required`로 한다. 암호 변경 후 기존 세션을 모두 폐기하고 현재 브라우저에는 새 세션을 발급한다. 초기화·비활성화는 해당 사용자의 모든 세션을 폐기한다. 상태 변경 요청에는 동일 출처 Origin 검증도 적용하는 안이다.
- 입출력: 웹 error.code/message 외형 유지. 로그아웃 ok=true. 쿠키 발급/삭제 헤더와 first-change403은 수언님 화면에 반영 필요. 외부 Origin/프록시 허용 목록의 실제 주소는 비밀 관리/배포 설정으로 주고 문서에 쓰지 않는다.
- 영향: security/deps/auth·users 서비스·세션 시험, 프론트 credentials/첫 변경 화면, VM HTTPS 프록시. expires_at/revoked_at은 기존 스키마로 수용 가능하다.
- 검토 상대/반영 요청: 수언님·오현님이 API 인증 절에 반영. 상대 확인 근거 없음·반영 커밋 없음·실연결 미실행. 값8시간은 사용자 확정 사항이 아니다.

## JH-H02 · 비밀번호 규정의 웹 적용 범위와 저장 구조

- 연결/요구: C01·C07 / BE-01·05. 상태: **제안, 미채택**.
- 기존: 첫 변경/초기화는 공통에 있지만 users에는 password_hash/must_change_password만 있다. 제공 `password-policy`는12자 이상·문자3종·추측하기 쉬운 단어 금지,90일 변경·최근5개 재사용 금지·5회 실패30분 잠금·회사 밖 OTP를 안내한다. 이를 웹 인증에 어떻게 적용할지와 이력/잠금 저장 구조는 공통에 없다.
- 제안: 생성/초기화/변경 모두 최소12자·대소문자/숫자/특수문자 중3종·알고 있는 본인 이름/회사명 포함 금지를 서버에서 검사한다. 최근5개 해시 이력을 검사하고90일 경과 시 변경 제한 흐름을 적용한다. 연속 실패5회면30분 잠금, 성공 시 실패 횟수를 초기화한다. 원본에 없는 생일/연락처를 새 필수 개인정보로 수집하지 않는다.
- DB 제안: users에 password_changed_at(timestamptz), failed_login_attempts(integer, 기본0), locked_until(timestamptz nullable) 추가; app.user_password_history에 id/user_id/password_hash/created_at 추가. H02 채택 후 다음 별도 revision으로 생성하고 현재 기본 revision에 끼워 넣지 않는다. 최근5개의 범위는 현재 암호 포함5개로 제안한다.
- 추가 범위 요청: 외부 접속 OTP의 웹 필수 적용 여부·수단/복구 경로를 오현님이 명시하도록 요청한다. 현재 문서에서 OTP 제외가 승인됐거나 규정 전체 준수가 완료됐다고 쓰지 않는다. OTP 구현 경로를 이번 문서 작업 범위에 새로 확장하지 않는다.
- 영향: 계정/암호/로그인 서비스·DB 변경·만료/잠금 화면·실패 응답. 로그인 실패/잠금은 동일401 안내로 계정 유무 노출을 줄이는 안이다. 입력 검증 실패400 세부 코드는 H03과 함께 검토한다.
- 검토 상대/반영 요청: 오현님(범위·API/DB 공통 반영), 수언님(화면), 원민님(경계 시험). 확인·채택·DB 변경·시험 모두 미실행. 이력·잠금 구현이 없어도 기존 스키마/seed 작업은 진행한다.

## JH-H03 · C01 세부 모델·HTTP 상태·내부 필드

- 연결/요구: C01·C02·C05 / BE-01~04. 상태: **제안, 미채택**.
- 기존: API 경로와 핵심 필드, 목록 items, 단건 객체, 웹 error 외형, 공통400 codes는 확정이다. current/new 암호의 정확한 키·직원 식별값·assignee 의미·목록 단건 필드·생성 성공 상태·중복/일부 오류코드는 미정이다.
- 제안 요청: change-password 키 current_password/new_password, 관리자 발급 employee_id/login_id/temporary_password(임의 role 입력 없음). 경로 users/{id}·tickets/{id}는 내부 bigint PK, assignee는 IT팀 `app.employees.id` 또는 null로 하고 외부 ticket_id(T-번호)와 구별한다(공통 `API-CONTRACT.md`·`DATA-AND-DB.md` 반영 완료). ticket patch는 status 필수, assignee/reply 생략 시 유지·명시 null 시 해제로 제안한다.
- 제안 응답: SPEC 4절의 AccountView/InquiryView/TicketView/AlertView 필드 목록을 사용한다. 로그인은 user 객체, me는 직접 요약 객체. 웹 생성 계정201, 나머지 웹 성공200. 기존 확정 C05 티켓 신규201/중복200·알림200은 변경하지 않는다. 목록 정렬은 created_at 내림차순·동일 시 id 내림차순으로 제안한다.
- 오류 제안: 웹400 `validation_error`와 필드별 codes(비밀번호 값 제외), 없는 계정404 `not_found`, 중복 employee/login_id409 `account_exists`, 없는 assignee/비IT400 `invalid_assignee`, 없는 외부 알림 ticket_id400 `unknown_ticket`. 추가 입력 필드는400으로 거절하고 context는 최대2000자로 제한하는 안이다. 공통 웹훅400 codes는 변환하지 않는다. 아직 이 세부400/409를 확정 계약으로 쓰지 않는다.
- support 세부 제안: security.blocked_by/reason은 문자열 또는 null, masked는 비음수 정수로 모델화한다. 기존 필드/route 및 추가 reason/timings는 그대로 유지한다. severity/category는 공통이 enum을 정하지 않았으므로 비어 있지 않은 문자열로 검증하고 임의 enum을 추가하지 않는다.
- 영향: Pydantic/OpenAPI, 화면의 ID/담당자 선택·목록 렌더링, 내부 알림 T-번호→PK 매핑, 계약 시험 fixture. 숫자형 id7/8 등은 문서 예시이며 실제 직원 매핑이 아니다.
- 검토 상대/반영 요청: 수언님(C01), 다혁님(C02 security), 원민님(C05), 오현님(API 반영). 기존/제안 차이는 SPEC 3~5절에 초안 표시. 상대 확인·반영·연결 모두 없음.

## JH-H04 · support 시간 제한·장애 응답·키 재사용

- 연결/요구: C01·C02 / BE-02·03·07. 상태: **제안, 미채택**.
- 기존: n8n 장애 때 정해진 안내/마스킹 로그, 같은 논리 요청은 같은 request_id, 타인 키403·입력400은 정해져 있다. 정확한 timeout·웹 장애 상태/코드·실행 중 재시도·같은 키의 본문 변경은 없다.
- 제안: 연결3초·요청 전체30초 제한(읽기 timeout만으로 전체 상한이라 주장하지 않고 전체 deadline 적용), FastAPI의 support 자동 재시도0회로 시작한다. n8n 내부 재시도와 중첩되지 않게 한다. 전체 예산은 실제 지연/하위 최악시간 측정 후 다혁님과 재검토한다. 숫자는 응답시간 달성 결과가 아니다.
- 제안 출력: 전체 시간 초과504 `support_timeout`, 연결/서비스 장애503 `support_unavailable`, 형식/ID 불일치502 `invalid_support_response`, 안내는 재시도/문의 확인을 요청한다. 성공200·담당자 이관으로 위장하거나 ticket을 꾸미지 않는다. 오류에도 생성 request_id를 error.request_id로 반환하도록 웹 외형의 선택 필드 추가를 제안한다. 공통 웹훅400 본문은 그대로 유지한다.
- 키 처리 제안: 소유권을 먼저 확인한 뒤 같은 key의 question/attempt/context가 다르면409 `request_conflict`, 이미 처리 중이면409 `request_in_progress`, 완료면 저장된 공통 응답 반환. inquiries.status는 pending/processing/succeeded/failed로 시작하고 원자적 상태 변경으로 단일 호출을 보장한다. 실패 재시도는 동일 소유자/동일 입력만 허용하며 티켓은 C05 UNIQUE로 중복을 방지한다.
- 복구 제안: 프로세스 중단으로 processing이 남으면 실제 n8n 결과·티켓 상태를 운영자가 확인한 뒤 재시도 가능 상태로 전환한다. 임의 시간 경과만으로 진행 중 호출을 다시 생성하지 않는다. 이 복구 동작/운영 인터페이스는 채택 전 확정 구현하지 않는다.
- 영향: HTTPX deadline/취소·문의 상태 거래·웹 재시도/안내·오류 모델/동시성 시험. 기존401/403을 retry하지 않는다. 데이터가 없는 오류를 정상 결과로 저장하지 않는다.
- 검토 상대/반영 요청: 다혁님(하위 timeout/재시도), 수언님(웹 오류/재시도), 원민님(중복/장애 시험), 오현님(공통 API 반영). 모두 미확인. 기본 입력/소유권/공통 응답 Mock 작업은 계속한다.

## JH-H05 · 최초 관리자 재실행·최후 관리자 안전장치

- 연결/요구: C01·C07 / BE-01·05. 상태: **제안, 미채택**.
- 기존: 첫 관리자1회·IT팀만 admin·나머지 관리자 발급은 정해져 있다. 첫 IT팀 인물/로그인 ID를 고정하는 정책, 비활성 관리자를 이용한 bootstrap 재생성/최후 관리자 차단은 없다.
- 제안: bootstrap CLI에서 제공 IT팀 이름과 login_id를 명시하고 특정 인물/ID를 공통 고정값으로 만들지 않는다. 관리자 계정이 있으면 활성 여부와 무관하게 생성하지 않고 기존 hash/role을 유지한다. 계정이 존재하는데 관리자가 전혀 없으면 자동 복구 생성을 거절하고 오현님 관리 절차로 넘긴다.
- 관리자 보호 제안: 마지막 활성 admin 비활성화는409 `last_admin_required`, 자기 계정 비활성화는409 `self_deactivation_forbidden`. 동시 두 관리자 변경도 거래/잠금으로 검사해 활성 관리자0명이 되지 않게 한다. 새로운 관리자 자동 추가로 우회하지 않는다.
- 영향: bootstrap CLI·관리자 활성 변경 거래·화면 오류. 신규 테이블 필요 없음. 기존 데이터/비밀번호를 덮어쓰지 않는 기본 재실행 동작은 그대로 진행한다.
- 검토 상대/반영 요청: 오현님(계정 운영·API), 수언님(버튼/오류), 원민님(동시 변경). 미검토·미반영·시험 미실행. 409 등은 제안 상태다.

## JH-H06 · app 모드 DLQ 쓰기 계약 반영

- 연결/요구: C05·C07 / BE-04·05. 상태: **공통 문서 반영 완료(실연결 미실행)**.
- 반영 내용: `docs/API-CONTRACT.md` 5절과 `docs/DATA-AND-DB.md` 3절에 X-Api-Key 인증 `POST /dlq`(`request_id`, `workflow`, `node`, `reason`, `safe_payload`, `execution_ref`) 및 `POST /alerts` 선택 `event_key`가 반영되었다.
- 영향: backend 라우터/모델·저장 서비스와 원민님 워크플로우 호출부·관측/시험에서 공통 스키마를 사용한다. 동일 실패를 두 저장소에 동시에 쓰지 않는다.
- 검토 상대/반영 요청: 원민님(입력/중복/재처리·실제 관측), 오현님(API C05/모드 반영 완료). 실제 연결은 미실행 상태다.

## 후속 기록과 버그 전달

> 아래2026-11-04 기록은 작성 당시 상태를 보존한다. 이후4bbbf49 커밋 생성·상대 회신 수신·2026-11-05 context 보완은 상단 현재표 및 IMP-PLAN 최신 보완 기록을 따른다. 당시 ‘미커밋/미확정/상대 확인 없음’을 현재 상태로 재사용하지 않는다.

### 2026-11-04 · C09 · DAY80 2절 지혜님 진행 내역 반영 요청

- 반영 대상: 루트 `docs/daily/DAY80.md`의 2절 「역할별 진행 내역」 중 지혜님 행. 반영 담당: 오현님.
- 상태: 본인 HANDOFF에 반영안을 기록했다. 루트 문서는 수정하지 않았으며, 외부 메시지 전송·오현님 확인·공통 문서 반영은 미확인이다.
- 아래 커밋·작업 상태는 이 요청 작성 시 로컬 Git 기준이다. P0-2 커밋이 생성되면 반영 전에 해당 커밋으로 갱신하고, push 여부는 별도 확인한다.

| 담당자 | 오늘 진행한 작업 | 산출물 · 커밋 | 상태 |
| --- | --- | --- | --- |
| 지혜님 | P0-1 FastAPI 골격·환경설정·liveness·공통 입력 검증 구현. P0-2 웹14·내부3 API 계약 모델·라우터·OpenAPI와 Mock 시험 구현. 유빈님 RAG P0-1 산출물의 DB 매핑을 문서 기준으로 검토하고 미확인 사항 기록 | `develop/jihye/app/`, `tests/`, `pyproject.toml`, `uv.lock`, README·Doc 문서. P0-1: `d05bff5`, C06 검토 기록: `60e3c1c`. P0-2는 로컬 변경 상태·미커밋 | P0-1~2 범위 로컬 검증 완료: 전체75개 통과·경고1건. 실제 인증·DB·data-api·n8n 연결 및 통합 시험 미완료. 다음 P0-3 DB 실행 기반 |

- 검증 근거: [IMP-PLAN P0-2 실제 기록](IMP-PLAN.md#p0-2-실제-기록--2026-11-04)의 `uv run pytest -q` 결과75개 통과(P0-1 30개+P0-2 45개), 기존 TestClient HTTPX 폐기 예정 경고1건. 이번 DAY80 반영안 작성에서는 시험을 재실행하지 않았다.
- 집계 주의: 75개는 백엔드 자체 시험 수다. DAY80 3절의 공통 시나리오 통과 수에 합산하지 않으며, 실제 data-api/n8n·팀 VM 시험 통과로 취급하지 않는다.

### 2026-11-04 · P0-2 계약 모델·Mock 전달 (C01/C02/C05, BE-01~04 일부)

- 상태: 웹14·내부3 API의 모델·라우터 시그니처와 OpenAPI·Mock 시험 완료. 실제 세션/내부키 검증·업무 저장·외부 서비스 연결은 미구현이다. 공통 계약 변경 없음.
- 실제 확인: 최종 `uv run pytest -q`로75개 통과(P0-1 30개+P0-2 45개), 기존 TestClient HTTPX 폐기 예정 경고1건. 상세 파일·명령·초안 범위는 [IMP-PLAN P0-2 실제 기록](IMP-PLAN.md#p0-2-실제-기록--2026-11-04)에 기록했다.
- 수언님(C01): 실행 앱의 `/openapi.json`·`/docs`, `tests/test_api_models.py`의 웹14개 요청/응답 fixture를 대조할 수 있다. 실제 로그인/쿠키 발급은501이고 보호 경로는 쿠키 누락401·임의 쿠키501이다. Mock 성공은 tests dependency override에서만 제공한다. InquiryView/TicketView/AlertView 단건 외형과 patch 의미는 H03 초안이며 합의로 처리하지 않는다.
- 다혁님(C02): `app/schemas/support.py`와 `tests/test_support_contract.py`에5 route·reason/timings·추가 필드 보존·400 codes 본문 전달·응답ID 불일치/잘못된 응답 검출 예시를 제공한다. 이름은 시험의 세션 fixture에서 전달하며 웹 user/dept/role/channel은 사용하지 않는다. 실제 n8n 클라이언트/문의 저장은 P1-2이며 security 세부 타입은 H03 초안이다.
- 원민님(C05): TicketCreate/TicketCreated·AlertCreate/StoredResponse·DlqCreate와 `/tickets`·`/alerts`·`/dlq` OpenAPI를 대조할 수 있다. 티켓201/중복200·알림/DLQ200은 fixture 검증이며 실제 멱등·DB 누적 건수·민감정보 제거·부분 실패 거래는 P1에 확인한다. 내부키 누락401·임의 키501, 쿠키는 내부키를 대체하지 않는다.
- 다음 지혜님 작업은 지정 시 P0-3 DB 실행 기반. P0-3~5 뒤 유빈님과 실제 저장을 연결한다. 앞선 C06 문서 검토의 실제 data-api 응답·인증 미확인은 유지된다.
- 미확정/확정 구분: H03 추가 입력 거절·context 상한·필드별 오류코드는 미채택. 최신 공통에 있는 계정 목록·생성201·assignee 정수·DLQ/event_key·첫 변경403을 적용했다. 실제 활성/만료/폐기 세션, 본인 이름/ID 포함 비밀번호 금지 검사는 P1 서비스에서 구현해야 한다.
- 본인 문서에 기록한 전달 자료이며 외부 메시지 전송·상대 확인/동의·공통 반영 커밋·VM 배포·n8n push/test는 수행하지 않았다.

### 2026-11-04 · C06 · 유빈님 P0-1 산출물 검토

**상태: 제공 문서 기준 매핑 검토 완료 / 실제 API·인증·DB 저장 미확인 / 상대 최종 확인 없음.**

검토 자료는 사용자가 대화로 전달한 유빈님의 `P0-1 원본 대장`과 `P0-1 원본 확인 실행 기록`(최신 절 `p0-1-local-03`)이다. 공통 [DATA-AND-DB 4절](../../../docs/DATA-AND-DB.md) 및 [API-CONTRACT](../../../docs/API-CONTRACT.md)에 대조했다. 원격 브랜치 내용·코드·커밋은 확인하지 않았으며 테스트 재실행이나 실제 API·DB 호출도 하지 않았다. 아래 평가는 문서에 기술된 동작과 표본 기준이며 코드 검증·실연결 완료 판정이 아니다.

#### 요청 항목별 검토 결과

| 요청받은 검토 | 결과 |
| --- | --- |
| 실제 API 응답 구조 | **미확인.** `/docs → {docs:[...]}`, 개별 문서의 `name/title/text`는 어댑터가 지원하는 가정이다. 실제 응답 표본이 필요하다. |
| 인증 방식 | **미확인.** `X-Api-Key`는 구현 가정이다. 공통 FastAPI 내부 API의 인증 헤더와 같다는 이유로 data-api에도 맞다고 확정할 수 없다. |
| 공통 DB 컬럼 매핑 표본 | **설계상 연결 가능.** 아래 조건을 지키면 현재 표본에서 공통 스키마 변경 필요는 발견하지 못했다. 실제 저장 성공을 의미하지 않는다. |

#### 대장 값과 공통 DB 매핑

| 대장 값 | 공통 DB 컬럼 | 검토 내용 |
| --- | --- | --- |
| `doc_key` | `rag.documents.doc_key` | 직접 대응한다. 대장에서 중복 두 항목을 모두 거절한 처리는 적절하다. |
| `title` | `rag.documents.title` | 마스킹 전 검증된 제목을 저장해야 한다. 대장의 마스킹 문자열을 원본 제목으로 저장하지 않는다. |
| `access_level` | `rag.documents.access_level` | `all/it`에 대응한다. `null`·충돌·미지 값은 색인·저장 대상에서 제외한다. |
| `source_url` | `rag.documents.source_url` | 대응 가능하다. 현재 표본은 상대 경로이므로 기준 `DATA_API_URL`과 함께 해석해야 한다. |
| `source_hash` | `rag.documents.source_hash` | LF 정규화한 원문 전체의 UTF-8 SHA-256으로 대응 가능하다. |
| `sections` | 후속 `rag.chunks.section/content` 생성에 사용 | 현재 대장에는 제목·길이만 있어 청크 저장 입력으로는 부족하다. 후속 단계에서 실제 본문과 청크 번호·해시·임베딩 등을 준비해야 한다. |

#### 저장 연결 시 구분할 사항

- 대장은 검토·추적용이다. `mock-it`의 `[非공개]` 제목을 실제 DB 제목으로 저장하면 안 된다. 후속 색인 단계는 권한이 확인된 원문을 안전하게 받아야 한다.
- 대장 투영 해시와 문서 `source_hash`는 용도가 다르다. 조회시각이 포함된 투영 해시는 실행 기록 식별용이며 시각 변경에 따라 달라진다. 문서 본문 변경 감지는 `source_hash`로 한다.
- `retrieved_at`은 수집 시각이다. DB의 `updated_at`과 자동으로 같은 의미라고 처리하지 말고 문서 저장·갱신 시각과 구분해야 한다.
- 문서에 기술된 권한 메타데이터 우선, 충돌 거절, 확정된 일반 규정 8종만 기본 `all` 매핑, 미확인 관리자 문서 거절은 공통 기준에 부합한다. 실제 코드에서 해당 동작이 보장되는지는 별도 검증이 필요하다.
- 테스트 33개 통과는 유빈님 산출물에 기록된 결과를 전달받은 것이다. 지혜님 측에서 재실행한 결과가 아니다. Mock의 조사 6항목·후속 준비 가능 2항목·거절 4항목은 실제 규정 확보·색인 성공 건수가 아니다.

#### 미확인 사항과 다음 연결

- 실제 data-api 호출로 응답 구조·인증 헤더와 성공/인증 실패 동작을 확인해야 한다. 비밀값을 제거한 실제 응답 표본 확보 후 어댑터 가정과 대조한다. 이 확인은 지혜님 P0-2 완료와 별개로 진행할 수 있다.
- 규정 8종의 실제 원본·권한 근거, 관리자 문서 식별자·제공 여부는 미확인이다. 유빈님·원민님·오현님 연결에서 실제 확보 결과를 확인해야 한다.
- 실제 DB 저장은 지혜님 P0-3~5의 마이그레이션·권한 준비와 유빈님 후속 색인 구현 뒤에 검증한다. 현재는 설계상 매핑 검토까지만 완료했다.
- 이번 기록은 계약 변경 요청이나 상대의 최종 동의가 아니다. 외부 도구로 팀원에게 메시지를 전송하지 않았으며, 유빈님의 검토 결과 수신·동의도 확인하지 않았다.

### 2026-11-04 · P0-1 로컬 기반 전달 (C01/C07, BE-02·05 일부)

- 구현: 앱 팩토리·공통 환경변수 설정·`GET /health/live`·웹 오류 외형·Question/RequestId/Attempt 타입, 의존성 잠금 파일. 상세 생성 파일·실행 결과는 [IMP-PLAN 실제 기록](IMP-PLAN.md#p0-1-실제-기록--2026-11-04)을 따른다.
- 확인: 설치 종료0, 계약 기초 시험30개 통과·TestClient 폐기 예정 경고1건. 실제 Uvicorn HTTP liveness 성공. DB/n8n·권한 기능·VM·다른 담당 구현과의 연결은 미실행이며 상대 확인도 없다.
- P0-2 담당 연결: 수언님용 업무 OpenAPI·다혁님용 support 모델·원민님용 저장 모델은 다음 단계다. 지금 넘길 수 있는 것은 공통 타입·오류 외형·실행 명령이며 업무 API 호출 가능을 뜻하지 않는다.
- H03: `invalid_input`은 현 골격의 임시 공통 코드다. 필드별 codes·추가 필드 거절·context 상한은 공통 반영 전 확정하지 않는다. 기존 H01~05의 제안 기록 중 현재 공통 API에 반영된 내용과 다른 부분은 최신 공통 API를 우선한다. 계약 변경 요청은 이번 작업에 없다.

상대 확인이 오면 요청ID·상대 HANDOFF 링크·검토 내용·오현님 공통 반영 커밋/절·관련 SPEC/계획 변경·실제 연결 입력/출력/증거를 구분해 덧붙인다. 현재 전 항목에 확인 근거와 반영 커밋은 없다.

실제 버그는 실행 위치/버전·마스킹한 재현 입력·기대/실제 결과·로그·영향을 전달한다. 상대 파일을 대신 수정하지 않는다. 절차는 [COORDINATION](../../../docs/COORDINATION.md), 기준은 [API](../../../docs/API-CONTRACT.md)·[DB](../../../docs/DATA-AND-DB.md)를 따른다.
