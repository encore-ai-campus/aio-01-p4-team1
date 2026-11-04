# 다혁님 · 구현 계획

[README](../README.md) → [TODO](TODO.md) → [SPEC](SPEC.md) → 이 문서 순서로 읽는다. 본체 `SUP-*` 요구만 구현하며 공통 `WF-*` 기대는 바꾸지 않는다. P0-1의 JSON·요청·Mock·로컬 기대값은 작성했고 Code 독립 실행만 확인했다. 프로젝트 n8n과 공통 시험은 미실행이며 나머지 단계는 구현 예정이다.

## 첫 작업 P0-1 · 입력과 차단 골격

**연결 SPEC: SUP-01/02.** 상대 서비스가 없어도 계약 Mock으로 시작한다. search·handoff·DB를 먼저 만들거나 추가 협의를 기다리지 않는다.

1. `workflows/oke-support.json`에 워크플로우 1개를 만든다. 이름은 oke-support, Webhook path=oke-support, POST, Header Auth Credential 참조, responseMode=responseNode, executionOrder=v1로 둔다. JSON 안에 실제 키를 넣지 않는다.
2. SPEC N01→N02→N03→N04→N22→N23을 연결한다. 성공/오류마다 Respond가 한 번만 도달하도록 한다. N03은 GET /employees 응답 형식의 Mock부터 연결하고 직원 없음과 조회 장애를 다른 상태로 만든다.
3. 아직 분류가 없는 정상 입력은 **개발용 임시 담당자 이관 응답**(ticket=null, reason=not_implemented, 안내에 "개발 중이며 접수하지 않았습니다")으로만 끝낸다. 이 응답을 실제 접수·공통 시험 통과로 취급하지 않으며 실서비스에 게시하지 않는다. P0-3에서 실제 handoff 경로로 교체한다.
4. `requests/input-valid.json`, `requests/input-empty.json`, `requests/input-too-long.json`, `requests/input-unknown-user.json`, `requests/injection.json`, `requests/normal-admin-contact.json`을 만든다. 각각 DH-T-01/13/08/15의 입력을 쓰고 501자는 실제 길이 501인지 확인한다.
5. `fixtures/employees.json`은 제공 6명의 name/dept만 담는다. 이메일/입사일/연락처를 만들지 않는다. 테스트용 직원 확인은 이 fixture를 읽는 Mock임을 표시한다. `cases/support-input.json`에 기대 HTTP/codes/route/LLM 0회를 먼저 정의한다.
6. 아래의 정적 검사로 JSON과 연결선을 확인한 뒤 사람이 로컬에서 차단·400을 확인한다. 이 단계에서는 정상 자동 답변·티켓 생성 완료를 요구하지 않는다.

넘길 결과: 원민님에게 입력/공격/정상 오탐 요청과 기대표, 지혜님에게 request_id/user/question/attempt/context 및 400 codes 예시를 제공한다. API 변경 요청 없이 공통 C02 형식을 사용한다.

완료 기준: DH-T-13 세 입력은 각각 400·정확한 code·LLM 0, DH-T-08은 차단·LLM 0, DH-T-15는 단어만으로 차단되지 않음. check가 가능해진 뒤 노드 타입·버전·연결 오류가 없어야 한다. 실제 확인 전 체크하지 않는다.

### P0-1 확인 기록 · 2026-11-04

- 대상: `workflows/oke-support.json`, `requests/input-*.json`·`requests/injection.json`·`requests/normal-admin-contact.json`, `fixtures/employees.json`, `cases/support-input.json`. 직원 확인은 로컬 Mock, 정상 입력은 `not_implemented` 임시 응답이다.
- 실행: `python3 -m json.tool`로 JSON 9개를 파싱하고, Python으로 요청 6개·직원 6명·긴 질문 501자·Mock/fixture 일치를 확인했다. 기존 `day65-n8n-n8n-1` 컨테이너의 Node v26.7.0에 본체 Code 노드와 요청을 표준 입력으로 보내 독립 실행했다. 이 컨테이너는 프로젝트 n8n 시험 대상이 아니다.
- 실제 로컬 결과: DH-T-13 빈 질문 `400/question_required`, 501자 `400/too_long`, 미등록 직원 `400/unknown_user`; DH-T-08 `200/차단`, `agents=[]`, `ticket=null`; DH-T-15 `200/담당자 이관`, `reason=not_implemented`로 오탐 차단 없음; 정상 입력도 `200/담당자 이관`, `reason=not_implemented`, `ticket=null`. 여섯 입력 모두 로컬 Code 시뮬레이션 일치. 워크플로우에 LLM 노드가 없어 이 단계의 로컬 LLM 호출 경로는 0개다.
- 미확인: 80일차 원본 `flow.py check`, 프로젝트 n8n의 Credential 연결·게시·Webhook HTTP 응답·실제 실행 노드 수와 LLM 호출 수. 로컬 Code 시뮬레이션을 n8n 기능 시험 통과나 공통 WF 통과로 표시하지 않는다. 사람이 프로젝트 환경에서 push·test한 뒤 실제 결과를 추가한다.
- 추가 로컬 도구: `tools/flow.py`를 P0-1 전용으로 작성했다. `python3 tools/flow.py check`는 현재 6노드 JSON·연결·직원 Mock 일치를, `python3 tools/flow.py test-local --node-container day65-n8n-n8n-1`은 기존 실습 컨테이너의 Node 실행기로 Code 경로 6건을 검사한다. 2026-11-04 재실행 결과 6/6 PASS. 이 도구는 프로젝트 키트 원본이 아니며 n8n 게시·Webhook 호출·Credential 동작을 확인하지 않는다.

## 작은 단계별 생성 파일·확인·전달

모든 경로는 `develop/dahyeok/` 기준이다. 같은 본체 JSON을 누적 수정하며 시험용 본체를 복제하지 않는다. 표의 fixture는 소유자 응답을 대체하는 로컬 Mock이며 운영 기준을 바꾸지 않는다.

| 단계 / SPEC | 실제 생성·수정할 파일(예정) | 작은 작업과 확인 입력/예상 route | 다음 담당자에게 넘길 결과 |
| --- | --- | --- | --- |
| P0-1 / SUP-01/02 | 위 본체·6개 requests·fixtures/employees.json·cases/support-input.json | 입력/직원/규칙 관문. DH-T-13→400, 08→차단, 15→규칙 통과. 정상은 미구현 임시 응답 | 지혜님 C02 필드/오류 예시, 원민님 입력·공격 사례 |
| P0-2 / SUP-03/04 | 본체 수정, requests/clarify-1.json·clarify-2.json·clarify-3.json·clarify-context.json, fixtures/triage-results.json, cases/support-triage.json | N06~07+보완 응답. 프롬프트/파서 스키마를 SPEC대로 적용. DH-T-02 attempt1·2→질문, 3→이관 경로(Mock); 정상 context를 합쳐 missing이 사라지는지도 확인 | 지혜님 새 차례 새 ID/증가 attempt/context 예시, 원민님 한도 기대 |
| P0-3 / SUP-07/09 | 본체 수정, fixtures/handoff-results.json, requests/no-evidence.json·urgent.json, cases/support-handoff.json | N20과 C04 Mock 연결. 정상 ticket / tickets_down / alerts_down / 전송 실패를 개별 주입. DH-T-03→이관, 04→이관+null. 임시 not_implemented 제거 | 원민님 request_id/requester/category/priority/reason payload와 결과 매핑 |
| P1-1 / SUP-05 | 본체 수정, fixtures/search-results.json·ticket-lookups.json, requests/own-ticket.json·other-ticket.json, cases/support-retrieval.json | N08~12 두 갈래+Merge. ID 없음·403·404·지연·search []/503/잘못된 형식. DH-T-06→권한 없음, 03→이관. N10 항상 항목 1개, 조회 실패를 근거 없음으로 합치지 않음 | 유빈님 C03 정확 payload/근거 응답, 원민님 조회 상태별 사례 |
| P1-2 / SUP-03/06 | 본체 수정, fixtures/writer-results.json·verifier-results.json, cases/support-verification.json | N13~15와 모든 출력 필터. DH-T-14 잘린 JSON/문자열 불리언/위조 출처→이관. DH-T-07→가림. 임계값은 Mock 값으로 분기만 검증하고 품질 통과라고 하지 않음 | 유빈님·원민님 사용 출처/점수 경계/검증 탈락 입력과 출력 |
| P1-3 / SUP-07/09 | 본체 수정, requests/urgent-complex.json·llm-down.json·slow-ticket.json, cases/support-failures.json | 긴급 N20→N08 보강→N22, handoff_done 유지. DH-T-12→high+보안 근거+본인 상태. writer 실패/조회 지연 뒤에도 재접수 0. DH-T-10→이관 llm_down | 원민님 오류 출력·부분 실패·긴급 단일 접수 관측표, 오현님 시간 예산 후보 |
| P1-4 / SUP-08/09 | 본체 수정, fixtures/replay-results.json, requests/duplicate.json, cases/support-replay.json | N05/N22 결과 재사용 연결. DH-CHG-02/04 미반영이면 adapter Mock까지만; 확정된 티켓 key 중복은 실제 검증. DH-T-09 순차/동시/재시작 재전송에서 티켓 1개 | 지혜님 소유권/결과 저장 API 연결 자료, 원민님 중복 관측·표현 불일치 재현 |
| P1-5 / SUP-10 | 본체 실제 주소/설정으로 교체, Doc/SUBMISSION-NOTES.md, Doc/VERIFICATION-RESULTS.md, 실제 생성된 runs/ 보고서 | 제공자 실제 호출, 공통 전체+팀 5개 이상+LLM 3회·bench·임계값 경계. DH-T-01은 측정 기준 반영 후 자동 답변. 실패 원인/수정/같은 조건 재시험 | 오현님 실제 노드/연결선·보고서·측정·미해결 요청, 원민님 최종 회귀 근거 |

P2 선택 고도화는 필수 P1-5 완료 뒤 [TODO](TODO.md)의 후순위를 따른다.

P0-2의 이관 분기는 P0-3 전에는 Mock이며 티켓 생성 완료가 아니다. P1까지도 Mock 결과와 실제 서비스 결과를 별도 열로 기록한다. 새 정책 승인이 필요한 adapter를 제외한 Agent/검색/이관/출력 작업은 계속 진행한다.

## JSON 작성과 정적 확인 방법 (구현 예정)

명령의 workdir는 저장소 기준 `develop/dahyeok`으로 지정한다. 아래는 단계별 검증 명령이다.

```bash
python3 -m json.tool workflows/oke-support.json > /dev/null
```

생성한 requests/cases/fixtures도 같은 방식으로 각 파일의 JSON 문법을 확인한다. 이 검사만으로 n8n 노드·실행이 통과했다고 하지 않는다.

프로젝트 키트가 제공되고 `tools/flow.py`의 실제 위치·CLI를 확인한 뒤 다음 check를 수행한다. 현재 지정 자료 경로의 Last3Mon/80 키트는 없어 명령은 **예정 경로 템플릿**이다. 다른 실습 키트를 프로젝트 키트인 것처럼 복사/설치하지 않는다.

현재 `develop/dahyeok/tools/flow.py`는 별도 **로컬 P0-1 검사기**다. 아래 예정 명령의 80일차 평가 키트 `flow.py`를 대신하지 않으며, 두 결과를 보고에서 구별한다.

```bash
uv run tools/flow.py check develop/dahyeok/workflows/oke-support.json
```

연결 검토 항목:

- Node name 중복 없음, connections 대상 존재, 각 Agent의 ai_languageModel 연결 분리, Tool 없음.
- 성공/오류 출력 인덱스가 올바름, onError 경로에서 Code 파싱을 건너뛰지 않음.
- HTTP 노드는 full status/오류를 구별하고 timeout을 명시. 승인 전 시간 후보는 Mock 설정으로만 사용.
- N09/N10의 skip/error도 단일 항목, N11에서 request_id 일치, 정상/긴급의 handoff_done 보존.
- 400·차단은 LLM 0회, 최종 응답 한 번, key/권한이 질문·Agent 값으로 덮이지 않음.
- JSON·요청·캡처·요약에 키/실제 연락처 없음, SERVICE_MODE에 맞는 호출/관측 대상 일치.

## 사람이 실행할 연결·시험 (모두 미실행)

키트·본체·하위 워크플로우·인증·색인·Mock 전환 설정이 준비된 뒤에만 실행한다. 아래 workdir도 담당 폴더다. push/test/bench의 실행 주체는 사람이며 이번 문서 작업에서는 호출하지 않는다. 실제 키는 Credential/안전한 환경 설정에서 주입한다.

1. check 뒤 사람이 같은 본체를 push한다. `tools/flow.py`의 실제 명령 도움말을 먼저 확인하고, 경로가 다르면 실제 경로로만 바꾼다.
2. 담당 cases/support-*.json의 해당 단계 입력부터 실행하고 결과를 확인한다. 실제 연결 전에는 Mock 표시가 있어야 한다.
3. 원민님이 원본 공통 사례를 소유 경로에 준비한 뒤 공통 전부와 LLM 3회를 수행한다. 원본의 before/after·expect·ID를 바꾸지 않는다.
4. practice 고장 시험의 fault/reset/ops가 실제 data-api를 향하는지 확인한다. app 저장 연동은 별도로 수행하며 같은 티켓을 양쪽에 쓰지 않는다. 고장은 끝나면 복구하고 복구 결과도 기록한다.

예정 CLI 형식(키트 제공 후 확인, 현재 실행 불가):

```bash
uv run tools/flow.py push develop/dahyeok/workflows/oke-support.json
uv run tools/flow.py test develop/dahyeok/cases/support-input.json --webhook oke-support -v
uv run tools/flow.py test develop/wonmin/cases/common.json --webhook oke-support --repeat 3
uv run tools/flow.py bench oke-support develop/dahyeok/requests/input-valid.json -n 5
```

공통·팀 시험 파일은 원민님이 소유한다. 여기서는 해당 파일을 읽어 호출할 뿐 기대값 수정이나 대체 공통 파일 생성을 하지 않는다. bench 원시 결과가 생긴 실제 위치를 확인해 자기 runs에 보존하며, 상대 runs를 대신 편집하지 않는다.

## 단계별 결과 기록과 인계 형식

각 단계 종료 때 이 문서의 해당 행 아래에 다음 값을 **실행한 경우에만** 추가한다: 날짜/본체 버전, SUP·DH-T·WF ID, Mock/실제, 요청 파일, 예상/실제 HTTP·route·ticket·sources, 실행 노드/LLM 수, 시간, 명령/workdir, 실제 보고서 경로, 실패 원인·수정·재시험, 미해결 DH-CHG ID. check 성공과 기능 시험 성공을 구분한다. 커밋/PR 정보는 실제 생성된 뒤만 기록한다.

원민님에게는 사례·원본 판정 불일치·고장 관측을, 유빈님에게는 질문 세트/기대 문서·권한 목록·점수·검색 실패를, 지혜님에게는 신원/attempt/context·중복 재사용·저장 연결을 넘긴다. 오현님에게는 Doc/SUBMISSION-NOTES.md에 공통 설계서의 반영 절과 실제 보고서만 정리한다.

검색 품질·시간 수치는 SPEC 9절 절차로 측정한다. 수치·설치·시험·협의 완료를 예상으로 채우지 않는다. Git 반영·팀 VM 배포·최종 검토는 상위 담당자가 수행한다.

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [팀 헌장·역할](../../../docs/TEAM-CHARTER.md)
- [협업 방식과 연결 규칙](../../../docs/COORDINATION.md)
- 참조 기준: [평가·시나리오 가이드](../../../docs/EVALUATION-GUIDE.md) · [워크플로우 설계서](../../../docs/WORKFLOW-DESIGN.md) · [공통 작업 규칙](../../../AGENTS.md)
