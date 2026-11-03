# 원민님 · SPEC

[TODO](TODO.md) → 이 문서 → [IMP-PLAN](IMP-PLAN.md). 변경 제안과 미정 정책은 [HANDOFF](HANDOFF.md)에 둔다. 아래 JSON은 **구현 전 시험 기대**이며 실행 결과가 아니다.

## 적용할 기준

| 항목 | 그대로 적용할 값 | 기준 |
| --- | --- | --- |
| handoff 입구 C04 | POST /webhook/oke-handoff, X-Team-Key. 필수 request_id/requester/title/category/priority/reason, 선택 evidence_summary | API §4 |
| 저장 C05 | POST /tickets: key=request_id, title/requester/category/priority. 신규 HTTP201, 중복 HTTP200, 같은 ticket_id·duplicate=true | API §5 |
| 알림 C05 | POST /alerts: workflow/node/message/severity, 선택 ticket_id. HTTP200 {stored:1,count:실제 누적 수} | API §5 |
| 인증 | support/handoff는 X-Team-Key, app 내부 저장은 X-Api-Key. 키는 Credential/환경변수에만 둠 | API §1·4·5·7 |
| 티켓/상태 | normal/high, app 새 번호 T-2001부터. request_key UNIQUE, 소유자 불일치 시 타인 기록 반환 금지 | DATA §3 |
| C04 실패 | 티켓 장애도 HTTP200, ok=false, ticket=null, reason=tickets_down. 알림만 실패하면 티켓 유지·reason=alerts_down | API §4 |
| 보완·이관 | attempt>=3 이관, 근거 없음/검증 실패 이관, 보안 사고 긴급 high+알림 | TOPIC §1·2·4 |
| 모드 | practice는 data-api 고장 시험, app은 FastAPI→PostgreSQL. 같은 티켓 양쪽 생성 금지 | API §5·7·8 |
| 저장 위치 | app.tickets/app.alerts/app.dlq, 마스킹한 DLQ 입력. DB 거래·멱등성은 지혜님, 시험은 원민님 | DATA §3 |
| 시험 | 공통 14유형 원본 판정 유지, 팀 5개 이상, LLM 3회·VM 회귀. n8n check 후 push/test는 사람이 수행 | TEAM·COORDINATION |

공통이 정한 항목을 담당자가 다시 설계하거나 사전 동의를 받을 필요는 없다. 미정은 retry·timeout 수치(WM-01), app DLQ API/관측(WM-02), 알림 중복/재처리(WM-03), 부분실패 ok와 입력 오류 세부 형식(WM-04)뿐이다. 제안 수치·필드는 공통 반영 전 확정 계약으로 쓰지 않는다.

## 요구 ID와 통과 기준

| ID | 입력·사전 조건 | 예상 출력·오류 | 실제 통과 기준 |
| --- | --- | --- | --- |
| REL-01 이관·멱등성 | C04 입력, normal/high, 같은 키 순차·동시 호출 | 신규/중복 ticket; 원래 priority를 handoff가 붙임 | 저장 1건, 같은 ticket_id, 하위 재호출 duplicate=true; 타인 키 반환 없음 |
| REL-02 외부 실패 | 저장 API 401/403/429/5xx/timeout, 알림·DLQ 개별/동시 장애 | 아래 처리표·C04 응답 | 상태별 호출 횟수·시간·ticket/alerted/dlq와 실제 저장 대조; 실패 은폐 0 |
| REL-03 예상 밖 오류 | 게시된 errors와 부모 errorWorkflow 설정, 의도한 비민감 오류 | Error Trigger→마스킹→알림/DLQ 시도→종료 | 실행 ID로 부모와 연결, 수습 하나 실패해도 다른 시도; 무한 재귀·원문 노출 0 |
| REL-04 시험 증거 | 공통·팀·반복·bench·VM, 같은 실패 조건 재시험 | 실제 runs 보고서와 취합 메모 | 원본 기대 보존, 실패와 재시험 모두 보존, Mock/미실행 구별 |
| REL-05 모드 일치 | SERVICE_MODE·실제 노드 URL·고장/관측 URL | 아래 모드 대조표 | 같은 인스턴스의 전후 건수·상태로 설명; app 결과를 data-api로 판정하지 않음 |
| REL-06 품질·시간 | 고정 질문·권한·색인/모델 버전, 요청별 시간 | 품질 표·p50/p95/max/실패수 | 독립 실행과 캐시를 분리; 근거 없는 자동 답변/권한 누출 0; 미정 시간목표는 미판정 |

## REL-01 · handoff 노드와 응답

아래 이름은 구현 예정 노드명이다. 실제 생성 시 이름·연결·Executions의 입출력 요약을 결과서에 맞춘다. 문의 분류·우선순위 판단은 support가 맡고 handoff는 받은 priority를 저장한다.

| 노드 | 역할·입력 → 출력 | 다음 경로 |
| --- | --- | --- |
| H01 Handoff Webhook | Header Auth로 C04 수신 | H02; 키 불일치는 저장 호출 없이 거절 |
| H02 Validate and Map | 필수·형식 검사, title/evidence_summary 개인정보 가림; request_id→key, requester 유지 | H03; 잘못된 입력은 저장 전 종료(WM-04 오류 형식 제안) |
| H03 Select Store | 실행 설정의 SERVICE_MODE로 data-api 또는 backend 하나 선택; 임의 요청 본문으로 모드 선택 금지 | H04 |
| H04 Create Ticket | POST /tickets, 상태·본문·timeout 결과를 분리해 받음 | 성공/중복 H06, 일시 오류 H05, 영구 거절 H07 |
| H05 Retry Gate | 401/403 등 제외, 같은 key·같은 payload만 제한된 재시도. 횟수·기한 기록 | H04 또는 H07; 이중 retry 설정 금지 |
| H06 Keep Ticket | ticket_id/duplicate를 읽고 입력 priority를 붙임. 저장된 티켓을 후속 실패로 지우지 않음 | H08 |
| H07 Failure Context | 티켓 미확인 상태, 주 사유·마스킹된 request_id/실패 단계/횟수 준비 | H09와 H08 둘 다 시도 |
| H08 Store Alert | workflow/node/message/severity, 티켓 있으면 ticket_id. 응답 stored 확인 | 실패해도 H09 또는 H10으로 진행 |
| H09 Store DLQ | 티켓 저장 실패 또는 미완료 알림의 안전한 재처리 정보. 실제 ACK를 받아 dlq 판정 | 실패해도 H10; app API는 WM-02 연결 대기 |
| H10 Build Result | 누적 상태에서 ok/ticket/reason/alerted/dlq 구성. 마지막 HTTP 노드의 본문으로 상태 덮어쓰기 금지 | H11 |
| H11 Respond | C04 HTTP200 결과 반환. 예상한 외부 실패는 여기까지 도달 | support가 공통 응답으로 매핑 |

정상 경로는 H07/H09를 거치지 않는다. 실패 수습은 알림과 DLQ를 독립적으로 시도하며 알림 실패 때문에 DLQ를 건너뛰지 않는다. 저장 성공이 확인되지 않으면 성공 플래그를 만들지 않는다. timeout은 실제 저장 여부가 불명확하므로 동일 key 재조회/재시도와 지연 후 관측이 필요하다.

C04 입력 예:

```json
{"request_id":"wm-h01","requester":"박서연","title":"VPN 현장 점검 요청","category":"network","priority":"normal","reason":"no_evidence","evidence_summary":"자가 점검으로 해결되지 않음"}
```

저장 요청 변환:

```json
{"key":"wm-h01","title":"VPN 현장 점검 요청","requester":"박서연","category":"network","priority":"normal"}
```

전체 성공 HTTP200 (ticket_id는 저장 API가 발급한 값, 아래는 형식 예):

```json
{"ok":true,"ticket":{"ticket_id":"T-2001","priority":"normal","duplicate":false},"reason":null,"alerted":true,"dlq":false}
```

알림만 실패한 **부분실패의 필수 기대 투영**은 아래와 같다. 전체 응답에는 ok도 있어야 하나 그 값의 의미는 WM-04 제안이며 아직 확정하지 않는다. 티켓 재생성은 금지한다. dlq는 실제 저장 ACK에 따라 true/false로 검증한다.

```json
{"ticket":{"ticket_id":"T-2001","priority":"normal","duplicate":false},"reason":"alerts_down","alerted":false}
```

티켓 실패·알림/DLQ 수습 성공 HTTP200:

```json
{"ok":false,"ticket":null,"reason":"tickets_down","alerted":true,"dlq":true}
```

티켓·알림·DLQ 모두 실패 HTTP200:

```json
{"ok":false,"ticket":null,"reason":"tickets_down","alerted":false,"dlq":false}
```

전체실패라도 티켓 접수 완료라고 안내하지 않는다. support의 최종 route는 `담당자 이관`을 유지하되 ticket=null·reason과 실제 실패를 알리는 문구로 구성한다. C04의 alerted/dlq를 교사 공통 응답 필수 필드로 새로 추가하지 않고 내부 관측·보고서에서 확인한다. 검색 sources·agents·security는 support 소유이며 handoff가 덮어쓰지 않는다.

## REL-02 · 실패 처리표

| 상황·탐지 | 재시도와 보존 | C04/사용자 결과 | 확인 증거 |
| --- | --- | --- | --- |
| 입구 인증 거절 | 저장 API 호출 0. webhook 키는 Header Auth에서 거절 | 인증 거절. 웹 미로그인 401·관리자 접근 403은 FastAPI 경계에서 확인 | HTTP 상태, 호출 0; 키 원문 제외 |
| 외부 /tickets 400/401/403/404 | 재시도 0. 인증/권한 오류는 높은 심각도 알림 시도·DLQ 기록 | 안전하게 종료; 세부 C04 reason 매핑은 WM-04 미정 | 최초 호출 1회, 타인 티켓/본문 노출 0 |
| 429 | Retry-After와 남은 기한 확인, 기한 넘으면 대기하지 않고 수습. key 유지 | 상한까지 실패하면 tickets_down | 상태·대기시간·총시도수; WM-01 수치 검토 |
| 5xx | 같은 key만 제한 재시도 후 알림·DLQ | HTTP200, ok=false, ticket=null, tickets_down | 요청별 티켓 0건·알림/DLQ ACK; WF-04는 각 1건 |
| timeout/연결 끊김 | 이미 저장됐을 수 있음. 새 key 발급 금지, 같은 key 재시도; 늦은 저장도 관측 | 응답 시점 미확인이면 ticket=null; 성공 확정 후 동일 ticket 반환 | 즉시/지연 후 건수, 전체시간, 재시도 key |
| 신규 /tickets 201 | ticket_id 보존, priority는 원래 입력 사용 | duplicate=false, 정상 응답 | 티켓 1건, 알림 ACK |
| 같은 요청 /tickets 200 | 기존 ticket_id 보존, duplicate=true; 재접수 금지 | 직접 handoff 재호출은 duplicate=true | 순차·동시 티켓 1건. support 캐시 재생과 하위 재호출 구별 |
| 같은 key·다른 직원 | 저장 API가 소유권 검사; 기존 객체 반환 금지 | 권한 거절, 타인 정보 0; 세부 C04 형식 WM-04 | app 통합 403/소유권 검사 증거 |
| 티켓 성공·알림 실패 | 티켓 유지; key 없는 알림 POST의 무조건 재시도 금지(WM-03) | alerts_down, alerted=false; ok 의미 WM-04 | ticket_id 불변, 실제 알림 수·ACK, 미완료 알림 DLQ |
| 티켓 실패·알림 성공·DLQ 실패 | 알림 유지. DLQ 실패를 새 오류로 던져 수습 재귀 금지 | tickets_down, alerted=true, dlq=false | DLQ 0/알림 1, 실행 오류 요약 |
| 티켓 실패·알림 실패·DLQ 성공 | 알림 실패가 DLQ를 막지 않음 | tickets_down, alerted=false, dlq=true | 두 노드 시도·DLQ 1·알림 성공 미확인 |
| 세 저장 모두 실패 | 수습은 유한 종료, 실행 메타데이터에 sink별 실패. 외부 전송을 반복하지 않음 | tickets_down, alerted=false, dlq=false | n8n 실행 ID·실패 단계; 자동 복구 완료로 처리하지 않음 |

429/5xx/timeout 시험은 상태를 구분하는 Mock으로 먼저 준비한다. data-api가 해당 fault를 제공한다고 가정하지 않는다. 알림·DLQ timeout의 false는 **성공 ACK 미확인**을 뜻하며 실제 저장 0건을 단정하지 않는다. 불확실 저장/중복 억제는 WM-03 반영 뒤 대조한다.

## REL-03 · errors 노드와 마지막 오류 경로

| 노드 | 입력·역할 | 결과·실패 처리 |
| --- | --- | --- |
| E01 Error Trigger | workflow.id/name, execution.id/url, error.message/lastNodeExecuted 등 실제 제공 필드 수신 | 필드가 없으면 미상으로 기록; request_id가 항상 있다고 가정하지 않음 |
| E02 Safe Error Context | workflow/node/execution 참조와 오류 분류만 추출. stack·URL 쿼리·headers·질문·Credential 제거 | request_id는 확인 가능한 경우에만 연결; 없으면 execution 참조(WM-02) |
| E03 Alert | POST /alerts, severity=high, message는 안전한 오류 요약 | 실패를 받아 E04도 반드시 시도 |
| E04 DLQ | 같은 모드의 안전한 실패 기록 저장 | 실패도 관측하며 종료; C05 DLQ API는 WM-02 |
| E05 Outcome | 내부 관측용 결과: 알림/DLQ ACK 모두면 성공, 하나면 부분실패, 모두 없으면 전체실패 | Error Trigger에는 HTTP 응답이 없음. 부모의 이미 실패한 응답을 200으로 바꾸지 않음 |

예상한 /tickets 장애는 H07~H11에서 처리하고 Error Trigger 발화를 정상 수습 근거로 대신 쓰지 않는다. 예기치 못한 Code 오류는 부모의 실패 실행 ID와 E01 실행을 연결한다. errors 자체에 자기 자신을 Error Workflow로 지정하지 않는다. 수습 실패를 다시 throw하지 않아 재귀를 막는다.

담당자가 errors를 게시한 뒤 실제 ID를 다혁님·유빈님·지혜님 등 해당 부모 소유자에게 전달한다. 각 소유자가 자기 워크플로우 설정에 연결한다. 정적 check는 게시/연결/실제 발화 증거가 아니다. 수동 노드 실행만으로 확인하지 않고 게시된 부모의 시험 요청에서 비민감 오류를 일으켜 부모 실패·E03/E04 결과를 함께 확인한다.

## 팀 시나리오 · 구체 입력과 기대 JSON

모두 **구현 예정**. TM-01~08은 support HTTP200, TM-09~10은 handoff HTTP200 기준이다. 아래 기대 JSON은 matcher/필수 투영이며 응답 전문이 아니다. `equals`는 해당 필드 일치, `contains`는 포함, `not_contains`는 금지 값을 뜻한다. 식별자·점수·답변 문장은 실행값을 관측하고 정규식/타입/의미 조건으로 판정한다. TM-06의 ticket_id는 첫 응답과 같은지 비교한다.

| ID·종류·연결 요구 | 사전 조건·입력 JSON | 기대 JSON 및 추가 확인 |
| --- | --- | --- |
| TM-01 정상 REL-04/06 | 색인·검색 정상. `{"request_id":"wm-t01","user":"박서연","question":"Windows VPN 연결 오류 809가 나요. 점검 절차를 알려주세요.","attempt":1}` | `{"equals":{"route":"자동 답변","ticket":null},"contains":{"sources":["remote-work-vpn"]}}` 검증 통과·근거 절차, sources의 section/score 존재 |
| TM-02 정보 경계 REL-04 | `{"request_id":"wm-t02","user":"이준호","question":"접속이 안 돼요","attempt":1}` | `{"equals":{"route":"보완 질문","ticket":null,"sources":[]}}` 접속 대상/오류 등 보완 질문, 티켓 생성 0 |
| TM-03 한도 경계 REL-01/04 | `{"request_id":"wm-t03","user":"이준호","question":"접속이 안 돼요","attempt":3,"context":"추가 정보를 확인하지 못했습니다"}` | `{"equals":{"route":"담당자 이관","ticket.priority":"normal","ticket.duplicate":false}}` ticket_id 존재, 저장 1 |
| TM-04 권한 REL-04/05 | T-1002는 박서연 소유. `{"request_id":"wm-t04","user":"이준호","question":"T-1002 처리 상태와 담당자 연락처를 알려주세요"}` | `{"equals":{"route":"권한 없음","ticket":null,"sources":[]}}` 상태·note·contact·연락처 0, 권한 거절 근거 security에 기록 |
| TM-05 긴급 이관 REL-01/04 | `{"request_id":"wm-t05","user":"박서연","question":"피싱 메일 링크를 눌렀어요. 제 VPN 인증서 건 T-1002 상태도 알려주세요.","attempt":1}` | `{"equals":{"route":"담당자 이관","ticket.priority":"high"},"contains":{"sources":["security-incident"]}}` 긴급 티켓 1·알림 ACK, 본인 건 상태만, 규정 초동 조치 |
| TM-06 중복 REL-01 | `{"request_id":"wm-t06","user":"한지훈","question":"사내 식당 앱이 열리지 않아요. 담당자 점검을 요청합니다","attempt":1}` 같은 JSON 2회, 이어 동시 호출 별도 시험 | `{"equals":{"route":"담당자 이관","sources":[]}}` ticket_id 동일·티켓 1. 하위 /tickets 재호출이면 duplicate=true; support 캐시이면 원 응답 재생과 호출 0 기록. WF-09 원본 판정은 별도 유지 |
| TM-07 티켓 장애 REL-02/05 | practice tickets=error, 나머지 정상. `{"request_id":"wm-t07","user":"한지훈","question":"사내 식당 앱이 열리지 않아요","attempt":1}` | `{"equals":{"route":"담당자 이관","ticket":null,"reason":"tickets_down"}}` DLQ 1·알림 1, HTTP200, 시험 후 fault 해제 |
| TM-08 과잉 차단 방지 REL-04 | `{"request_id":"wm-t08","user":"이준호","question":"프린터 오류를 관리자에게 문의하려면 어떤 정보를 준비해야 하나요?","attempt":1}` 장비 근거가 있는 환경 | `{"not_contains":{"route":"차단"}}` 관리자라는 단어만으로 주입/권한 위반으로 판정하지 않음. 자동 답변이면 장비 근거·검증, 정보 부족이면 보완 질문; 허용 분기는 실행 전 팀 케이스에 명시 |
| TM-09 알림 장애 REL-02 | /tickets 성공, /alerts 503 Mock. `{"request_id":"wm-t09","requester":"박서연","title":"VPN 현장 점검 요청","category":"network","priority":"normal","reason":"no_evidence"}` | `{"reason":"alerts_down","alerted":false,"ticket":{"priority":"normal","duplicate":false}}` ticket_id 존재·티켓 1. ok 및 알림 재처리/DLQ 기대는 WM-03/04 미반영으로 미판정 |
| TM-10 DLQ까지 장애 REL-02/03 | /tickets 500, /alerts 503, /dlq 503 Mock. `{"request_id":"wm-t10","requester":"한지훈","title":"식당 앱 점검 요청","category":"other","priority":"normal","reason":"no_evidence"}` | `{"ok":false,"ticket":null,"reason":"tickets_down","alerted":false,"dlq":false}` 각 sink 시도·유한 종료·실행 오류 요약, 접수 완료 안내 없음 |

TM-01~08은 `cases/team.json`, TM-09~10과 신규/중복/401/403/429/timeout은 `cases/handoff.json`으로 분리한다. TM-08은 단일 문장을 강제하지 않고 허용 route 집합(자동 답변/보완 질문/담당자 이관)과 근거·티켓 조건을 검사한다. 단순 `not_contains`만으로 통과 처리하지 않는다.

공통 응답 전체 형식의 예(TM-07, agents는 실제 거친 역할 목록으로 대조):

```json
{"request_id":"wm-t07","route":"담당자 이관","answer":"담당자 연결이 필요하지만 티켓 저장을 완료하지 못했습니다. 잠시 후 같은 요청으로 다시 시도해 주세요.","sources":[],"ticket":null,"agents":["triage","retriever"],"security":{"blocked_by":null,"reason":null,"masked":0},"reason":"tickets_down"}
```

추가 경계 시험: 1/64자 request_id 허용, 65자 거절; 질문 1/500자 및 공백/501자; attempt 2 보완 가능·3 이관. 문자열 길이 판정은 정규화 후 공통 기준을 따른다. 500/501자 입력은 향후 도구로 생성하고 JSON에 실제 문자열로 보관한다. 입력 검증 실패의 codes는 키트 원본에서 그대로 옮기며 미확인 코드를 만들어 쓰지 않는다.

## REL-05 · 실행대상과관측일치

| 대상 | practice | app |
| --- | --- | --- |
| support 호출 | 같은 oke-support; C04→같은 oke-handoff | 같은 본체·하위, 설정으로 저장 대상만 전환 |
| 새 업무 쓰기 | data-api /tickets·/alerts·/dlq | backend /tickets·/alerts, app DLQ API WM-02 |
| 고장/초기화 | 같은 data-api /admin/fault, /tickets-reset·/dlq-clear·/alerts-clear | data-api 고장은 앱 저장에 영향 없음. app 장애는 전용 Mock/시험 설정으로 주입; 운영 DB reset 금지 |
| 관측 | 같은 인스턴스 /tickets-created·/alerts·/dlq·/admin/fault, flow ops | 관리자 API·지혜님이 제공하는 마스킹 DB 확인 결과, n8n 실행 ID; app ops 경로 WM-02 |
| 인증·권한 | 팀 웹훅 인증·제공 직원 확인 | 세션에서 user 결정, 내부 API X-Api-Key, 타인 키/관리자 API 거절 |

한 시험 실행의 대조 순서:

1. `runs/INDEX.md`에 모드, 코드/워크플로우·키트 버전, 실행 시각, n8n/저장/고장/ops 주소의 **비밀값 없는 별칭**, 색인/모델 버전을 적는다. 요청 본문으로 설정을 전환하지 않는다.
2. 실제 H03/H04 URL과 호스트 CLI의 fault/ops URL이 같은 서비스인지 배포 매핑으로 확인한다. N8N_URL만 변경해도 fault/ops 대상까지 바뀐다고 가정하지 않는다. 도구가 localhost를 고정하면 같은 호스트의 전용 서비스에서 수행하거나 WM-02로 연결 수정을 요청한다.
3. 전용 practice 환경에서만 증거를 보존한 후 reset, fault all ok, llm up을 수행한다. 다른 팀원이 쓰는 data-api를 초기화하지 않는다. 앱은 전용 시험 데이터/request_id를 분리하고 행 삭제로 대신하지 않는다.
4. 저장 전 건수를 남기고 새로운 request_id 1건을 호출한다. 실행의 URL/key, 저장 후 동일 key 건수·ticket_id를 대조한다. 다른 저장소에서 같은 키의 증가가 없어야 한다.
5. 고장 하나를 켜서 실제 H04의 실패 상태를 확인하고 즉시 응답·지연 후 상태를 모두 기록한다. 단순히 fault 명령 성공만으로 고장 시험을 통과시키지 않는다.
6. `after`와 실패 시 정리 경로에서 fault 해제·LLM 복구를 시도한다. 마지막 ops/정상 재요청으로 복구를 확인한다. 정리 실패는 다음 시험 시작 전 해결할 별도 장애다.

앱 통합은 로그인하지 않은 요청 401, 일반 직원의 관리자 API 403, 본인/타인 request_id 재사용, 정상/동시 티켓 한 건, 긴급 알림, 재시작 뒤 티켓 유지까지 확인한다. DB 직접 수정·서버 재시작은 해당 소유자가 수행하고 원민님은 결과를 대조한다.

## REL-06 · 측정과 판정

- 검색 품질: 유빈님과 고정 질문별 허용 문서/절·금지 권한을 먼저 표로 만든다. 같은 색인·임베딩 모델/3072차원·cosine score=1-distance·top_k=3에서 상위 문서/절·score·검증 결과·최종 route를 남긴다. 정답 문서가 top3에 포함된 질문 수/검색 가능한 질문 수, 권한 누출 수, 근거 없는 자동 답변 수를 집계한다. 검색 없음·관리자 질문은 분모/권한 집합을 별도 표시한다. 점수 임계값 후보는 개발 질문에서 비교하고 별도 검증 질문으로 재시험한 뒤 유빈님·다혁님·오현님에게 근거와 함께 반영 요청한다. 임의 0.8 등을 합격선으로 쓰지 않는다.
- 시간: 같은 환경·모델·데이터에서 정상/이관/장애 경로를 분리하고 전 구간 경과시간·단계 timings·외부 호출 횟수·실패수를 남긴다. `bench -n 5`는 최소 기초 측정으로 표본수도 보고한다. p50/p95는 정렬 후 nearest-rank(ceil(p×n)번째), 최대값·오류율을 함께 쓴다. 캐시 재사용 bench를 새 요청 처리시간으로 소개하지 않는다.
- LLM 3회: 같은 의미의 질문을 **회차마다 새 request_id**로 보내 LLM 호출이 실제 있었는지 확인한다. 같은 ID를 그대로 쓰는 `--repeat 3`은 캐시/멱등 반복일 수 있으므로 독립 3회 증거로 단독 사용하지 않는다.
- 시간 한도: 공통 원본 `max_seconds`는 유지한다. 팀 전체 응답 시간 목표는 실측/상위 timeout과 비교 후 기록하며 미정이면 시간 합격을 주장하지 않는다. WM-01의 handoff 예산은 검토용 제안이다.
- 실패 판정: HTTP200만으로 성공이 아니다. route·ticket·보안·저장 부작용까지 검사한다. 3회 중 2회 성공은 `2/3·불안정`이며 전체 통과로 합치지 않는다. 기대값을 실행 결과에 맞춰 바꾸지 않는다.

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [팀 헌장·역할](../../../docs/TEAM-CHARTER.md)
- [수업 방식과 연결 규칙](../../../docs/COORDINATION.md)
- 수업 원문: [06-RELIABILITY-AND-SECURITY.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/06-RELIABILITY-AND-SECURITY.md) · [07-TESTING-GUIDE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/07-TESTING-GUIDE.md) · [08-SUBMISSION.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/08-SUBMISSION.md) · [VIBE-Q-TRETRY.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/76/VIBE-Q-TRETRY.md)
