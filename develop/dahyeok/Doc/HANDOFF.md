# 다혁님 · 변경 제안과 전달 기록

[README](../README.md)의 상대 표와 [COORDINATION](../../../docs/COORDINATION.md)을 따른다. 기본안 적용에 사전 승인은 필요 없다. 공통 기준의 빈 부분에 대한 제안만 아래에 분리했다. **2026-11-03 문서 작성 상태이며 외부 요청 전송·상대 확인·공통 반영·실제 연결 확인은 모두 미실행**이다. 검토와 GitHub 반영은 상위 담당자가 한다.

`DH-CHG-*`는 변경 제안 ID이며 SPEC의 `SUP-*`, 개인 검증의 `DH-T-*`, 공통 시험의 `WF-*`와 다르다. 상대는 자기 HANDOFF에 검토 결과를 남기며 응답이 없다는 이유로 동의로 처리하지 않는다.

## 연결 상태

| 연결 | 검토 상대 | 현재 상태 |
| --- | --- | --- |
| C02 | 지혜님 | DH-CHG-01/02/03/04 제안 작성, 미전송·미검토 |
| C03 | 유빈님 | DH-CHG-03 시간 예산 제안, 실측·실연결 없음 |
| C04 | 원민님 | DH-CHG-03/04 제안, 실연결 없음 |
| C08 | 원민님 | 원본 판정·중복·장애·측정 검증 미실행 |
| C09 | 오현님 | 공통 문서 보완 검토 요청안, 미반영 |

기준은 docs/API-CONTRACT.md 1·3·4·8절과 docs/DATA-AND-DB.md 3·4절이다. 공통 문서는 오현님만 반영한다. 아래의 경로는 수정 요청 대상 또는 미래 생성 경로이며 현재 존재하는 구현 파일의 링크가 아니다.

## DH-CHG-01 · 공통 입력의 추가 오류 코드와 context 제한

- 연결 / 요구: C02·C08 / SUP-01/02/04.
- 기존: request_id는 필수 1~64자, attempt는 1 이상 정수, context는 이전 답이다. 빈 질문/501자/미등록 직원의 question_required·too_long·unknown_user는 적용 가능하다. request_id·attempt·context의 타입/상한 위반에 대한 정확한 codes와 context 상한은 공통에 명시되지 않았다.
- 제안: HTTP400 `{"error":"invalid request","codes":[...]}` 형식은 유지한다. request_id 누락/타입·범위 오류는 `request_id_required`/`invalid_request_id`, question 비문자열은 `invalid_question`, attempt 비정수·1 미만은 `invalid_attempt`, context 비문자열/상한 초과는 `invalid_context`/`context_too_long`으로 추가한다. context 상한 후보는 2,000자이며 초과분을 조용히 자르지 않는다. user 타입 오류는 unknown_user로 처리하는 안을 검토한다.
- 재현/예상: `{"request_id":"dh-bad-attempt","user":"박서연","question":"VPN 오류","attempt":0}` → 제안 기준 HTTP400 codes=[invalid_attempt], LLM 0. 공통 WF-13의 기존 기대값은 그대로 둔다.
- 영향: 지혜님 입력 검증과 본체 Code의 코드/길이/타입 검사가 같아야 한다. 프론트가 보완 context를 무한 누적하지 않도록 안내가 필요하다. request_id·기존 3개 code·route는 변경하지 않는다.
- 검토 상대 / 공통 반영: 지혜님(C02), 원민님(C08), 오현님(API-CONTRACT 1절). 2,000자는 확정된 사용자 요구가 아니라 검토 후보다.
- 계속할 작업: 확정된 입력 범위·WF-13·규칙 차단과 나머지 Agent 구현. 신규 codes는 Mock 기대 후보로만 구분하고 확정 계약으로 배포하지 않는다.
- 상태: 제안만 작성. 상대 확인·반영·재시험 없음.

## DH-CHG-02 · 결과 재사용 API·소유권·동시 처리 경계

- 연결 / 요구: C02·C08 / SUP-08/09.
- 기존: 웹 신원·request_id 소유권은 FastAPI, app.inquiries의 request_id UNIQUE 및 result/context 저장, 티켓 request_key UNIQUE는 확정이다. 본체가 기존 result를 읽고 완료 결과를 저장하는 내부 경로·처리 중 응답·같은 ID의 다른 내용 처리 규칙은 없다. 본체 메모리는 재시작/동시성 보장이 아니다.
- 제안: app 모드에서는 지혜님 소유 FastAPI 내부 API를 X-Api-Key로 호출한다. 후보 경로는 GET `/internal/inquiries/{request_id}/result?requester={name}`, PUT `/internal/inquiries/{request_id}/result`다. 읽기는 완료 200 `{"state":"done","result":{}}`, 처리 중 202 `{"state":"processing"}`, 없음 404, 타인 소유 403으로 구분한다. PUT에는 검증한 requester와 result를 보내고 소유권·request_id 일치를 서버가 확인한다. result={}는 형식 표기이며 실제로는 공통 응답 전체다.
- 제안: 같은 user+ID라도 question/attempt/context가 달라지면 HTTP409 request_conflict, 동일 내용 처리 중 재전송은 중복 실행 없이 bounded wait 후 HTTP409 request_in_progress로 처리하는 안을 검토한다. 원자적 실행 소유권 확보는 백엔드 트랜잭션에서 담당하고, 본체의 조회→생성 두 호출만으로 경쟁을 해결했다고 하지 않는다. 이 409 정책은 아직 공통 확정이 아니다.
- practice 경계: 제공 data-api 캐시를 쓰더라도 순차 결과 재사용과 영속/원자 보장을 구별한다. 동시 티켓 중복은 이미 정한 하위 key 멱등으로 방지한다. 제공하지 않은 cache 원자 연산·TTL·새 DB 스키마를 본체가 있다고 가정하지 않는다.
- 재현/예상: 같은 ID/같은 직원의 순차·동시 전송과 처리 후 재시작, 다른 직원의 같은 ID를 각각 확인한다. 티켓 수 1, 타인 응답 0, 완료 결과 재사용 여부를 별도 기록한다. 새 보완 차례는 새 ID라는 기존 기준은 바꾸지 않는다.
- 영향: 백엔드 내부 API/동시성 처리·본체 N05/N22 adapter·practice/app 전환·원민님 관측에 영향. app.inquiries 저장 책임이나 기존 티켓 키 제약은 옮기지 않는다.
- 검토 상대 / 공통 반영: 지혜님(C02), 원민님(C08), 오현님(API-CONTRACT·필요 시 DATA-AND-DB).
- 계속할 작업: 재사용 adapter는 fixture의 hit/miss/forbidden/processing/실패로 작성하고 나머지 필수 작업 진행. P1-4에서 실서비스 보장이 필요한 부분만 미확인으로 남긴다. API를 본체 폴더에서 구현하지 않는다.
- 상태: 제안만 작성. 내부 API 존재·저장/동시성 성공을 확인하지 않았다.

## DH-CHG-03 · 호출 시간 예산·장애 응답 경계

- 연결 / 요구: C02·C03·C04·C08 / SUP-05/07/09/10.
- 기존: timeout과 오류 출력, search 503/search_unavailable, handoff 200/tickets_down·alerts_down은 확정이다. 본체/백엔드 전체 deadline, 각 하위 timeout·재시도 수, 직원 조회 불능·handoff 응답 유실의 외부 응답은 미정이다. 참고 문서의 6초/8초는 프로젝트 SLA 확정값이 아니다.
- 제안: 본체의 예상 오류는 HTTP200 공통 7필드로 안전 종료한다. 직원 조회 장애는 unknown_user 400으로 위장하지 않고 route=담당자 이관, ticket=null, reason=identity_unavailable 및 "직원 정보를 확인하지 못해 접수하지 못했습니다"로 응답하며 검증되지 않은 requester로 handoff를 호출하지 않는다. handoff 응답 timeout/전송 실패는 같은 route, ticket=null, reason=handoff_unavailable 및 접수 결과 확인 불가 안내로 처리한다. 실제 티켓이 생성됐을 수 있으므로 재전송은 같은 ID다.
- 제안: 본체의 search/조회 전송은 초기 자동 재시도 0회, 생성 재시도는 본체가 중첩하지 않고 handoff 소유 정책에 둔다. 400/401/403/404는 재시도 0회, 429는 Retry-After가 남은 deadline에 맞는 경우에만 추가 시도를 검토한다. 하위 실패를 무조건 성공으로 바꾸지 않는다.
- 시간 측정안: 원본 common.json의 케이스별 max_seconds를 먼저 확인해 변경 없이 사용한다. 직원/조회 timeout 후보 500·1,000·2,000ms, search/handoff 후보 2,000·4,000ms, Agent 후보 3,000·8,000ms를 **Mock 지연 실험 후보**로 비교한다. 운영 설정값·통과 목표가 아니다. 단계별 실측과 실패율을 모아 원본 판정 안에 들어가는 조합만 제안한다.
- 예산 계산: 최악 시간은 직원+재사용+triage+search+ticket+writer+verifier+handoff(해당 경로만)+출력/기록+재시도 대기 합이다. executionOrder v1의 두 갈래 시간을 합산한다. 총 deadline과 남은 handoff 예산을 검사해 시간이 부족하면 새 Agent/재검색을 시작하지 않고 안전 종료하는 안을 검토한다. FastAPI 호출 제한은 본체의 종료 예산과 네트워크 여유를 포함해야 한다.
- 재현/예상: search 503/지연, 직원 조회 장애, 접수 조회 8초 지연, handoff가 저장 후 응답만 유실, 하위 401/403, LLM 중단을 각각 시험한다. HTTP/route/사유·실제 시간·티켓 수·하위 호출 횟수를 기록한다. 미검증 수치를 PASS로 적지 않는다.
- 영향: 웹 timeout 안내·본체 HTTP/Agent 설정·검색 처리·handoff 재시도와 알림/DLQ 관측이 함께 맞아야 한다. 하위가 응답하지 않으면 alerted/dlq를 성공이라고 추정할 수 없다. 예상 밖 버그는 별도 oke-errors다.
- 검토 상대 / 공통 반영: 지혜님(C02), 유빈님(C03), 원민님(C04/C08), 오현님(API-CONTRACT 1·3·4·8절). 실제 수치는 SPEC 9절 측정 뒤 결정한다.
- 계속할 작업: 각 하위의 확정된 성공/빈 결과/장애 payload와 오류 출력은 그대로 구현한다. 미정 장애/시간은 Mock으로 경계를 확인하고 실제 통합 결과와 구분한다.
- 상태: 제안만 작성. timeout·처리시간 보장·알림/DLQ 성공 미확인.

## DH-CHG-04 · 중복 응답의 ticket 동일성과 duplicate 표시

- 연결 / 요구: C02·C04·C08 / SUP-08.
- 기존: 공통 설명은 같은 요청에 "저장된 결과 그대로", WF-09는 "티켓 1건(duplicate:true), 두 응답의 ticket 같음"을 요구한다. C04/C05는 신규 duplicate=false, 재시도 true다. ticket 전체 깊은 비교와 duplicate 변경을 동시에 요구하면 충돌할 수 있다. 원본 common.json의 실제 비교 방식을 확인하지 않았다.
- 제안: 첫 신규는 실제 false, 재시도는 실제 true를 보존하고 동일성은 ticket_id·priority 및 생성 수 1로 해석하는 안을 검토한다. 결과 캐시 재응답이면 재생성 없이 duplicate=true로 표시하되 저장 원본을 덮지 않는 방식을 검토한다. 이 해석이 원본 판정과 맞는지 원민님이 먼저 확인한다.
- 재현/예상: 같은 이관 요청 ID로 두 번 보내 첫/둘째 응답 전체 ticket, 실제 생성 수, 캐시 hit·하위 호출 횟수를 나란히 남긴다. 원본이 deep equality와 서로 다른 duplicate를 동시에 요구하면 불일치를 오현님에게 전달한다. 통과를 위해 common.json 기대값을 바꾸지 않는다.
- 영향: 본체 재사용 응답 매핑·FastAPI 저장 응답·handoff duplicate 보존·원민님 판정에 영향. 티켓 하나라는 불변 조건과 하위 멱등 계약은 그대로 유지한다.
- 검토 상대 / 공통 반영: 원민님(C04/C08), 지혜님(C02), 오현님(API-CONTRACT 1·4절). 공통 판정 변경이 필요한지는 상위 담당자가 확인하며 개인이 변경하지 않는다.
- 계속할 작업: ticket_id·생성 수·원본 duplicate를 기록하고 멱등 호출은 그대로 구현한다. 충돌하는 표시 해석을 협의 완료로 쓰지 않는다.
- 상태: 제안만 작성. 원본 시험 실행·상대 확인·공통 해석 확정 없음.

## 인계·확인 기록 원칙

P0 기반 → P1 필수 MVP(후속 P1-4 중복/동시성·P1-5 실제 통합/시험/측정 포함) → P2 선택 고도화 순서다. 상대 구현이 없으면 계약 Mock으로 계속 진행한다. 새 보완 요청 때문에 필수 작업 전체를 보류하지 않는다.

## P1-1 C03·본인 조회·C04 읽기 전용 대조 · 2026-11-05

- `workflows/oke-support-07.json`에서 C03 요청은 검증된 부서로 `all`/`all,it`을 선택하고 `top_k=3`으로 고정한다. 검색 빈 결과·503, 본인 조회 403·404·장애를 분리하며 연락처는 병합 전에 제거한다. 현재 하위 호출은 모두 Mock이다.
- 원민님 원격 `feat/wonmin-p0`의 P1-1 `oke-handoff.json`·정상/중복 요청을 읽기 전용으로 대조했다. C04 필수 입력 6필드와 신규/중복 ticket 형식은 호환된다. 알림 실패의 `ok=false`, ticket 보존, `reason=alerts_down` 조합과 503/tickets_down을 `07`에 반영했다. 원민님 실제 확인·통합 시험·공통 반영 완료를 뜻하지 않는다.
- 연결 시 확인 요청: 유빈님은 C03 실제 HTTP 상태/본문과 권한 필터, 지혜님은 GET `/tickets/{id}?requester=`에서 세션으로 확인된 이름 사용·403/404/장애 응답, 원민님은 C04 알림 ACK와 정상·중복 응답을 실제로 확인해 주셔야 한다. n8n Merge가 두 분기에서 각 한 항목을 내는지도 실제 실행으로 확인해야 한다.

## P1-2 writer·verifier Mock 인계 · 2026-11-05

- `oke-support-08.json`은 허용 evidence와 가린 본인 조회만 writer 입력에 전달하고, 출처 위조·잘못된 JSON·불리언 타입·검증 실패를 자동 답변에서 제외한다. 로컬 Mock에서 0.8을 분기값으로 사용했으나 검색 품질 측정이나 공통 기준 확정은 아니다.
- 유빈님께는 실제 문서·권한별 검색 근거의 doc/section/score와 점수 분포, 원민님께는 검증 실패·근거 부족·연락처 가림 사례의 기대값 대조를 요청한다. 점수 임계값 확정은 품질 측정과 공통 반영 후에 진행한다. 현재 상대 확인·실제 Agent 실행·공통 시험은 미실행이다.

## P1-3 긴급 선이관 Mock 인계 · 2026-11-05

- `oke-support-10.json`은 high 문의에서 C04 Mock을 먼저 한 번 실행한 뒤 `security-incident` 합성 검색 근거와 성공한 본인 티켓 상태를 보강한다. 부가 단계 실패·타인 조회 403에도 기존 high 이관 결과를 유지한다. 로컬 `cases/support-failures.json` 14/14에서 같은 실행의 C04 Mock 1회를 확인했다.
- 원민님 `8b1fd74`의 C04 페어링 검증 17/17은 당시 다혁 `08`의 요청·매핑 경계 결과다. `10`의 새 그래프·실제 C04 HTTP·서로 다른 실행의 동일 ID 멱등성까지 확인한 결과로 확대하지 않는다. 실제 n8n 연결 시 선이관 후 Merge가 단일 응답으로 끝나는지와 최초 티켓 ACK를 잃지 않는지 재검증이 필요하다.

## DH-CHG-05 · 단계별 워크플로우 JSON 보존과 게시 대상

- 연결: C09. 2026-11-04 사용자 요청에 따라 P0-1 원본은 `workflows/oke-support.json`으로 복원하고 P0-2는 `workflows/oke-support-02.json`에 보존했다. 원격의 P0-2 수정 이력은 강제 삭제하지 않고 새 커밋에서 파일 배치를 바로잡는다.
- 영향: 번호판 JSON의 내부 이름·POST 웹훅 경로는 모두 `oke-support`다. n8n에서 동시에 활성화하면 경로가 충돌하므로 기록용 JSON을 함께 게시하지 않는다. 최신 개발본 경로는 `workflows/README.md`를 따른다. 프로젝트 n8n 게시·시험은 미실행이다.
- 오현님 전달 내용: 최종 완성 시점에 공식 제출/게시본을 `develop/dahyeok/workflows/oke-support.json`으로 단일 정리하고 현재는 번호판을 유지한다. 실제 정리·공통 문서 반영은 아직 하지 않았다.

실제 검토/연결 후에만 해당 제안에 상대 HANDOFF 링크, 확인 날짜·내용, 공통 반영 절·커밋, 재현 입력·예상/실제·보고서 경로를 추가한다. 현재는 모두 미확인이다. 버그는 실행 위치/버전·마스킹 로그·재현 입력을 자기 기록에 추가하고 파일 소유자가 수정한다. 외부 메시지는 이번 작업에서 전송하지 않는다.
