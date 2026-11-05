# P1-2 결과·추가 진행 가이드 · 2026-11-05

**티켓 제한 재시도와 tickets_down/alerts_down/알림·DLQ 부분/전체 실패 수습을 구현했다. 전체 로컬65개 시험 통과. 실제 n8n·지혜님 저장 API/DB 시험은 미실행이다.**

## 승인 반영과 구현

사용자가 전달한 팀장 지시의 **알림 duplicate 유지·DLQ HTTP200 승인**을 적용했다. 추가 승인을 요청하지 않고 원민 폴더만 수정했다. fetch 시 원격main 550d784의 공통 표와 지혜님4904a49 모델에는 이 승인 문구/필드가 아직 없었다. 계약 승인과 상대 코드 반영을 구분하며, 지혜님·오현님 반영 필요 사항을 HANDOFF에 기록했다. 원민이 상대 파일이나 공통 파일을 대신 바꾸지 않았다.

- `workflows/oke-handoff.json`: H05 재시도/대기·예산 재확인, H07 실패 컨텍스트, H08 알림 ACK, H09 DLQ·ACK를 추가했다. 현재30개 노드, 순환0개, 단일 H11 응답이다.
- 티켓은 최대2회·각1초. 400/401/403/404/409는 최초1회로 종료하고, 429/5xx/전송 오류/timeout만 제한 재시도한다. 같은 key와 같은 payload를 유지한다. 알림·DLQ는 각1회·0.6초이고 노드의 자동 retry는 꺼 중첩하지 않는다.
- 429 Retry-After는 유효한 초/HTTP날짜·최대200ms·남은 예산을 확인한다. 잘못된/너무 긴 값이면 추가 시도 없이 수습한다. 기본200ms 대기는 실행 설정으로0~200ms까지 바꿀 수 있다. 재시도 전후에 티켓1초+sink1.2초의 예산을 검사한다. 기본4초는 재시도 판단 예산이며 실제 n8n 전체시간의 하드 보장이나 서비스 SLA가 아니다.
- 티켓 실패에도 알림을 시도한 뒤 DLQ를 독립적으로 시도한다. 알림 실패/timeout이 DLQ를 막지 않는다. 티켓 성공·알림 실패이면 ticket을 유지하고 DLQ stage=alert를 기록한다. 티켓 실패면 stage=ticket이다. 둘 다 실패해도 재귀/무한 재시도 없이 종료한다.
- 알림은 신규 stored=1 또는 app의 stored=0/duplicate=true ACK를 검증한다. DLQ는 승인대로 **HTTP200+stored=1+양의 정수 count**만 성공으로 확인한다. 단순HTTP200, Boolean stored, 문자열 count, DLQ201, 누적count만 있는 응답은 성공으로 추정하지 않는다.
- safe_payload에는 stage/priority/attempts/last_status/확인된 ticket_id만 허용한다. request_id는 외부 추적용 필드로 별도 보존한다. requester/title/evidence_summary·오류 원문·headers·stack·키·연락처를 복사하지 않는다. 복구는 서버 기록 연결에 따른 수동 절차를 전제로 하며 자동 replay는 구현하지 않았다.

부분실패 ok=false는 현재 원민/다혁 호환 동작을 유지한다. 이번 C05 승인만으로 WM-04의 공통 ok 의미까지 새로 확정한 것은 아니다.

## 검증과 실제 결과

실행 위치는 저장소 루트다. Node v26.12.1·Python 표준 라이브러리를 사용하고 추가 패키지 설치 없이 실행했다.

```bash
node --test
node develop/wonmin/tools/check-c04-pair.mjs
python3 -B develop/wonmin/tools/mock-store.py --help
```

- 전체 시험: [p1-2-local-20261105T022016Z.txt](../runs/p1-2-local-20261105T022016Z.txt) — 65개/통과65/실패0/종료0. 기존40개+P1-2 추가25개다. 실제 fault-injected HTTP Mock 시나리오22개와 Code 단위 경계3개를 추가했다.
- 실제 응답·호출 횟수·동일 key/payload 해시·즉시/후속 관측: [p1-2-local-20261105T022016Z.json](../runs/p1-2-local-20261105T022016Z.json). 워크플로우/Mock/테스트/어댑터 SHA-256 포함. 독립 loopback 임시 서버는 종료했고 공유 환경을 초기화하지 않았다.
- C04 기존 aac0dbf mapper와 현재 원민 JSON의 로컬 경계17건도 재실행해 일치했다. 원격 최신96d8f85/11의 mapper에서도 dlq 플래그를 전달하는 코드를 읽기 확인했다. 이17건은 전체65개 시험과 별개이며 실제 n8n/최신11 전체 경로를 실행한 것은 아니다.

| 장애 | 실제 로컬 응답/관측 |
| --- | --- |
| tickets503 지속 | 티켓2회, 알림1회, DLQ1회. ticket=null/tickets_down/alerted=true/dlq=true |
| tickets+alerts 실패 | ticket=null/tickets_down/alerted=false/dlq=true. DLQ까지 도달 |
| tickets+DLQ 실패 | ticket=null/tickets_down/alerted=true/dlq=false. 알림 보존 |
| 세 저장 모두 실패 | ticket=null/tickets_down/alerted=false/dlq=false, 유한 종료 |
| 티켓 성공·알림 실패 | 티켓1건 보존, alerts_down, DLQ 성공이면true·실패면false. 티켓 재생성0 |
| 영구거절400/401/403/404/409 | 티켓1회만 호출, 알림/DLQ 각1회 시도 |
| 일시503 후 정상 | 같은 key/payload 2회로 티켓1건, 알림1, DLQ0 |
| 429 | Retry-After0은 재시도, 5초/잘못된 값/-1은 추가 호출 없이 수습 |
| 알림 또는 DLQ timeout | 해당 플래그false, 다른 sink는 실제 ACK대로 유지 |
| 티켓 timeout/지연 저장 | 최초 응답 미확인 상태와 실제 지연 저장을 구분. 두 timeout 뒤 같은ID 재요청에서도 기존 티켓1건·duplicate=true |
| app 중복 알림 | 티켓 중복true·알림1건·alerted=true, DLQ0 |

개발 중에는 기존 Mock이 fault 설정을 무시해 tickets_down 시험이 정상 응답으로 실패하는 것을 먼저 확인했다. P1-2 구현 후 기존 고립 H06 시험4개가 새 H05 이력 없이 실패해 fixture에 해당 이력을 추가했고, 기존 기대는 유지했다. 지연 Wait 후 예산 재확인 부재와 Retry-After=-1을 과거 날짜로 해석하는 문제도 실패 시험을 먼저 확인한 뒤 수정해 전체65개를 통과했다. 이 개발 실패 원 출력은 별도 raw 파일로 보존하지 않았으며 공통 시나리오 실패2건 요구의 증거로 집계하지 않는다.

## Mock에서 재현하는 방법

로컬 환경에 INTERNAL_API_KEY가 준비된 상태에서, 아래 변수는 **비밀값이 아닌** 시작 시 fault plan이다.

```bash
WONMIN_MOCK_FAULTS='{"tickets":[{"status":503}],"alerts":[{"status":503}],"dlq":[{"status":503}]}' python3 -B develop/wonmin/tools/mock-store.py --port 18800
```

각 endpoint의 배열을 순서대로 쓰고 마지막 상태를 반복한다. `status`, `delay_ms`(최대10000), `retry_after`를 지원한다. 예: tickets=[{"status":503},{}]는 첫 실패 뒤 정상, tickets=[{"delay_ms":1500},{}]는 첫 응답 지연 뒤 정상이다. fault는 요청 body로 선택하지 못한다. `/tickets`, `/alerts`, `/dlq`, `GET /_mock/ops`는 X-Api-Key 인증이며 reset/fault API는 없다. 호스트/컨테이너 연결은 워크플로우 README의 배포 주소 설정을 따른다. 키를 명령/보고서에 값으로 출력하지 않는다.

새 증거를 저장할 때는 덮어쓰지 않는 basename을 사용한다.

```bash
WONMIN_RECOVERY_REPORT_BASENAME=p1-2-new-run.json node --test
```

## 추가 진행 순서

1. **지혜님·오현님 C05 반영 확인:** 승인된 알림 duplicate를 응답 모델/직렬화에서 유지하고, DLQ HTTP200·실제stored/count ACK를 제공해야 한다. event_key UNIQUE·티켓 key UNIQUE/소유권·동시 거래와 실제 내부키 검증이 준비되면 마스킹된 결과를 대조한다. DLQ stored=0/중복 의미는 별도로 정해야 하며 현재 성공으로 추정하지 않는다.
2. **공식80일차 키트와 n8n 확인:** tools/flow.py·common 원본/버전·해시 확보 후 공식 check를 수행한다. 사람이 Credential 연결·게시·독립 시험환경에서 정상→중복→tickets_down→alerts_down→DLQ 실패→모두 실패→지연 저장→복구 순서로 실행한다. 실제 호출/fault/ops 대상이 같은 저장소인지 먼저 맞춘다. HTTP200만으로 PASS 처리하지 않는다.
3. **다혁님 C04 실제 호출:** 현재 최신11도 하위 C04는 Mock이다. 실제URL·X-Team-Key·5초timeout·응답 envelope를 연결하고 ticket/reason/duplicate와 alerted/dlq를 실제로 보존하는지 확인한다. 여러 support 번호판을 동시에 게시하지 않는다.
4. **다음 원민 P1-3:** oke-errors.json의 Error Trigger→안전한 오류 컨텍스트→독립 알림/DLQ→유한 종료를 구현한다. 부모 소유자가 실제 errorWorkflow ID를 설정하고, 게시된 시험 부모의 비민감 오류에서 부모/수습 실행 ID를 확인해야 한다. 예상 가능한 저장 장애 수습은 현재 본 경로에 그대로 둔다.
5. **P1-4/P1-5 증거 완성:** 실제 app 인증·DB·권한·동시성·재시작 유지 후 공통14종·팀 사례·LLM 새ID3회·bench·실패/재시험·VM 회귀를 수행한다. 이번 Mock 통과를 그 결과로 대체하지 않는다.

단계 공유에는 변경 파일 / 확인 명령 / 실제 결과 / 다음 연결 상대를 함께 전달한다. 본인 Doc/HANDOFF에는 준비했으며 외부 메시지를 보내거나 상대 승인·실제 연결 완료로 표시하지 않았다.
