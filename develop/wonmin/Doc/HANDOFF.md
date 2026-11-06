# 원민님 · 변경 제안·전달 기록

기본안대로 구현하는 일에는 새 협의가 필요 없다. [README](../README.md) → [TODO](TODO.md) → [SPEC](SPEC.md) → [IMP-PLAN](IMP-PLAN.md)으로 바로 진행한다. 여기는 **공통에 실제로 빠진 정책의 제안과 변경 근거**만 기록한다.

> 2026-11-03 문서 제안 작성. 아래 상태는 모두 **제안 작성·미검토·공통 미반영·실제 연결 미확인**이다. 외부 메시지 전송·상대 동의·설치·시험·PASS를 뜻하지 않는다. 공통 반영은 오현님이 맡는다.

## 연결과 계속 진행할 범위

| 연결 | 검토 상대 | 제안 | 기다리지 않고 할 일 |
| --- | --- | --- | --- |
| C04 | 다혁님 | WM-01·04 | 기존 요청/응답 매핑, 정상·중복 티켓 예와 팀 입력 준비 |
| C05 | 지혜님 | WM-01~04 | /tickets·/alerts 기본 API, 모드 선택, 정상·중복·권한 Mock |
| C07 | 지혜님·오현님 | WM-02 | 고정 서비스명/포트 적용, practice/app 대상 대조 문서 |
| C08 | 해당 기능 담당 | 실패 재현 발생 시 기록 | 공통 원본 보존, 팀 기대·보조 검사 준비 |
| C09 | 오현님 | 아래 공통 보완 제안 | 본인 문서와 실제 증거 정리; 루트 파일 편집은 하지 않음 |

## WM-01 · 재시도 수치와 C04 시간 예산

- 연결/요구: C04·C05 / REL-02·06. 상태: 제안, 검토·실행 없음.
- 기존: 401/403 무재시도, 429/5xx/timeout 상한 필요. 공통에는 횟수·호출별 timeout·handoff와 부모의 시간 관계가 없다.
- 제안: tickets는 최초 포함 최대 2회, 각 timeout 1000ms. 5xx 대기 200ms. 429는 유효한 Retry-After를 지키되 허용 대기 200ms 또는 남은 전체 기한을 넘으면 재시도 없이 수습한다. 400/401/403/404는 최초 1회만. timeout 재시도는 동일 key/payload만 한다.
- 제안 예산: alerts 1회 600ms, DLQ 1회 600ms, handoff 전체 4000ms, support의 C04 호출 timeout 5000ms. 최악 외부 대기=2×1000+200+600+600=3400ms, 처리 여유 600ms. 이것은 **실측 전 후보**이며 전체 문의 응답 목표가 아니다. deadline 남은 시간이 부족하면 추가 시도를 시작하지 않는다.
- 기존/제안 입출력: C04 필드·route·HTTP200 실패 계약은 유지한다. 설정과 시도/대기/실제 시간 메타데이터만 분리한다. `tickets_down` 등 기존 사유를 사용한다.
- 영향: 다혁님의 C04 HTTP timeout, 원민님 H05, 지혜님 내부 API 지연/거래. 8초 지연으로 늦게 저장될 수 있어 지연 후 동일 key 한 건 확인이 필요하다. alerts는 멱등 키가 없어 자동 재시도하지 않는 보수적 후보(WM-03).
- 검토 상대/수정 소유자: 다혁님(C04 시간), 지혜님(C05 거래·지연), 공통 API §4·8 반영 오현님.
- 기다릴 부분/계속할 부분: 상한 정책의 최종 시간 판정만 보류. 상태별 분기·설정 분리·Mock 측정·정상/중복 구현은 진행한다.
- 검토 근거·상대 기록·반영 커밋: 없음. 실제 시험: 미실행.

## WM-02 · app DLQ API와 모드별 관측

- 연결/요구: C05·C07 / REL-03·05. 상태: **`POST /dlq` 및 `app.dlq` 스키마 공통 반영 완료(내부 ops 조회 및 실제 연결 미실행)**.
- 반영 내용: `docs/API-CONTRACT.md` 5절과 `docs/DATA-AND-DB.md` 3절에 backend 내부 `POST /dlq`(X-Api-Key, `request_id`/`workflow`/`node`/`reason`/`safe_payload`/`execution_ref`, 201/200)가 반영되었다.

제안 요청 예(비밀값·질문/답 원문·연락처 없음):

```json
{"request_id":"wm-t07","workflow":"oke-handoff","node":"Create Ticket","reason":"tickets_down","safe_payload":{"stage":"ticket","priority":"normal","attempts":2},"execution_ref":"n8n-execution-example"}
```

- 제안 응답: 신규 HTTP201 `{"stored":true,"dlq_id":"D-2001","duplicate":false}`, 동일 실패 중복 HTTP200에 같은 dlq_id·duplicate=true. 인증 실패 401/403, 저장 불가 503. Error Trigger가 request_id를 제공하지 않으면 null 허용·execution_ref로 연결하고 가짜 request_id를 생성하지 않는다.
- 제안 저장: request_id의 nullable 여부·execution 참조·stage·멱등 키를 지혜님이 검토한다. 같은 실패의 재전송은 `(request_id 또는 execution_ref, stage, reason)`으로 중복 억제한다. 개인정보를 제거한 summary만 저장한다. 복구에 필요한 직원 식별/원래 작업은 서버의 inquiry/ticket 연결로 확인하고 없으면 자동 replay하지 않고 수동 확인 대기로 둔다.
- 제안 관측: X-Api-Key로 보호한 `GET /internal/ops?request_id=...`에서 해당 키의 ticket_id·티켓/알림/DLQ 개수·실패 단계만 제공. 개인정보·Credential 제외. 미제공 시 지혜님이 실행한 마스킹 DB 조회 결과를 실행 ID와 함께 넘긴다. 원민님이 새 DB/SQL을 작성하거나 관리자 권한을 우회하지 않는다.
- 실행 연결: 도구의 실제 고장/ops 호스트를 먼저 확인한다. 호스트가 고정인 키트는 같은 호스트의 전용 data-api에서 시험한다. N8N_URL만 VM으로 바꿔 로컬 data-api를 관측하는 시험은 금지한다. 원본 common 판정·URL을 임의 수정하지 않고 실행 환경 매핑을 조정한다.
- 영향: 지혜님 내부 라우터·마이그레이션·권한/관측, 원민님 H09/E04·시험 도구, 다혁님 오류 연계. app 초기화 API를 운영용으로 추가하자는 제안은 아니다.
- 검토 상대/공통 반영: 지혜님·다혁님, C07 지혜님·오현님; API §5·7, DATA §3 갱신 오현님.
- 기다릴 부분/계속할 부분: app DLQ 실제 저장/관측만 대기. practice 기존 스키마·app /tickets·/alerts·안전한 오류 요약과 Mock은 계속한다.
- 검토 근거·반영 커밋·실제 연결: 없음/미실행.

## WM-03 · 알림 중복과 부분완료 재처리

- 연결/요구: C04·C05 / REL-01·02·03. 상태: **`POST /alerts` 선택 `event_key` 및 `app.alerts.event_key UNIQUE` 공통 반영 완료(자동 재처리 및 실제 시험 미실행)**.
- 기존: ticket key 멱등성은 확정. /alerts 입력에는 request_id/멱등 키가 없으며 알림 timeout 후 재시도·중복 티켓 재요청·DLQ replay의 알림 중복 억제 경계가 정해지지 않았다.
- 제안(공통 반영 완료): /alerts에 내부 선택 `event_key`를 추가한다. 티켓 접수 알림은 `request_id:ticket-created`, 저장 장애는 `request_id:tickets-down`, 예상 밖 오류는 `execution_ref:unexpected-error`로 구분해 백엔드 UNIQUE로 보장한다. 신규 알림 ACK는 기존 stored/count를 유지하고 중복은 stored=0·count 유지·선택 duplicate=true를 반환한다. 기존 키트 호환 모드에는 미지원 필드를 강요하지 않는다.
- 제안 예: 기존 요청 `{"workflow":"oke-handoff","node":"Create Ticket","message":"티켓 저장 실패","severity":"high"}` → app 선택 필드 `"event_key":"wm-t07:tickets-down"` 추가. 키에 질문/이름/비밀값을 넣지 않는다.
- 제안 재처리: 티켓 성공·알림 실패는 DLQ stage=alert에 ticket_id/event_key만 연결하고 알림만 재시도한다. 티켓 실패는 stage=ticket으로 분리하며 원래 request_id로 재시도한다. 이미 생성된 티켓을 다시 생성하는 흐름으로 전체 replay하지 않는다. ACK 불명확 상태는 event_key로 조회/중복 억제 후 처리한다. 자동 replay는 후순위다.
- 제안 경계: 알림과 DLQ 기록의 중복 방지·완료 표시는 백엔드의 거래/멱등 설계로 보장한다. 티켓 성공 응답과 알림 저장이 하나의 원자적 거래라고 가정하지 않는다. 전송 시도 수와 실제 알림 건수는 따로 기록한다.
- 영향: 지혜님 /alerts·app.alerts 제약/미완료 기록, 원민님 H08/H09/E03/E04·복구 검사. practice는 기존 key 지원 여부를 먼저 확인하고 무조건 알림 POST 재시도를 하지 않는다. WF-04의 알림/DLQ 1건 기대는 변경하지 않는다.
- 검토 상대/공통 반영: 지혜님·다혁님 검토, API §4·5와 DATA §3 반영 오현님.
- 기다릴 부분/계속할 부분: 중복 알림의 최종 개수/자동 replay 정책만 미판정. 티켓 1건·ACK 확인·실패 단계 분리는 계속한다.
- 검토 근거·반영 커밋·실제 연결: 없음/미실행.

## WM-04 · C04 미정 상태의 응답 의미

- 연결/요구: C04·C05 / REL-01·02. 상태: 제안, 검토·실행 없음.
- 기존: 전체 성공 ok=true, 티켓 장애 ok=false, 알림 실패 ticket 유지·reason=alerts_down은 확정이다. 알림만 실패했을 때 ok, 잘못된 C04 입력, 저장 API 401/403·타인 key 거절의 하위 응답 형식/사유는 비어 있다.
- 제안 A: ok는 **티켓 저장 확인 여부**로 정의한다. 알림만 실패하면 HTTP200 `{"ok":true,"ticket":{"ticket_id":"T-2001","priority":"normal","duplicate":false},"reason":"alerts_down","alerted":false,"dlq":true}`; dlq는 실제 ACK일 때만 true다. 주 실패 reason은 tickets_down을 우선하고 알림/DLQ 실패는 내부 단계 기록으로 남긴다.
- 제안 B: C04 잘못된 입력은 저장 전 HTTP400 `{"error":{"code":"invalid_handoff_input","message":"이관 입력을 확인해 주세요."}}`. 이것은 공통 support 웹훅의 HTTP400 codes를 대체하지 않는다. C04 입구 인증 거절은 기존 Header Auth를 따른다.
- 제안 C: 저장 API 401/403은 재시도 없이 C04 HTTP200 `ok=false,ticket=null,reason=storage_auth_failed,alerted/dlq=실제ACK`로 처리한다. 타인 key 반환 거절은 별도 `request_owner_mismatch` 사유로 표시하고 support가 개인정보 없이 권한 없음으로 매핑한다. **이 두 reason과 권한 매핑은 새 제안**이며 현재 확정된 tickets_down 계약을 임의 변경하지 않는다.
- 영향: 다혁님 Handoff 응답 해석·최종 route/reason/안내, 지혜님 소유권 오류 상태, 원민님 H02/H10과 부분실패 기대. 공통 400 codes·route 집합은 보존한다.
- 검토 상대/공통 반영: 다혁님·지혜님, API §4·5·8 반영 오현님.
- 기다릴 부분/계속할 부분: 미정 필드·새 reason만 확정 판정 보류. 정상·티켓 장애·티켓 보존·401/403 무재시도·타인 정보 미노출은 기존대로 시험 준비한다.
- 검토 근거·반영 커밋·실제 연결: 없음/미실행.

## 실제 실패·검토가 생기면 남길 기록

실행 시각/모드/배포·키트·색인 버전, SPEC/케이스 ID, 사전 조건, 비밀값 없는 요청, 기대 HTTP/JSON/부작용, 실제 HTTP/JSON/부작용, 실행 ID·마스킹 로그·보고서, 재현 명령을 적는다. 원인 근거와 추정을 구분한다.

검토 상태는 `제안 → 검토 요청 → 상대 확인 → 공통 반영 → 실제 연결 확인`을 각각 증거 링크로 남긴다. 상대 답변이 없으면 동의로 처리하지 않는다. 소유자가 수정한 뒤 동일 조건으로 재시험하고 원 실패/수정 버전/재시험 보고서를 연결한다. 다른 사람의 파일은 고치지 않는다.

절차 기준: [COORDINATION](../../../docs/COORDINATION.md). 현재 외부 전달·검토·시험 기록은 없다.

## REAL-QA-1 · 앱 실통합 시험 전 코드 갭 (검토 요청 전)

- 상태: 코드 읽기 전용 확인으로 발견. 상대 확인·공통 반영·VM 실행은 없음.
- 기존: `develop/sueon/src/app/(protected)/admin/tickets/page.tsx`는 로컬 `seed`와 `useState`만 사용하며 `/api/admin/tickets` 조회·PATCH를 호출하지 않는다. 관리자 로그아웃 링크는 `/login` 이동이다. 따라서 현재 UI만으로 실제 티켓 조회·상태/답변 저장을 증명할 수 없다.
- 기존: `develop/jihye/app/services/inquiries.py`의 `_list_requests`는 `Inquiry.result.ticket`을 반환하며 저장된 티켓의 최신 `status`·`reply`를 조회해 합치지 않는다. `GET /api/my-requests`는 관리자 변경 뒤에도 현재 상태·답변을 제공하지 않을 수 있다. 공통 C01의 본인 문의·답변·티켓 상태 목록 계약 및 `InquiryTicketView`의 status/reply 의도와 대조가 필요하다.
- 제안: 수언님이 관리자 티켓 페이지를 세션 기반 GET/PATCH API에 연결하고 실제 logout API를 호출한다. 지혜님이 본인 문의 목록에서 소유권이 확인된 앱 티켓의 최신 상태·답변을 안전하게 포함한다. 오현님은 실제 배포 버전·FE/API 준비를 확인한다.
- 영향: 관리자 메뉴/API 연계, 재로그인 후 직원 문의 UI의 현재 티켓 상태·답변, 이 작업의 실통합 합격 범위.
- 검토 상대: 수언님(FE), 지혜님(API/DB), 공통 계약 해석이 필요할 때 오현님. 각자 소유 파일만 수정한다.
- 실행: `tools/real-qa-api-runner.py`는 읽기 전용 preflight가 기본이며 실쓰기 모드는 예약 창 및 FE/계정 인계 환경 게이트를 요구한다. 이 runner는 HTTP API 시퀀스를 지원하지만 실제 브라우저 UI 확인과 DB 직접 count 증거를 대신하지 않는다.
- VM 쓰기·계정 생성/변경·배포·n8n 작업·외부 전달은 수행하지 않았다. 본 절은 검토 요청 초안이며 상대 동의나 수정 완료를 의미하지 않는다.
- 후속 재확인: 이 기록 뒤 shared worktree에서 수언님 관리자 티켓 UI의 API 연결과 지혜님 문의 목록의 현재 티켓 상태/답변 결합 변경이 관측됐다. 해당 변경은 아직 실제 통합 시험·VM 배포 근거가 없어 초기 갭은 **로컬 소스 후보 수정으로 보완 중, 실행 준비 미확인**으로 둔다. 이 문서 작성자는 해당 파일을 수정하지 않았다.
- QA runner 검토 반영: 기존 `attempt=3` 보완질문 한도 강제 입력을 제거했다. 기본은 VPN 첫 질문·attempt=1·context 없음이며 `--question`·`--attempt`·`--context`를 명시할 수 있다. 실제 route/source ID·score·API 경과시간만 기록하고 질문·context·답변 원문은 보고서에서 제외한다. 실제 route가 보완 질문이면 미완료로 종료하고 저장된 문의 재로그인 확인만 한다. ticket_id가 없으면 관리자 PATCH를 호출하지 않고 전체 PASS도 반환하지 않는다. curl 전송은 TLS 검증을 유지하고 redirect를 따르지 않는다. 요청 본문은 stdin, 계정 비밀번호 환경변수는 curl child에서 제거하며 cookie/raw response는 0700/0600 임시 저장소에 한정한다. mock subprocess 회귀 5개가 통과했고 실제 TLS/VM 연결은 미실행이다.
- 통합자 분리 인계: oc0.2는 FE/BE 통합·배포를 담당하고, 원민은 이번 후속에서 `tools/real-qa-api-runner.py` 전송 계층과 그 회귀 테스트만 인수했다. 실제 live/API 작업창은 시작하지 않는다.

## 실제 실행 후 보완 · 2026-11-06 11:52 KST

- 앞 절의 “실제 작업창 미시작” 및 FE/계정/배포 미확인은 runner 실행 전 시점의 기록이다. 이후 oc0.2가 main `99fff9c`의 FE/BE를 VM에 배포하고, 별도 FE guard fix `3ff836a`를 frontend-only 배포한 뒤 공개 HTTPS attempt 1 QA를 실행했다.
- `request_id=real-qa-36352d26c53e48eab65a42c4a0c5ec85`, `route=담당자 이관`, `sources=[]`, elapsed 7.341초. 인증/role·employee admin 403·문의 생성/직원 목록/재로그인·관리자 처리와 재조회 API sequence는 PASS. 이는 검색 성공/정상 자동답변/WF-01 8초 PASS가 아니다.
- 같은 고유 request_id로 독립 read-only DB 검증: inquiry 1행, matching ticket request_key 1행, `T-2005`; inquiry/ticket/requester ID 연결, `in_progress`, 관리 답변 일치. 전체 row count 증가분을 단건 증거로 쓰지 않았고, 기존/타인 데이터를 삭제하지 않았다. 자세한 비밀 없는 실행 결과는 `docs/EXECUTION-RESULT.md` 및 `daily/DAY81.md`에 있다.
- 브라우저 시각/클릭 검증은 자동화 host unavailable로 미실행. 공식 common-14, duplicate retry, alert/DLQ 연계, WF-01 normal answer/source evidence도 미실행이다.
