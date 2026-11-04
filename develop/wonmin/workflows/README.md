# 원민님 n8n 개발 결과물

`oke-handoff.json`의 P1-1 정상·중복 경로를 작성했다. `oke-errors.json`은 P1-3 예정이다.
[자기 개발 계획](../Doc/IMP-PLAN.md) → [공통 계약](../../../docs/API-CONTRACT.md) → 한 단계 구현·check → 사람이 push·test 순서로 진행한다.
전체 경로·작업 디렉터리를 명령에 명시하고, 키는 Credential에만 둔다. 제출은 [리드의 취합 안내](../../ohyun/SUBMISSION.md)를 따른다.

## 현재 경로

H01 Header Auth → H02 C04 검사·마스킹 → H03 실행 설정으로 저장소 선택 → H04 `/tickets` → H06 상태/본문 검증·원래 priority 복원 → H08 `/alerts` → H10 ACK 확인 → H11 단일 응답.

입력의 request_id를 그대로 C05 key로 사용한다. 중복 방지는 저장 API의 원자적 UNIQUE/거래 책임이며 워크플로우 캐시로 대체하지 않는다. 정상은 HTTP200, ok=true, ticket, reason=null, alerted=true, dlq=false다. HTTP201+duplicate=false 또는 HTTP200+duplicate=true와 유효 ticket_id를 모두 확인해야 티켓을 반환한다. 저장 API 응답에 priority가 없어도 입력의 normal/high를 유지한다.

잘못된 C04는 쓰기 없이 HTTP400과 일반 오류 메시지로 종료한다. 코드/세부 오류 형식은 WM-04 미정으로 확정하지 않았다. 설정 누락/잘못된 모드·URL은 쓰기 없이 503으로 종료한다. P1-1의 최소 안전장치로 티켓 미확인은 tickets_down, 알림 미확인은 티켓을 유지한 alerts_down으로 반환한다. 알림만 실패한 ok=false는 보수적인 임시 처리이며 WM-04 승인/최종 계약을 뜻하지 않는다.

알림은 신규 stored=1 및 정수 count>=1일 때 확인한다. app의 동일 event_key 응답은 stored=0·duplicate=true·정수 count>=1일 때만 기존 저장 ACK로 인정한다. 그 밖에는 확인 불가로 처리한다. practice에는 event_key를 보내지 않으므로 중복 호출 시 알림이 여러 건일 수 있다. app의 stored=0 응답 의미와 duplicate 필드 실제 제공은 지혜님과 연결 검증이 필요하다.

## n8n 가져오기 전 설정 (사람이 수행)

JSON은 active=false이며 Credential ID는 교체용이다. 아래 이름의 Header Auth Credential을 실제 로컬 ID에 연결한다. 값은 JSON·문서·로그에 쓰지 않는다.

| 참조 이름 | 적용 노드 | 헤더/값 출처 |
| --- | --- | --- |
| WONMIN_X_TEAM_KEY | H01 | X-Team-Key / N8N_WEBHOOK_KEY를 Credential에 등록 |
| WONMIN_PRACTICE_STORE_AUTH | H04/H08 Practice | 로컬 Mock은 X-Api-Key / INTERNAL_API_KEY. 실제 data-api는 제공된 인증 명세·DATA_API_KEY를 확인 후 설정 |
| WONMIN_APP_STORE_AUTH | H04/H08 App | X-Api-Key / INTERNAL_API_KEY를 Credential에 등록 |

n8n 실행 환경의 SERVICE_MODE를 practice 또는 app으로 명시한다. 기본 저장 주소는 각각 `http://data-api:8800`, `http://backend:8000`이다. 전용 Mock 연결에는 WONMIN_PRACTICE_STORE_URL 또는 WONMIN_APP_STORE_URL을 설정한다. 값은 http(s)의 호스트·포트만 가능하며 사용자정보·경로·쿼리·fragment는 거절한다. 요청 body의 mode/주소는 무시한다. IPv6 literal 주소는 현재 지원하지 않는다.

키는 $env로 읽지 않고 Credential로만 전송한다. 모드·주소의 $env 접근이 차단된 n8n에서는 배포 담당자가 해당 설정 접근 방법을 준비해야 한다. 접근 오류는 503으로 종료한다. 환경/Compose 공통 파일은 이번 작업에서 수정하지 않았다.

HTTP 노드는 티켓 1초·알림 0.6초, 자동 재시도 없음, 리다이렉트 추적 없음으로 설정했다. practice와 app의 HTTP 노드는 서로 다른 Credential을 사용하며 선택한 한 경로만 실행한다. 수동 시험 시 n8n 컨테이너의 localhost는 호스트 Mock이 아니다. 호스트 Mock을 명시적으로 외부 바인딩한 전용 시험 환경에서 `http://host.docker.internal:18800` 등 실제 도달 가능한 주소를 사용한다.

Webhook에는 원래 headers/body가 들어오므로 실행 데이터 자동 저장을 껐다. 수동 편집기·프로세스/외부 로그의 원문 노출까지 보장하는 설정은 아니며 캡처에 Credential·연락처를 담지 않는다. H02 이후에는 선택한 필드만 전달하고 evidence_summary·headers는 버린다. title의 이메일·국내 휴대전화·Bearer/명시적 password/token/api-key 표기를 가린다. 모든 종류의 민감정보 탐지를 보장하지 않는다.

## 남은 확인

공식 80일차 `flow.py check` → 사람이 Credential 연결·n8n 게시 → handoff-normal/high/duplicate 요청 → Executions와 동일 저장소의 전후 티켓 건수 대조가 필요하다. 단독 Code 실행과 로컬 어댑터 통과를 게시된 n8n 실행으로 표시하지 않는다.

재시도·티켓 실패 시 독립 알림/DLQ 수습(H05/H07/H09)은 P1-2, Error Trigger·실제 app 인증/DB는 P1-3이다. 현재 DLQ는 호출하지 않으며 항상 false다. 티켓 실패 전체 수습/공통 장애 시나리오를 통과한 버전으로 사용하지 않는다.

노드 설정 참고: [HTTP Request](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest), [Webhook](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook), [Respond to Webhook](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.respondtowebhook), [Code](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code). 설치된 n8n 버전과의 실제 import 호환은 미검증이다.
