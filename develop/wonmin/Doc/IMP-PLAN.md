# 원민님 · IMP-PLAN

현재 실행 근거(2026-11-05): [ec6a735 C05 실제 app 연동](C05-APP-INTEGRATION-RESULT.md). 로컬 Ubuntu에서 실제 n8n·backend·PG 15개 시험 그룹을 통과했다. 전용 app DB의 직원 fixture로 수행했으며, 아래 초기 계획의 미실행 표기는 당시 기록이다. 공식 키트·실제 data-api·본체 전체/팀 VM 및 Error Trigger app 저장 전체 재시험은 별도다.

[README](../README.md) → [TODO](TODO.md) → [SPEC](SPEC.md) → 이 계획 순서로 진행한다. 계약 변경은 [HANDOFF](HANDOFF.md)에만 제안하고 공통 기준 그대로의 작업은 바로 시작한다.

> 2026-11-04 P0 입력 파일·정적 확인 완료. 키트 반입 및 서비스 시험은 대기다. P1-1은 로컬 구현·Mock 40개 검증 완료, 실제 n8n/저장 연결은 대기다. P1-2 로컬 구현·HTTP Mock 검증도 완료했고 실제 n8n·C05 연결은 대기다. P1-3 errors 로컬 구현·Mock 검증도 완료했으며 실제 부모연결·자동발화·app통합은 대기다. P1-4 이후는 구현 예정이다. 상세 증거는 ../runs/INDEX.md 참조.

단계 분류: **P0 기반 → P1 필수 MVP → P2 선택 고도화**. P1-1~P1-5는 모두 필수다.

## 공통 실행 위치와 준비 규칙

모든 명령 블록은 먼저 아래 폴더(저장소 루트 기준)로 이동한 뒤 한 줄씩 실행할 **예정**이다. 상대 폴더 명령을 대신 실행하거나 공통 파일을 생성하지 않는다.

```bash
cd develop/wonmin
```

서비스 주소/키는 지혜님이 제공한 실행 환경과 Credential을 사용한다. n8n 내부는 data-api:8800/backend:8000, 호스트 CLI는 같은 서비스의 공개된 포트다. SERVICE_MODE는 실행 설정으로 정하고 저장 호출 두 대상을 동시에 활성화하지 않는다. 환경변수 값이나 키를 보고서에 출력하지 않는다.

## P0 · 계약과시험입력준비

**첫 작업**은 새 정책 협의가 아니라 시험 입력과 기대를 파일로 옮기는 일이다. REL-01~06에 연결한다.

1. SPEC의 TM-01~08을 `cases/team.json`, TM-09~10과 신규/중복/영구 거절/일시 오류를 `cases/handoff.json`으로 작성한다. 각 케이스에 ID·조건·입력·예상 HTTP·필수 필드·부작용·정리 경로를 넣는다. app은 `cases/app-integration.md`에 세션/권한/중복/영속성의 수동 확인 절차를 작성한다. 미정 정책 관련 필드는 `Doc/HANDOFF.md` 제안 ID를 연결하고 미판정으로 둔다.
2. `requests/demo-normal.json`(TM-01), `demo-clarify.json`(TM-02), `demo-handoff.json`(TM-06), `demo-urgent.json`(TM-05), `demo-failure.json`(TM-07), `bench-normal.json`(TM-01)을 만든다. 설명 문서의 가짜 ticket_id를 실제 기대값으로 고정하지 않는다.
3. 제공된 80일차 키트가 준비되면 `tools/flow.py`와 실행에 필요한 보조 파일을 본인 폴더 안에 배치하고 출처·버전을 기록한다. `--help`와 코드를 읽어 보고서 출력 경로·fault/ops 호스트·인증 처리를 확인한다. tools 기준 상대경로 때문에 보고서가 외부 폴더나 루트로 나가지 않게 한다. 키트가 없으면 해당 파일과 common은 생성 대기, 팀 입력 작성은 계속한다. 과거 일차의 키트를 공통 14유형 원본으로 대체하지 않는다.
4. 공통 원본을 `cases/common.json`으로 그대로 보존하고 원본 경로·버전·SHA-256을 `runs/INDEX.md`에 기록한다. 판정·질문·고장 조건을 수정하지 않는다. 웹훅만 실행 옵션 `--webhook oke-support`로 선택한다. 원본 before/after의 주소가 현재 시험 인스턴스와 다르면 공통 파일을 고치지 말고 WM-02에 재현·실행 환경 조정 요청을 추가한다.
5. `runs/INDEX.md`에 환경/모드·커밋·배포 버전·색인/모델·도구 버전·예정 사례와 상태를 기록한다. 이 파일은 시험 후 증거 색인이며 별도의 시작 안내파일을 만들지 않는다.

파일 준비 뒤 확인 예정:

```bash
python3 -m json.tool cases/team.json
python3 -m json.tool cases/handoff.json
python3 -m json.tool requests/demo-normal.json
python3 -m json.tool requests/demo-clarify.json
python3 -m json.tool requests/demo-handoff.json
python3 -m json.tool requests/demo-urgent.json
python3 -m json.tool requests/demo-failure.json
python3 -m json.tool requests/bench-normal.json
shasum -a 256 cases/common.json
uv run tools/flow.py --help
```

JSON 파싱은 문법 확인이며 기능 통과가 아니다. 키트 원본 해시는 원본 경로의 실제 해시와 비교한다. 비밀값 없이 입력·기대·미정 경계가 준비되면 다음 단계로 간다.

**다음 담당자에 넘길 결과:** 다혁님에게 C04 입력/응답 예와 팀 기대, 지혜님에게 C05 저장 요청/상태·관측 요구, 오현님에게 키트 준비 여부·제안 ID. 새 합의 요청을 기본안 개발의 선행조건으로 만들지 않는다.

- [x] 실제 P0 입력 파일·정적 확인 결과·키트 미준비 항목을 runs/INDEX.md에 기록 (서비스 시험 통과 아님)

## P1-1 · 정상과중복handoff

REL-01·05. `workflows/oke-handoff.json`에 H01~H04/H06/H08/H10/H11을 먼저 구현한다. P0의 handoff 케이스와 `requests/handoff-normal.json`, `requests/handoff-high.json`, `requests/handoff-duplicate.json`을 준비한다. 상대 API가 없으면 본인 폴더의 `tools/mock-store.py`(구현 예정)에서 C05의 201/200·알림 ACK를 재현하고 Mock 표시를 한다.

1. Header Auth→검사/마스킹→모드 선택→티켓 요청 변환을 구현한다. POST /tickets 응답에 priority가 없어도 원래 priority를 붙인다.
2. 티켓 ID를 유지한 채 /alerts로 넘기고 stored ACK로 alerted를 정한다. 티켓 생성과 알림 성공의 상태를 분리한다.
3. 같은 키 순차·동시 요청에서 티켓 한 건을 확인한다. 캐시와 저장 API의 duplicate 동작은 별도 기록한다. 알림 중복 정책은 WM-03으로 분리한다.

정적 확인 예정:

```bash
uv run tools/flow.py check workflows/oke-handoff.json
```

사람이 게시·Credential 연결 후 수행할 예정:

```bash
uv run tools/flow.py call oke-handoff requests/handoff-normal.json -v
uv run tools/flow.py call oke-handoff requests/handoff-duplicate.json -v
uv run tools/flow.py call oke-handoff requests/handoff-duplicate.json -v
uv run tools/flow.py call oke-handoff requests/handoff-high.json -v
uv run tools/flow.py ops -v
```

위 ops는 practice이며 같은 인스턴스인지 먼저 확인한다. 새 티켓 수·key·ticket_id·priority·알림 ACK를 대조하고 동시 호출은 P1-4의 필수 시험 도구로 확인한다. **다음 담당자에 넘길 결과:** 다혁님에게 실제 C04 성공/중복 응답과 워크플로우 버전, 지혜님에게 순차/동시 관측 불일치 재현. 실제 연결 전에는 Mock 통과만 보고한다.

- [x] 신규/중복/긴급 로컬 Mock 결과·대상·보고서 경로 기록 (실제 n8n 연결은 대기)

## P1-2 · 장애와부분실패

REL-02·05. 같은 `oke-handoff.json`에 H05/H07/H09와 오류 출력을 추가한다. `cases/handoff.json`, `tools/mock-store.py`에 400/401/403/404/429/5xx/timeout, 알림만 실패, DLQ만 실패, 모두 실패를 추가한다. Mock은 상태·호출 횟수·key·지연 저장 여부를 기록하되 키와 원문은 남기지 않는다.

1. 401/403 등은 최초 호출에서 종료시켜 상태별 재시도를 분리한다. 모든 HTTP 오류에 retryOnFail을 일괄 적용하지 않는다.
2. WM-01의 수치는 미확정이므로 설정값으로 분리해 Mock에서 상한·기한 동작을 확인한다. 실제 부모 timeout 변경은 다혁님, 공통 반영은 오현님이 한다.
3. 티켓 실패에도 알림과 DLQ 양쪽을 시도하고 성공 ACK를 따로 누적한다. 하나가 실패해도 다른 시도를 생략하거나 생성 티켓을 지우지 않는다.
4. practice /dlq는 실제 키트 스키마를 확인해 매핑하고, app `/dlq`는 `docs/API-CONTRACT.md` 5절(`POST /dlq`) 스키마로 연결한다. 알림 `event_key` 선택 필드와 함께, 알림 재시도/재처리 세부(WM-03)·부분실패 ok(WM-04)는 표시를 유지한다.
5. timeout 뒤 지연 저장·같은 key 재시도를 관측해 최종 티켓 1건을 확인한다. 즉시 ops만 보고 유실/중복을 단정하지 않는다.

정적/파싱 확인과 사람이 수행할 단독 시험 예정:

```bash
python3 -m json.tool cases/handoff.json
uv run tools/flow.py check workflows/oke-handoff.json
uv run tools/flow.py test cases/handoff.json --webhook oke-handoff -v
```

Mock의 세부 상태·지연은 도구 구현 시 `--help`에 실행 방법을 적고 README에 실제 검증 명령을 추가한다. 지금 설치/실행 명령이 검증된 것으로 쓰지 않는다.

**다음 담당자에 넘길 결과:** 다혁님에게 tickets_down/alerts_down·ticket=null 매핑 증거, 지혜님에게 지연 저장·거래·멱등성·DLQ 문제의 입력/기대/실제, 오현님에게 미반영 정책과 그 경계의 미판정 항목.

- [x] 실패별 로컬 호출 횟수·시간·ACK·저장 상태 및 Mock 종료 결과 기록 (실제 n8n/DB·공식 check 대기)

## P1-3 · errors와app연결

REL-03·05. `workflows/oke-errors.json`에 E01~E05를 구현하고 `cases/app-integration.md`에 실제 관측 절차를 보완한다. 다른 소유자의 워크플로우·Compose·SQL은 수정하지 않는다.

```bash
uv run tools/flow.py check workflows/oke-errors.json
uv run tools/flow.py check workflows/oke-handoff.json
```

1. 사람이 errors를 import·저장하고 실제 ID를 확보한다(Error Trigger 자체 게시가 필수는 아니며, 부모의 자동 실행 실패로 시험한다). 부모 소유자에게 ID와 설정 위치를 전달하고 연결 여부를 기록한다. errors 자체에는 자기 자신을 연결하지 않는다.
2. 전용 시험 n8n의 **본인 handoff 임시 시험 버전**에서 비민감 고정 Code 오류를 의도적으로 발생시켜 E01 발화를 확인한다. 실제 운영 요청으로 시험 오류를 활성화하는 입력을 남기지 않는다. 부모 설정·부모 실패 ID·errors 실행 ID·알림/DLQ ACK를 보존한다.
3. errors의 알림만/DLQ만/양쪽 실패를 Mock으로 재현해 유한 종료와 비밀값·stack 제거를 확인한다. 시험 오류를 제거한 버전을 다시 check하고 정상 요청으로 복구를 확인한다.
4. app 모드에서 backend `/tickets`·`/alerts`·`/dlq`의 X-Api-Key 인증과 실제 DB 저장, 세션 신원/타인 request_id 거절, 동시 티켓 1건을 확인한다. 재시작은 지혜님이 수행하고 전후 같은 티켓을 조회한다. app 관측은 practice ops로 대체하지 않는다.

**다음 담당자에 넘길 결과:** 각 부모 소유자에게 실제 errors ID·연결 근거, 지혜님에게 app 시험 결과와 미준비 API, 오현님에게 실행별 수습 성공/부분실패/전체실패와 남은 문제. 실제 확인이 없으면 연결 완료라고 쓰지 않는다.

- [x] errors 안전한 컨텍스트·독립 sink·유한종료 로컬 구현/Mock 결과 기록
- [ ] 실제 부모연결·자동 errors 발화·수습/복구 및 app 권한/저장/중복/영속성 근거 기록

## P1-4 · 필수 시험·반복·bench·재시험·동시성 확인

REL-04~06. 구현 예정 보조 도구는 두 개로 한정한다.

| 파일·예정 CLI | 동작과 출력 |
| --- | --- |
| `tools/run-fresh.py --suite PATH --webhook NAME --repeat N --prefix TEXT --output PATH` | 원본 suite를 바꾸지 않고 회차별 새 request_id 파생 요청. 중복 시험은 같은 회차 안에서만 동일 key 유지. 실행 요청·응답·LLM 호출/캐시·초 단위 시간을 개인 runs에 저장. --bench이면 n과 p50/p95/max/실패수 계산, --parallel 2이면 동시 멱등성 확인 |
| `tools/check-evidence.py --index runs/INDEX.md` | 색인에 적힌 실제 raw 보고서·n8n 실행 요약·ops 전후를 읽어 ID·route·ticket_id·건수·권한/마스킹·retry를 대조. 빠진 증거/미정 정책은 미판정, 실패는 실패. HTTP200만으로 PASS 생성 금지 |

도구는 공통 판정기를 대체하지 않는다. 키트가 이미 fresh ID 기능을 제공하면 그 기능을 먼저 사용하고 별도 도구를 줄인다. 독립 LLM 실행이 실제로 있었는지 확인하는 책임은 유지한다.

사람이 실행할 순서(전용 practice, 실제 파일·키트 준비 후):

1. 모드/대상·버전·건수와 기존 증거를 기록한다. reset 가능한 전용 환경에서만 아래 준비를 한다. 공유 환경이면 새로운 request_id와 전후 차이로 격리하고 reset을 생략한다.

```bash
uv run tools/flow.py doctor
uv run tools/flow.py ready
uv run tools/flow.py ops --reset
uv run tools/flow.py fault all ok
uv run tools/flow.py llm up
uv run tools/flow.py ops -v
```

`ready` 등은 제공된 80 키트 --help에서 지원을 확인한 뒤 사용한다. 미지원이면 준비 상태를 수동 확인하고 미지원 명령을 실행 성공으로 기록하지 않는다.

2. 공통 원본 한 번 → 팀 사례 → 관련 하위/권한 시험 → 공통 회귀를 수행한다. 장애 사례는 하나씩, before/after와 실패 정리 경로를 확인한다.

```bash
uv run tools/flow.py test cases/common.json --webhook oke-support -v
uv run tools/flow.py test cases/team.json --webhook oke-support -v
uv run tools/flow.py test cases/handoff.json --webhook oke-handoff -v
uv run tools/flow.py ops -v
```

3. LLM 관련 팀 사례를 새 ID로 독립 3회 반복한다. `cases/team-llm.json`은 P0 기대 중 LLM 관련 사례만 추출해 **구현 시 생성**하고 원본과 대응 ID를 기록한다. 기대는 바꾸지 않는다.

```bash
python3 tools/run-fresh.py --suite cases/team-llm.json --webhook oke-support --repeat 3 --prefix wm-llm --output runs/llm-fresh.json
```

회차별 route·sources·검증·LLM 호출 수와 실패를 기록한다. `flow.py test ... --repeat 3`도 필요 시 수행하되 동일 ID이면 멱등/캐시 반복 보고서로 분리한다.

4. bench를 정상 상태에서 수행한다. 같은 입력 bench와 새 ID 측정을 구분한다.

```bash
uv run tools/flow.py bench oke-support requests/bench-normal.json -n 5 -v
python3 tools/run-fresh.py --suite cases/team-llm.json --webhook oke-support --repeat 5 --prefix wm-bench --bench --output runs/bench-fresh.json
```

첫 명령은 동일 body 반복이며 캐시가 섞일 수 있다. 두 번째는 경로별 분리 집계·n/분모를 기록한다. 실제 타이밍을 SPEC REL-06대로 비교하고 시간 목표가 없으면 수치만 보고한다. 재실행 시 output은 새 실행 식별자가 든 파일명으로 바꿔 원 보고서를 덮어쓰지 않는다.

5. 실패는 원 보고서·실제 실행 노드·원인 근거·수정 소유자/버전·조치·잔여 위험을 `runs/INDEX.md`에 연결한다. 같은 질문/모드/고장/권한/색인 조건을 복원하고 새 요청 ID로 재시험한다. 중복 재현은 원래 key 관계를 유지한다. 관련 회귀 후 결과를 별도 파일에 기록한다. 보고서를 편집해 실패를 지우거나 기대를 느슨하게 하지 않는다.
6. fault all ok → llm up → ops → 정상 새 요청으로 복구를 확인한 후 증거를 대조한다.

```bash
uv run tools/flow.py fault all ok
uv run tools/flow.py llm up
uv run tools/flow.py ops -v
python3 tools/check-evidence.py --index runs/INDEX.md
```

실제 도구가 생성한 JSON 원본은 보존한다. 파일명 충돌을 피하고 `runs/<실행ID>/` 아래 원본 파일명 그대로 모아도 된다. 색인에는 실행ID/모드/배포커밋/케이스·회차/명령/원본경로/기대/실제/판정/실행ID·캡처/실패→재시험/정리 상태를 연결한다. 비밀·개인정보가 나온 원본은 공유하지 말고 마스킹 사본과 처리 내역을 기록한다.

**다음 담당자에 넘길 결과:** 기능 소유자에게 재현·실패/재시험 링크, 오현님에게 공통·팀의 고유 시나리오 수와 실행 횟수·성공/실패/미판정·3회 안정성·bench·예외 처리 비율. 반복 횟수를 시나리오 수로 부풀리지 않는다.

- [ ] 실제 보고서와 실행 근거 대조, 실패/재시험·복구 상태 기록

## P1-5 · 필수 VM회귀와시연·제출

REL-04~06. VM 반영은 오현님이 수행한다. 배포 커밋이 바뀔 때마다 VM의 실제 대상 확인 뒤 공통 회귀를 하고 최종 배포에서 팀·반복·bench를 재확인한다. 로컬 보고서를 VM 결과로 이름만 바꾸지 않는다.

시연 순서(사람이 실행 예정):

1. 배포 버전·모드·화면 로그인·n8n Executions·ops를 확인하고 정상 상태를 준비한다.
2. `demo-normal.json`으로 근거 답변·sources·검증을 보여 준다.
3. `demo-clarify.json`으로 보완 질문, 새 ID·attempt=3의 한도 사례로 티켓을 보여 준다.
4. 전용 practice에서 tickets error → `demo-failure.json` → ticket=null·사유·DLQ/알림을 보여 준다.
5. 즉시 fault all ok로 복구하고 정상 요청을 확인한다. 장애 단계가 실패해도 정리 명령을 먼저 수행한다.
6. `demo-urgent.json`으로 high 티켓·알림·sources=[] 및 사내망 분리 안내·본인 T-1002 상태를, `demo-handoff.json` 재호출로 같은 ticket_id·한 건 저장을 보여 준다. 일반 직원의 이 사례에는 IT 전용 보안 규정 색인을 선행조건으로 요구하지 않는다.
7. 요청별 실행 노드·시간·마스킹·실패/재시험 보고서를 보여 주고 app 관리자 화면의 실제 티켓/권한 흐름을 별도 보여 준다. practice DLQ가 app에 저장됐다고 설명하지 않는다.

실제 시연 호출 형식:

```bash
uv run tools/flow.py call oke-support requests/demo-normal.json -v
uv run tools/flow.py call oke-support requests/demo-clarify.json -v
uv run tools/flow.py fault tickets error
uv run tools/flow.py call oke-support requests/demo-failure.json -v
uv run tools/flow.py fault all ok
uv run tools/flow.py llm up
uv run tools/flow.py ops -v
```

매 리허설은 새 request_id 세트로 준비하되 중복 시연 쌍만 같은 ID를 쓴다. 화면 지연/실패를 숨기지 않고 준비한 실제 실행 근거를 설명한다.

최종 구현 예정 `Doc/SUBMISSION-NOTES.md`에는 **반영할 공통 문서·절 / 실제 노드·edge 입출력 / 실행 환경·배포커밋 / 원본 보고서·캡처 / 측정·실패·재시험 / 남은 제안·미실행**을 정리한다. 오현님이 [취합 안내](../../ohyun/SUBMISSION.md)에 따라 제출 사본을 만든다. 본인은 루트 제출 파일·상대 코드·GitHub를 직접 수정하지 않는다.

문서/변경 범위 확인 예정(저장소 루트에서 읽기 전용):

```bash
git diff --check -- develop/wonmin
git diff --name-only -- develop/wonmin
git diff --cached --name-only
```

다른 작업자의 변경/스테이징이 보이면 건드리지 않고 본인 작업 목록만 보고한다.

- [ ] VM 결과·시연 복구·취합 메모·문서 링크·편집 범위 확인

## P2 · 선택 고도화

자동 DLQ replay, 회로 차단, 알림 묶음 전송 고도화, 장시간 부하 시험은 P1 필수 증거를 갖춘 뒤 선택적으로 진행한다. 수동 복구·동일 키 재시험과 동시성 확인 도구는 P1 필수 범위다.

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [팀 헌장·역할](../../../docs/TEAM-CHARTER.md)
- [협업 방식과 연결 규칙](../../../docs/COORDINATION.md) · [시나리오·평가 가이드](../../../docs/EVALUATION-GUIDE.md) · [아키텍처](../../../docs/ARCHITECTURE.md) · [제출 안내](../../ohyun/SUBMISSION.md)
