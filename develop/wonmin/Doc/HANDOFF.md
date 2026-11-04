# 원민님 · 변경 제안·전달 기록

최신 C04 검토: [C04-CONNECTION-REVIEW.md](C04-CONNECTION-REVIEW.md). 다혁님 `9bda763` 최신 개발본은 P0-2이며 C04 발신·응답 매핑 미구현. SPEC 표본 수신 적합과 로컬 6건 상태만 확인했고 실제 연결은 미실행이다.

최신 C05 검토: [C05-MODEL-REVIEW.md](C05-MODEL-REVIEW.md). 지혜님 `4bbbf49` 실제 모델에 요청 표본 7/7 적합, 중복 알림 ACK의 duplicate 직렬화 불일치 1건 확인. 실제 API/인증/DB는 미실행이다.

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

## P0 전달 자료 · 2026-11-04 (외부 전송 없음)

- 변경 파일: cases/team.json(12), handoff.json(13), app-integration.md(11절차), requests 6개, runs/INDEX.md 및 p0-validation.txt. README/TODO/IMP-PLAN에 실제 준비 상태 반영.
- 확인 방법/실제 결과: p0-validation.txt의 로컬 정적 확인. 서버·인증·DB·n8n·공통 평가 키트 기능 시험은 미실행. suite는 공식 도구 호환을 아직 주장하지 않는 P0 검토 명세다.
- 다혁님(C04): 팀 입력과 정상/중복/티켓 장애/알림 부분실패 기대를 준비했다. TM-09의 ok·알림 DLQ와 인증 거절 새 reason은 WM-04 미판정이다. 다음 P1-1에서 실제 handoff를 제공한다.
- 지혜님(C05): 신규 201/중복 200 및 ticket_id 동일, 소유권 거절, alert/DLQ 실제 ACK, 동시 1건과 재시작 유지의 관측이 필요하다. app 상세 ops는 아직 미확정이므로 제공할 관리자 API/마스킹 DB 관측으로 확인한다.
- 유빈님·오현님: 현재 저장소에는 실제 data-api 규정 8종 원문·관리자 문서 식별자·실제 권한 응답 및 인증 확인 근거가 없다. 제공 문서의 명세를 실제 확보로 간주하지 않았다. 실제 원본 확보 여부는 **미확인**이다. data-api 환경이 준비되면 유빈님 어댑터로 원본·권한 출처를 확보하고 TM-11/12 정답 문서를 고정해야 한다. 상대 폴더와 대장은 수정하지 않았다.
- 오현님(C09): 80일차 flow.py/common.json 원본 반입·배포 버전·해시·실행 환경 매핑이 필요하다. 과거 키트로 대체하지 않았고 공통 판정은 생성/수정하지 않았다.
- 문서 불일치 처리: 최신 공통 API §8에는 handoff 5초, tickets 최대 2회·각 1초, alerts/DLQ 각 1회·0.6초의 **초기 기본값**이 있다. 위 WM-01의 '공통에 없음'은 과거 제안 기록으로 읽는다. 현재 사례는 공통 초기값을 우선하며 backoff/Retry-After/내부 전체 기한의 제안은 계속 미판정이다. WM-02의 예시 dlq_id 응답도 확정 ACK로 사용하지 않는다.
- 다음 연결 상대: 다혁님·지혜님(C04/C05), 유빈님·오현님(실제 원본·키트). 본 기록은 전달 자료 작성이며 상대 검토/동의/실제 연결 완료가 아니다.

## P1-1 전달 자료 · 2026-11-04 (외부 전송·상대 확인 없음)

- 변경 파일: workflows/oke-handoff.json(15노드), tools/mock-store.py, tests/handoff.test.mjs·workflow-runner.mjs, requests/handoff-normal·high·duplicate.json, README·워크플로우 안내·TODO·IMP-PLAN·runs 증거.
- 확인 방법/실제 결과: 저장소 루트 `node --test` 40개 통과. 실제 HTTP Mock 두 인스턴스를 사용했고 원본 워크플로우의 Code·표현식·분기를 로컬 어댑터로 실행했다. 신규 201/중복 200, 순차 동일 ID, 동시 8건 중 신규 1/중복 7·저장 1건, high 유지와 알림 ACK, 설정 기반 단일 저장소 선택을 확인했다. 공식 check/n8n Header Auth·실행/실제 백엔드·DB/VM은 미실행이다.
- 다혁님(C04): 요청은 handoff-normal/high/duplicate.json 참조. 정상 C04는 기존 6필드이며 티켓에 입력 priority를 복원한다. 캐시 없이 C05를 호출하므로 중복 응답은 duplicate=true다. H01은 X-Team-Key Credential 연결 필요. 단일 H11 응답 경로이며 n8n 게시·실제 호출은 사람이 확인해야 한다.
- 지혜님(C05): request_id를 key로 보내고 신규 201+duplicate=false/중복 200+duplicate=true 및 ticket_id를 함께 확인한다. title은 제한된 개인정보/명시적 비밀값을 가리고 requester는 유지한다. Mock의 동일 key 본문/소유자 충돌은 409·티켓 미노출이다. 실제 UNIQUE·거래·소유권·동시성은 백엔드 구현 책임이며 현재 Mock 결과로 실제 DB를 보증하지 않는다.
- app 알림은 event_key=request_id:ticket-created를 보낸다. 로컬 Mock은 stored=0/count 유지/duplicate=true로 중복 ACK를 반환한다. 실제 백엔드에서 이 조합을 지원하는지 미확인이고 duplicate가 없으면 alerted=true로 추정하지 않는다. 지혜님 최신 원격 4bbbf49의 DTO도 읽기 대조했으며 실제 인증·저장이 아직 미구현인 것으로 문서에 기재되어 있다. 상대 테스트를 대신 실행하거나 승인하지 않았다.
- 미정 경계: C04 오류 필드 code는 추가하지 않았고 잘못된 입력은 400+일반 오류 메시지의 임시 외형이다. 알림만 실패하면 티켓 유지·alerts_down·alerted=false, ok=false를 보수적으로 반환하며 WM-04의 확정으로 간주하지 않는다. 설정 오류는 쓰기 없이 503. 이 응답의 세부 합의와 부분실패/DLQ는 후속 검증 대상이다.
- 범위/다음 단계: 티켓 자동 재시도·실패 시 독립 알림/DLQ는 P1-2, Error Trigger/실제 app 연결은 P1-3이다. 현재 dlq=false이며 티켓 실패는 tickets_down으로 안전 반환만 한다. 공통 WF-04 전체 수습을 통과한 구현은 아니다. practice 중복 알림 건수 정책도 WM-03으로 구분한다.
- 오현님(C07/C09): Credential placeholder 교체, SERVICE_MODE와 Mock/실제 주소 매핑, n8n의 모드/주소 $env 접근 확인, 공식 키트 반입과 사람이 check 후 게시/시험할 환경 준비가 필요하다. 원민 폴더 이외 및 루트/다른 팀원 코드는 수정하지 않았다.
- 다음 연결 상대: 다혁님 C04, 지혜님 C05, 오현님 키트·배포. 실제 증거는 runs/INDEX.md 참조.

## C05 모델 대조 · 2026-11-04 · 지혜님 4bbbf49

- 변경 파일: Doc/C05-MODEL-REVIEW.md, requests/c05-store-samples.json, tools/check-c05-models.py, runs/c05-jihye-4bbbf49-review.json 및 인계/색인 링크. 워크플로우·Mock·지혜님 코드·공통 계약은 변경하지 않았다.
- 확인 방법/실제 결과: fetch 후 지혜님 고정 커밋의 common/tickets/alerts 모델을 메모리로 읽고 uv.lock과 동일한 Pydantic 2.14.2로 실제 검증했다. 기존 Code 노드에서 추출한 티켓3·알림2, 후속 구현용 DLQ 계획2 표본은 7/7 필드 손실 없이 적합하다. DLQ는 현재 미전송이며 request_id=null은 허용, 필드 생략은 거절됨을 확인했다.
- **WM-C05-01 · 응답 불일치:** StoredResponse에는 stored/count만 있고 extra=ignore이므로 backend 결과의 duplicate=true가 제거된다. 원민 app H10의 중복 ACK는 stored=0/count>=1/duplicate=true를 요구하므로 직렬화 전 alerted=true에서 후 alerted=false/alerts_down으로 바뀜을 실제 모델/로컬 Code로 재현했다. count만으로 성공 판정하도록 완화하지 않았다.
- 지혜님·오현님 검토 항목: 중복 알림의 명시적 ACK 필드/의미를 공통 계약·응답 DTO로 확정할지 검토 필요. 선택 duplicate 또는 이벤트 저장 확인 경로는 제안이며 승인 아님. 현재 요청 DTO 변경 필요는 보이지 않는다.
- DLQ 상태 기대: 지혜님 현재 POST /dlq 라우터는 StoredResponse+기본200이다. 원민 SPEC의 신규201/중복200은 팀 공통 C05에 별도 확정되어 있지 않으므로 P1-2 전에 기대를 정리해야 한다. `dlq_id`를 실제 확정 응답으로 사용하지 않는다.
- 미확인: deps는 X-Api-Key 누락401/키 존재501, 기본 backend도501인 골격이다. 이는 코드 검토 결과이며 서버를 호출한 것이 아니다. 실제 키 대조·DB·멱등/동시성·알림/DLQ ACK 및 n8n 연결은 미실행이다.
- 다음 연결 상대: 지혜님(C05 DTO·응답), 오현님(공통 ACK/상태 정리). 본 문서는 검토 자료 작성이며 외부 전송·상대 동의/수정 완료로 표시하지 않는다.

## C04 연결 대조 · 2026-11-04 · 다혁님 9bda763

- 변경 파일: Doc/C04-CONNECTION-REVIEW.md, tools/check-c04-dahyeok.mjs, requests/c04-dahyeok-urgent.json, runs/c04-dahyeok-9bda763-review.json 및 문서 링크. 원민 워크플로우·다혁님 파일·공통 계약은 변경하지 않았다.
- 참조 대상: fetch 후 origin/feat/dahyeok-p0 고정 커밋 9bda7639aaeee3f6dca59f6aabd91e61fa05a847. oke-support.json은 P0-1 보존본, 최신 개발본은 oke-support-02.json(P0-2)이며 C04 구현은 상대 계획 P0-3이다. 상대 자체 flow.py는 공식 키트로 취급하지 않았다.
- 확인 방법/실제 결과: Git에서 JSON을 메모리로 읽어 기존 Code/표현식 어댑터로 로컬6건 실행. attempt1/2는 보완 질문, attempt3·긴급은 내부 handoff_mock이나 최종 ticket=null/reason=not_implemented다. context-resolved도 미구현 응답이며 injection은 차단이다. 6/6은 골격 상태 확인이고 공통 시나리오나 이관 기능 PASS가 아니다.
- **WM-C04-01 · 실제 연결 미구현:** 최신 본체에 발신 HTTP Request 노드가0개이고 N20 Prepare/Call/Map도 없다. 실제 C04 URL/Credential/timeout·결과 매핑 검증은 불가하다. SPEC의 긴급 C04 표본1개는 원민 H02에 적합하며 ID/requester/high를 유지했다. 문서 표본의 적합과 실제 생성/호출을 구분했다.
- 다혁님 후속 연결: 검증한 user→requester, ID 유지, title 마스킹·category/priority/reason, X-Team-Key Credential, 공통 초기 timeout5초·중첩 재시도0을 N20에 적용해야 한다. 정상 reason=null이면 본체 원래 이관 사유 유지, 실패 reason은 보존, 중복 ticket_id/priority/duplicate 보존이 필요하다.
- WM-04: 상대 SPEC의 alerts_down 예시는 ok=true, 원민 임시 구현은 ok=false이며 둘 다 ticket 보존을 요구한다. 향후 mapper에서 ok=false만 보고 확인된 ticket을 폐기하지 않도록 정책 확인 필요. 현재 mapper가 없어 실제 본체 버그나 합의 완료로 판정하지 않았다.
- 미확인/다음 상대: 다혁님 C04 실제 호출·매핑 구현, 오현님 게시 버전 선택·공식 키트·n8n 환경. 프로젝트 n8n 게시/웹훅/인증/Executions·저장소는 미실행이다. 다음 버전 제공 뒤 정상/중복/high/tickets_down/alerts_down/전송 실패를 실제 경로로 재확인한다. 본 기록은 외부 전송·상대 동의가 아니다.
