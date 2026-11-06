# 원민님 n8n 개발 결과물

실환경 갱신(2026-11-05): [Ubuntu Compose 결과](../Doc/UBUNTU-INTEGRATION-RESULT.md). 실제 n8n 2.46.6 import/게시·부모 errors ID 연결·자동 발화를 확인했다. 전용 Mock 수습 4조건 성공, 실제 C05는 501이다. 해당 설치본은 errors도 게시해야 실행됐다. 원본 handoff에 webhookId를 추가했으며 실제 ID/관측 설정은 ignored 배포 사본에만 반영한다. 아래 미확인 설명은 이전 구현 단계 당시 기록이다.

2026-11-05: `oke-handoff.json`에 P1-2 장애·부분/전체 실패 수습을 구현했다. `oke-errors.json`도 P1-3 로컬 구현·검증을 완료했다. 실제 n8n import/게시/실행은 미확인이다.

## 현재 경로

H01 Header Auth → H02 검사·마스킹 → H03 설정 기반 단일 저장소 → H04 티켓 → H05 제한 재시도 → H06 티켓 보존 → H07 실패 컨텍스트 → H08 알림/ACK → 필요 시 H09 DLQ/ACK → H10 결과 → H11 단일 응답.

그래프는30개 노드·순환0개다. 티켓은 같은 key/payload로 최대2회, 알림/DLQ는 각각 최대1회다. 티켓 실패에도 알림과 DLQ 양쪽을 시도하며 하나의 실패가 다른 시도를 막지 않는다. 알림 실패는 기존 티켓을 지우지 않는다. 오류 raw body·headers·stack을 후속 노드/DLQ에 복사하지 않는다. `ok`는 현재 ticket과 alerted가 모두 확인되면 true다. 알림 실패의 ok=false는 기존 동작을 유지하며 WM-04의 최종 공통 정의를 임의 확정하지 않는다.

## ACK와 승인된 C05

사용자가 전달한 팀장 승인(2026-11-05)에 따라 **알림 duplicate 유지·DLQ HTTP200**을 적용했다. 공통 파일이나 지혜님 모델은 대신 수정하지 않았다. 원격4904a49의 StoredResponse는 아직 duplicate가 없는 상태이므로 실제 구현 반영은 지혜님 확인이 필요하다.

| 결과 | 확인 방식 |
| --- | --- |
| 티켓 신규/중복 | 201+duplicate=false 또는200+duplicate=true, 유효 ticket_id. 입력 priority 복원 |
| 알림 신규 | HTTP200, stored=1, 정수 count>=1, duplicate가 명시적 true가 아님. Mock 신규 응답은 duplicate=false를 포함 |
| app 중복 알림 | HTTP200, stored=0, duplicate=true, 정수 count>=1. 기존 event_key 저장 ACK로 alerted=true |
| DLQ | **HTTP200**, stored=1, 정수 count>=1. 201·문자열 숫자·불리언 ACK는 성공으로 판정하지 않음 |

practice는 원본 키트 호환을 위해 event_key를 강제하지 않으며 중복 알림이 생길 수 있다. app은 request_id:ticket-created 또는 request_id:tickets-down으로 나눈다. DLQ stored=0의 의미/중복 억제는 아직 확정하지 않았고 성공으로 추정하지 않는다. flags=false는 ACK 미확인이지 실제 저장0건 보장이 아니다.

DLQ에는 request_id, workflow/node/reason과 safe_payload의 stage(ticket/alert), priority, attempts, last_status 및 확인된 ticket_id만 보낸다. requester·title·evidence_summary·원문 오류·키·연락처는 넣지 않는다. 이 정보만으로 자동 replay하지 않고 백엔드 inquiry/ticket 연결을 통한 수동 복구를 전제로 한다.

## 재시도·시간 설정

400/401/403/404/409 등 영구 거절은 추가 호출0회다. 5xx/전송 오류/timeout 및 조건을 만족하는429만 최대1회 추가한다. Retry-After는 유효한 초 또는 HTTP 날짜를 해석해200ms 상한/남은 예산을 넘거나 잘못된 값이면 재시도하지 않는다. 없으면 기본 대기값을 쓴다.

실행 설정의 WONMIN_RETRY_WAIT_MS는0~200(기본200), WONMIN_HANDOFF_BUDGET_MS는1500~4000(기본4000)이다. 값이 잘못되면 쓰기 없이503으로 종료한다. 재시도 전후에 다음 티켓1초와 두 sink1.2초의 예산을 확인한다. Wait가 늦게 깨어나도 예산 부족 시 재시도를 시작하지 않는다. 이4초는 로컬 추가 재시도 판단 예산이며 n8n 스케줄링을 포함한 하드 SLA/실측값이 아니다. 부모 C04 초기timeout5초와 실제 배포에서 검증해야 한다.

대기는 [n8n Wait](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait)의 시간 간격 모드로 설정했다. 로컬 어댑터도 같은 설정을 실행하지만 설치된 n8n과의 호환·스케줄링은 미검증이다.

## n8n 가져오기 전 설정 (사람이 수행)

JSON은 active=false이며 Credential ID는 교체용이다. 아래 이름의 Header Auth Credential을 실제 로컬 ID에 연결한다. 값은 JSON·문서·로그에 쓰지 않는다.

| 참조 이름 | 적용 노드 | 헤더/값 출처 |
| --- | --- | --- |
| WONMIN_X_TEAM_KEY | H01 | X-Team-Key / N8N_WEBHOOK_KEY를 Credential에 등록 |
| WONMIN_PRACTICE_STORE_AUTH | H04/H08/H09 Practice | 로컬 Mock은 X-Api-Key / INTERNAL_API_KEY. 실제 data-api는 제공된 인증 명세·DATA_API_KEY를 확인 후 설정 |
| WONMIN_APP_STORE_AUTH | H04/H08/H09 App | X-Api-Key / INTERNAL_API_KEY를 Credential에 등록 |

n8n 실행 환경의 SERVICE_MODE를 practice 또는 app으로 명시한다. 기본 저장 주소는 각각 `http://data-api:8800`, `http://backend:8000`이다. 전용 Mock 연결에는 WONMIN_PRACTICE_STORE_URL 또는 WONMIN_APP_STORE_URL을 설정한다. 값은 http(s)의 호스트·포트만 가능하며 사용자정보·경로·쿼리·fragment는 거절한다. 요청 body의 mode/주소는 무시한다. IPv6 literal 주소는 현재 지원하지 않는다.

키는 $env로 읽지 않고 Credential로만 전송한다. 모드·주소의 $env 접근이 차단된 n8n에서는 배포 담당자가 해당 설정 접근 방법을 준비해야 한다. 접근 오류는 503으로 종료한다. 환경/Compose 공통 파일은 이번 작업에서 수정하지 않았다.

HTTP 노드는 티켓 1초·알림/DLQ 각각 0.6초, 노드 자체 자동 재시도 없음, 리다이렉트 추적 없음으로 설정했다. 티켓은 별도 H05 분기에서 최대1회 추가 호출한다. practice와 app의 HTTP 노드는 서로 다른 Credential을 사용하며 선택한 한 경로만 실행한다. 수동 시험 시 n8n 컨테이너의 localhost는 호스트 Mock이 아니다. 호스트 Mock을 명시적으로 외부 바인딩한 전용 시험 환경에서 `http://host.docker.internal:18800` 등 실제 도달 가능한 주소를 사용한다.

Webhook에는 원래 headers/body가 들어오므로 실행 데이터 자동 저장을 껐다. 수동 편집기·프로세스/외부 로그의 원문 노출까지 보장하는 설정은 아니며 캡처에 Credential·연락처를 담지 않는다. H02 이후에는 선택한 필드만 전달하고 evidence_summary·headers는 버린다. title의 이메일·국내 휴대전화·Bearer/명시적 password/token/api-key 표기를 가린다. 모든 종류의 민감정보 탐지를 보장하지 않는다.


## 게시·시험 및 다음 단계

공식80일차 도구가 준비되면 `flow.py check workflows/oke-handoff.json` 후 사람이 Credential을 연결해 게시·시험한다. 정상/중복/high 및 tickets_down, alerts_down, DLQ 실패, 모두 실패, 영구거절, 429, 지연 저장을 실행 ID와 같은 인스턴스의 전후 건수로 확인한다. 예상 실패는 H11까지 종료하고, 예상 밖 오류의 Error Trigger 수습은 다음 P1-3 범위다.

실제 결과·추가 진행 가이드는 [P1-2 결과](../Doc/P1-2-RESULT.md)와 [증거 색인](../runs/INDEX.md)을 참조한다. 공식 키트 없이 자체 도구를 flow.py로 대신 만들지 않는다.

## oke-errors · P1-3

[구현 결과·안전한 부모 시험/연결 절차](../Doc/P1-3-RESULT.md)를 따른다. E01 Error Trigger→E02 허용목록 컨텍스트/모드선택→E03 알림/ACK→E04 독립DLQ/ACK→E05 내부Outcome의14노드다. HTTP응답/티켓생성/자동replay/재시도는 없고 errors의 errorWorkflow를 자기ID로 지정하지 않는다. n8n 기본 자기오류 라우팅에 대비해 source이름/ID 재진입 가드도 둔다.

앱/연습모드 설정·Header Auth Credential은 위 handoff와 동일한 WONMIN_APP_STORE_AUTH/WONMIN_PRACTICE_STORE_AUTH를 E03/E04 노드에 연결한다. mode/주소는 요청본문이 아닌 실행설정만 읽는다. errors 입구는 내부 Error Trigger라 webhook용 X-Team-Key Credential이나 URL을 새로 만들지 않는다.

모든HTTP는 각1회·0.6초·continueRegularOutput다. 알림만/DLQ만/둘다 실패를 내부 partial_failure/failed로 기록하고 추가throw하지 않는다. success는 두 수습sink의ACK 확인이지 부모업무 복구가 아니다. Error Trigger 표준에는 검증된 inquiry request_id가 없어 null로 두고, 부모execution.id가 유효하면 추적참조로만 쓴다. 원문오류·stack·URL·headers는 제거하며, 업무/노드이름도 허용목록 외에는unknown이다.

errors 저장 후 실제ID를 부모 소유자에게 전달해 해당 부모 Settings→Error workflow에 연결해야 한다. Error Trigger는 수동Execute로 발화검증하지 못하고 자동실행 부모의 오류로 확인해야 한다. 현재 실제ID/설정/발화는 미확인이며, 이번 변경에서 handoff나 상대부모의 설정을 임의수정하지 않았다.
