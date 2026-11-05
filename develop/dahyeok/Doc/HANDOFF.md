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

## P1-4 결과 재사용 Mock 인계 · 2026-11-05

- `oke-support-11.json`에서 N05 replay hit/miss/forbidden/conflict/processing/unavailable을 합성 응답으로 분리했다. 같은 ID·검증된 직원·내용의 hit는 캐시 결과를 재사용하며 C04 Mock을 호출하지 않는다. 타인·내용 충돌·처리중·조회 장애·잘못된 캐시는 새 이관을 막는다. `cases/support-replay.json` 로컬 13/13이다.
- 지혜님 `fdcd265`에는 DH-CHG-02의 내부 결과 조회·저장 API가 없으므로 이 결과는 영속 저장/원자 중복 방지 시험이 아니다. 실제 연결 전 requester 검증, question/attempt/context 지문, 완료/처리중/충돌 상태, 저장 ACK와 API 경로를 지혜님·오현님이 확정해야 한다. 현 로컬 Mock의 충돌 HTTP400/invalid_request 및 처리중·장애 안전 응답은 임시 판정이다.
- 원민님·오현님께는 재사용 응답의 ticket_id/priority 동일성과 duplicate=true 표시를 DH-CHG-04 및 원본 WF-09 판정과 대조 요청한다. 캐시 hit의 duplicate 표시는 저장 원본을 바꾸지 않는 로컬 제안이다. 순차·동시·재시작 후 실제 티켓 1건은 원민 C04/C05와 백엔드 DB를 연결해 검증해야 한다.

## P1-5 HTTP 연결 준비 1단계 인계 · 2026-11-05

- 최신 번호판 `workflows/oke-support-12.json`에 직원 GET `/employees`, C03 POST `/webhook/oke-search`, 본인 티켓 GET `/tickets/{id}?requester={검증된 이름}`, C04 POST `/webhook/oke-handoff` 경로를 추가했다. `SERVICE_MODE=practice|app`에서만 해당 경로를 선택하며 누락·오류 설정은 직원 확인에서 안전하게 종료한다. 실제 Credential 값은 JSON에 없다.
- 지혜님/오현님: 프로젝트 n8n의 `SERVICE_MODE`, `DATA_API_URL`, X-Api-Key Header Auth Credential과 직원 6명 응답의 `{items:[{name,dept}]}` 형식, 본인 티켓 조회 200/403/404·장애 응답을 확인 부탁드린다. 실제 응답 형식이 다르면 어댑터를 조정해야 한다. DH-CHG-02의 결과 조회·저장 API는 이 번호판에도 연결되지 않았다.
- 유빈님: C03의 X-Team-Key Credential, 200 빈 근거·503 상태와 본문을 확인 부탁드린다. 원민님: C04의 X-Team-Key Credential, 신규/중복·alerts_down·tickets_down 응답을 확인 부탁드린다. 동일 request_id의 실제 저장 멱등은 C04/DB와 함께 별도 시험이 필요하다.
- 합성 HTTP 어댑터 검사 12/12와 최신 번호판의 로컬 Mock 사례 56/56(13+14+9+20)을 확인했다. 이 수치는 실제 HTTP·n8n 실행이나 공식 `flow.py` 결과가 아니다. 사람이 Credential을 연결하고 프로젝트 n8n에서 한 버전만 게시·시험한 실행 ID/마스킹 결과를 받아야 실제 연결 완료로 기록한다. 실제 Agent 답변 품질 임계값도 미확정이라 자동 답변 검증 완료로 표시하지 않는다.

## P1-5 로컬 n8n 실제 실행과 버그 수정 · 2026-11-05

- 실행 위치: 개인 로컬 n8n 2.42.6(`SERVICE_MODE=practice`, `DATA_API_URL=http://data-api:8800`, `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`), 제공 data-api, triage Agent는 로컬 OpenAI Credential(gpt-4.1-mini). 팀 VM·프로젝트 n8n 결과가 아니다. 로컬 Header Auth 키는 n8n Credential에만 두고 저장소에 넣지 않았다. `oke-search`·`oke-handoff`는 아직 없어 C03/C04는 404였다.
- `oke-support-12.json` 실행에서 찾은 버그를 `oke-support-13.json`에 수정했다(12는 원본 보존):
  1. N03 Capture employee: 제공 data-api `/employees`는 `{employees:[{name,dept}]}`인데 `{items:[...]}`만 받아 정상 직원도 `직원 정보를 확인하지 못해`로 끝났다. 두 형식을 모두 받도록 고쳤다.
  2. N01 Support webhook: `webhookId`가 없어 CLI import 시 `/webhook/oke-support`가 아닌 `{workflowId}/n01 support webhook/oke-support`로 등록됐다. 고정 webhookId를 넣었다. 편집기 import는 자동 부여되어 영향이 없었다.
  3. N06 Triage Agent 프롬프트: 실제 LLM이 "VPN이 계속 끊겨요. 어떻게 해야 하나요?"를 `needs_action=true`로 바로 이관하고, 증상이 적힌 질문에도 보완 질문을 했다. needs_action은 IT팀 조치 요청에만, missing은 대상조차 모르는 질문에만 쓰도록 Mock 기준과 맞췄다.
  4. N06 Parse triage: LLM이 `처리 상태`·`증상` 등 정해지지 않은 missing을 내 T-ID 상태 문의가 보완 질문으로 갔다. 허용 3개(`접속 대상`·`오류 메시지`·`발생 시점`)만 남기고 ticket_id가 있으면 missing을 비운다.
  5. N07 Route triage: 정해지지 않은 missing 문구가 "오류을 알려주세요"로 조사가 틀렸다. `'값' 정보를 알려주세요.`로 바꿨다.
- 로컬 검사(12·13 동일): `http_adapter_check.py` 12/12, `retrieval_check.py` failures 14/14·replay 13/13·review-fixes 9/9·verification 20/20, ticket-lookup 6/6. 검사기는 `--node-container`로 n8n 컨테이너의 Node.js를 사용했다.
- 단계별 사례 파일 적용 범위: 이전 단계용 파일은 해당 단계 번호판의 기대값이며 12·13에는 적용하지 않는다. 기대값은 바꾸지 않았다.
  - `support-input`(P0-1)은 `flow.py test-local`로 `oke-support.json` 6/6. 12·13에서는 P0-1의 `not_implemented` 기대 때문에 4/6이다.
  - `support-triage`·`support-handoff`(P0-2·P0-3)는 `flow.py` 형식이라 `retrieval_check.py`에서 TypeError가 난다. `flow.py test-local`로 02 triage 9/9, 03 handoff 17/17이다.
  - `support-retrieval`·`support-search`(P1-1)는 07에서 21/21·7/7이다. 08부터 writer·verifier가 추가되어 근거 found가 `자동 답변`으로 가므로 P1-1의 `low_confidence` 이관 기대 3건(R03·R21·S04)이 맞지 않는다. 같은 경로는 `support-verification`(P12-01·02)·`support-review-fixes`가 현재 기대로 검사한다.
  - 12·13의 적용 검사는 위 adapter와 failures·replay·review-fixes·verification·ticket-lookup이며 모두 통과했다.
- 13 실제 실행(execution 1553~1577, 25건 모두 success, `requests/*.json`에 `-l12`를 붙인 ID):
  - 인증: 키 없음·틀린 키 403.
  - 입력: 빈 질문·501자·미등록 직원 HTTP400 `question_required`/`too_long`/`unknown_user`.
  - 주입: `차단`, Agent 0회. 타인 T-1002: 티켓 조회 forbidden, `권한 없음`, 상태 미노출.
  - 보완: clarify-1·2·context `보완 질문`, clarify-3(attempt 3) `담당자 이관`.
  - 나머지 16건: triage 후 C03 404 → search_unavailable → C04 404 → `ticket:null`과 "접수 결과를 확인할 수 없습니다" 응답. 접수 완료로 표시하지 않았다. 본인 T-1002 조회 ok 3건은 `masked:2`.
- 미확인: C03 실제 근거, writer·verifier 실제 실행(검색 통과 0건이라 미실행), 티켓 생성·중복(WF-09), LLM 장애(`llm-down`은 장애 주입 없이 정상 호출됨), 긴급 알림, 답변 품질 임계값. triage는 LLM이라 반복 실행 결과가 달라질 수 있어 3회 반복 측정이 남았다.
- 다음: 유빈님 `oke-search.json`, 원민님 `oke-handoff.json`을 로컬 n8n에 import해 13으로 같은 요청을 재실행한 뒤 Mock 제거판(14)을 만든다. 지혜님께는 제공 data-api `/employees`가 `employees` 키라는 점을 공유하고, FastAPI 쪽 형식이 `items`로 유지되는지 확인을 부탁드린다.

## P1-5 로컬 C04 연동 1단계 · 2026-11-05

- 대상: 원민님 `origin/feat/wonmin-p0` `e249957`의 `workflows/oke-handoff.json`을 `git show`로 꺼내 Credential ID만 바꾼 사본을 로컬 n8n에 import·게시했다. 원민님 파일·작업 트리는 바꾸지 않았다. practice 저장소는 기본값 `http://data-api:8800`, Credential은 `WONMIN_X_TEAM_KEY`(본체 C04 키와 같은 값)·`WONMIN_PRACTICE_STORE_AUTH`·`WONMIN_APP_STORE_AUTH`(로컬 값). `oke-errors`는 연결하지 않았다. C03은 여전히 없음(404).
- C04 직접 호출: 인증 없음 403. 같은 request_id 2회 → `T-2001` duplicate false→true, `/tickets-created` 0→1.
- 13 경유(execution 1580~1594, 모두 success): urgent·urgent-complex는 high 티켓 신규(`T-2002`·`T-2003`), clarify-3(attempt 3)·input-valid(C03 404)는 normal 티켓, duplicate 2회는 `T-2006` duplicate false→true(WF-09 형태). other-ticket `권한 없음`·injection `차단`은 티켓 0. 서로 다른 요청 5건에 티켓 5건, urgent-complex 재전송은 duplicate=true로 추가 생성 없음. 긴급 선이관 뒤 C04 재호출 0회.
- 알림: data-api `/alerts`에 티켓마다 H06 알림 저장, duplicate 재전송도 알림 1건 추가(원민님 README의 practice 중복 알림 허용 범위). DLQ 0건.
- 확인 필요(13 본체): urgent-complex(WF-12)는 본인 T-1002 조회가 ok였으나 C03이 없어 writer가 실행되지 않았고 응답은 "IT팀 티켓이 접수되었습니다."뿐이다. WF-12의 본인 상태 안내가 근거 없이도 나와야 하는지 C03 연결 후 재확인한다. 실제 모드에서도 내부 decision 값이 `handoff_mock`으로 남아 있어 이름 정리가 필요하다(응답 영향 없음).
- 미확인: tickets_down·alerts_down·DLQ·영구 거절·지연 저장 장애 경로, `oke-errors` 연동, app 모드, C03 실제 근거와 writer·verifier.

## 13 수정: 본인 티켓 상태 안내 경로 · 2026-11-05

- 이유: 7교시 VM 시연 [본인 조회 정상]과 WF-07. 기존 13은 본인 T-1002 조회가 ok여도 규정 검색 근거가 없으면 N20 이관으로 새 티켓을 만들었다(로컬 재현: 박서연 "T-1002 처리 상태를 알려주세요" → 담당자 이관, 새 T-2007). 상태 문의는 규정 문서에 근거가 없어 C03 연결 뒤에도 같은 결과가 된다.
- 변경 노드(노드·연결선 수 변화 없음, 이전 13은 git `c151c8b`):
  1. N12 Evidence gate: 티켓 ID가 있고 본인 조회 ok이며 질문이 처리 상태/상황/현황을 묻고 사용할 규정 근거가 없을 때만 `decision=ticket_status`. 근거가 있으면 기존 writer 경로를 유지한다. 긴급 보강·타인(forbidden)·없는/장애 조회는 기존과 같다.
  2. N20 Prepare handoff: `ticket_status`는 이관하지 않는다.
  3. N22 Finalize: `자동 답변`, sources=[], ticket=null로 티켓 ID·제목·상태·갱신일을 안내한다. 연락처를 물으면 본인 전화만 `앞3-****-뒤4`로 가려 안내하고 이메일·note·담당자는 내보내지 않는다.
  4. N10 Normalize ticket: 상태 안내용 title(가림 적용)·updated와 `phone_hint`를 만든다. N13 Prepare writer는 `phone_hint`를 writer에 넘기지 않는다.
- 로컬 검사: adapter 12/12, failures 14/14·replay 13/13·review-fixes 9/9·verification 20/20·ticket-lookup 6/6. 첫 시도에서 근거가 있는 본인 티켓 사례(P12-15)를 가로채 실패해 근거 없음 경우로만 좁혔다.
- 로컬 n8n 실행(execution 1599~1609, 모두 success, C04는 원민님 handoff, C03 없음):
  - 박서연 T-1002 상태 → `자동 답변` "T-1002 (VPN 인증서 재발급) 문의는 현재 '처리 중' 상태입니다…", 새 티켓 0.
  - 이준호 T-1002 → `권한 없음`.
  - 최유진 "T-1003 처리 상황과 제 연락처 알려주세요"(WF-07) → `자동 답변`, 연락처 `010-****-2135`, masked 2, 새 티켓 0.
  - 회귀: T-9999 없음·긴급 복합·일반 문의는 기존대로 이관(티켓 3건), clarify-1 보완 질문, injection 차단.
- 남은 확인: agents 값은 `["triage"]`로 두었다(조회 단계 이름은 공통에 없음). 상태 문의 판정은 정규식이라 다른 표현("T-1002 끝났나요?")은 기존 이관으로 간다. VM의 실제 티켓 형식이 data-api와 같은지 시연 전에 확인한다.

## 13 + C04 장애 경로 로컬 시험 · 2026-11-05

- 원민님 최신 `origin/feat/wonmin-p0`(`90f02aa`)의 `oke-handoff.json`은 시험한 `e249957`과 바이트 단위로 같다. 이후 커밋은 문서·배포·실행 기록만 바꿨으므로 C04 연동 결과는 최신 버전에도 해당한다. 원민님 TEAM-REDEPLOY-RESULT에 따르면 원민님 Ubuntu lab에도 `859e3af`의 13이 게시되었고, 직원 API가 없어 정상 질문은 `identity_unavailable`로 끝났다.
- 방법: 로컬 data-api `POST /admin/fault`로 장애를 켜고 13에 `input-valid`·`slow-ticket` 요청을 보낸 뒤 스위치를 모두 `ok`로 되돌렸다(종료 후 확인). 티켓·DLQ·알림 수는 `/tickets-created`·`/dlq`·`/alerts`의 전후 차이다. 알림 장애 스위치는 data-api에 없어 alerts_down은 시험하지 못했다.

| 장애 | 13 응답 | 실제 저장 변화 | 판정 |
| --- | --- | --- | --- |
| tickets=error | 4.3초, 담당자 이관, `tickets_down`, ticket=null, "티켓을 접수하지 못했습니다" | 티켓 0, DLQ 1, 알림 1 | WF-04 기대와 같음 |
| tickets+dlq=error | 1.7초, 위와 같은 응답 | 티켓 0, DLQ 0, 알림 1 | 접수 성공으로 표시하지 않음 |
| tickets=flaky(키별 첫 시도 실패) | 2.1초, 담당자 이관, ticket `T-2011` | 티켓 1, 알림 1 | C04 재시도로 성공 |
| tickets=slow 8초, 일반 이관 | 3.9초, `tickets_down`, ticket=null | **티켓 1**, DLQ 1, 알림 1 | 아래 확인 필요 |
| tickets=slow 8초, 본인 T-1002 상태(WF-11) | 6.0초, 담당자 이관, `tickets_down` | 티켓 1, DLQ 1, 알림 1 | 제한 시간 안 응답. 본인 조회 2초 timeout 뒤 이관 |

- 저장 지연 시 C04는 시간 초과로 `tickets_down`을 주지만 data-api는 늦게 티켓을 만든다. 기존 본체는 "티켓을 접수하지 못했습니다"라고 단정했다.
- 결정(2026-11-05, 원민님 동의를 사용자가 전달): B안. C04·공통 계약은 바꾸지 않고, 본체 N22 Finalize의 `tickets_down` 문구를 "티켓 접수 여부를 확인하지 못했습니다. 같은 요청 ID로 다시 확인해 주세요."로 바꿨다. reason은 `tickets_down` 그대로다. 시간 초과를 별도 reason으로 나누는 안은 계약 변경이라 필요할 때 따로 제안한다.
- 수정 후 확인(로컬 Mock 검사 결과 동일, n8n 재게시 `okeSupport13Loc7`): tickets=error → 새 문구, 티켓 +0. tickets=slow → 새 문구, 늦은 티켓 +1. 같은 request_id 재전송 → 담당자 이관, 같은 `T-2014` `duplicate:true`로 새 티켓 없이 기존 접수를 확인했다. 스위치는 모두 ok로 되돌렸다.
- 미시험: alerts_down(스위치 없음), `oke-errors` 연동, 영구 거절(400/401/403/409), 429·Retry-After.
- 재시도 시험(로컬, 스위치 종료 후 ok 복구):
  - 저장 장애 중 같은 request_id 3회 → 매번 새 문구, 티켓 0. 복구 후 같은 ID → `T-2015` 신규. 한 번 더 → `T-2015` duplicate=true.
  - 저장 지연 중 매번 새 request_id 3회 → 응답은 모두 "확인하지 못했습니다"였지만 지연이 끝난 뒤 티켓 3건이 생겼다.
  - 결론: 본체·C04는 같은 ID 재시도에 티켓 1건을 보장한다. 웹의 "다시 시도"가 새 ID를 만들면 중복 티켓이 생기므로, 화면(수언님)·백엔드(지혜님)가 공통 계약대로 이전 request_id를 재사용하는지 확인 요청한다.
  - 같은 ID 재시도도 triage를 다시 실행하므로 분류가 달라질 수 있다. 이를 막는 결과 재사용은 DH-CHG-02 API가 없어 Mock이다.

## 13 수정: WF-12 긴급 보안 사고 초동 조치 안내 · 2026-11-05

- 근거: 팀장님 공지(2026-11-05). `security-incident.md`는 IT 전용이라 일반 직원 검색 근거로 쓸 수 없다. 보안 사고는 triage에서 즉시 긴급 이관하고, 사용자에게 기본 초동 조치(사내망 분리 안내)와 접수 완료 메시지를 돌려준다. 같은 공지의 팀 키 값은 문서·JSON에 쓰지 않는다.
- 변경: N22 Finalize만 수정했다. 긴급 선이관(`urgent_pre_handoff`)이고 triage `type=security`이면 검색 근거 없이 다음을 돌려준다(route 담당자 이관, sources=[]).
  - 접수 결과: 성공은 "긴급 보안 문의가 접수되었습니다(티켓 ID)", 알림 실패는 그 뒤에 알림 실패 사실, `tickets_down`은 "접수 여부를 확인하지 못했습니다…", 그 밖은 "접수 결과를 확인할 수 없습니다…".
  - 고정 초동 조치: "피해 확산을 막기 위해 해당 PC의 사내망 연결(유선·Wi-Fi·VPN)을 바로 끊고 IT팀 연락을 기다려 주세요."
  - 본인 티켓 조회가 ok이면 그 티켓 ID·제목·상태를 덧붙인다. 타인(forbidden)·없음·장애는 붙이지 않는다.
  - 기존 IT 직원용 `security-incident` 근거 보강 경로(urgent_enriched)와 보안 외 긴급, 그 밖의 분기는 바꾸지 않았다.
- 확인: 로컬 Mock 검사 결과 동일(12/12, 14/14, 13/13, 9/9, 20/20, 6/6). 로컬 n8n `okeSupport13Loc8` execution 1642~1652(모두 success):
  - WF-12 박서연 → high `T-2019` + 사내망 분리 + "T-1002(VPN 인증서 재발급)는 현재 '처리 중'".
  - 피싱만 → high + 사내망 분리. 이준호가 T-1002 포함 피싱 신고 → high + 사내망 분리, 타인 T-1002 상태 없음.
  - 티켓 저장 실패 중 피싱 → `tickets_down`, ticket=null, 확인 못 함 + 사내망 분리.
  - 회귀: 일반 이관과 본인 상태 안내는 이전과 같다.
- 남은 확인: 초동 조치 문구는 공지의 "사내망 분리"만 담았다. 다른 조치를 넣으려면 팀장님 문구가 필요하다. 팀 VM의 oke-support는 아직 `859e3af` 버전이고 Credential이 연결되지 않아 웹훅이 HTTP 500이다(2026-11-05 조회만 함, 변경 없음). VM 반영은 리드·원민님과 맞춘다.

## 워크플로우 설계서 공통 반영 요청 · 2026-11-05

- 담당 원고: `Doc/WORKFLOW-DESIGN-DRAFT.md` 1~8절과 `Doc/SUBMISSION-NOTES.md`. 오현님이 소유한 `docs/WORKFLOW-DESIGN.md`의 기존 “구현 예정” 설명을 실제 번호판·노드·로컬 검증 상태와 대조해 반영해 주시기 바란다.
- 이번 요청은 문서 취합이며 C02/C03/C04 계약 변경 요청이 아니다. `12`는 Git 반영본, `13`은 로컬 미커밋 수정본이므로 최종 게시 버전 확인 뒤 상태·실행 ID를 갱신해야 한다. 유빈님·원민님·지혜님 담당 절은 각자의 실제 실행 근거가 필요하다.
- 영향: 설계서의 노드 수·연결선·Mock/실제 경계와 제출용 `oke-support.json` 버전 표시. 공식 평가 통과나 팀 VM 배포 완료로 표시하지 않는다.

## DH-CHG-05 · 단계별 워크플로우 JSON 보존과 게시 대상

- 연결: C09. 2026-11-04 사용자 요청에 따라 P0-1 원본은 `workflows/oke-support.json`으로 복원하고 P0-2는 `workflows/oke-support-02.json`에 보존했다. 원격의 P0-2 수정 이력은 강제 삭제하지 않고 새 커밋에서 파일 배치를 바로잡는다.
- 영향: 번호판 JSON의 내부 이름·POST 웹훅 경로는 모두 `oke-support`다. n8n에서 동시에 활성화하면 경로가 충돌하므로 기록용 JSON을 함께 게시하지 않는다. 최신 개발본 경로는 `workflows/README.md`를 따른다. 프로젝트 n8n 게시·시험은 미실행이다.
- 오현님 전달 내용: 최종 완성 시점에 공식 제출/게시본을 `develop/dahyeok/workflows/oke-support.json`으로 단일 정리하고 현재는 번호판을 유지한다. 실제 정리·공통 문서 반영은 아직 하지 않았다.

실제 검토/연결 후에만 해당 제안에 상대 HANDOFF 링크, 확인 날짜·내용, 공통 반영 절·커밋, 재현 입력·예상/실제·보고서 경로를 추가한다. 현재는 모두 미확인이다. 버그는 실행 위치/버전·마스킹 로그·재현 입력을 자기 기록에 추가하고 파일 소유자가 수정한다. 외부 메시지는 이번 작업에서 전송하지 않는다.
