# C05 저장 API 모델 대조 · 2026-11-04

이 문서는4bbbf49/P1-1 당시 검토다. 2026-11-05 사용자 전달 팀장 승인으로 알림 duplicate 유지·DLQ HTTP200을 P1-2에 적용했다. 최신 [P1-2-RESULT.md](P1-2-RESULT.md)를 우선하며, 아래 불일치 재현 스크립트는 원민 당시ceb8efe 워크플로우에 고정해 과거 증거를 재현한다. 상대 실제 응답 모델 반영/연결은 별도 대기다.

**요청 표본 7/7은 지혜님 DTO에 필드 손실 없이 적합하다. 중복 알림 응답에는 연결 불일치 1건이 있다. 실제 API·인증·DB/n8n 연결 완료는 아니다.**

대상: `origin/feat/jihye-p0`, 커밋 `4bbbf49aac652bae947fec1a787b86af7e74f24e`. fetch 후 common.py, tickets.py, alerts.py 모델과 tickets/alerts 라우터, deps.py, tests/test_api_models.py를 읽었다. 원민 워크플로우는 `ceb8efe`의 P1-1 JSON을 사용했다. 다른 팀원 파일은 수정하거나 체크아웃하지 않았다.

요청 원본은 [c05-store-samples.json](../requests/c05-store-samples.json), 실제 검증 결과·모델 소스/워크플로우 해시는 [c05-jihye-4bbbf49-review.json](../runs/c05-jihye-4bbbf49-review.json)에 있다. 실제 Pydantic 2.14.2 모델을 Git에서 읽어 메모리에서 실행했다. 버전은 지혜님 uv.lock과 일치한다. 지혜님 API 테스트 전체를 재실행한 결과는 아니다.

## 요청 필드 매핑

| 경로 / 지혜님 모델 | 원민 표본 | 대조 결과 |
| --- | --- | --- |
| `/tickets` / TicketCreate | H02가 handoff-normal/high/duplicate에서 생성한 key, title, requester, category, priority | 3/3 적합. key=request_id, 1~64자·공백만 불가. priority는 normal/high. requester는 제공 직원 이름 유지. 나머지는 비어 있지 않은 문자열 |
| `/alerts` / AlertCreate | H06이 생성한 workflow, node, message, severity, ticket_id. app에만 event_key | 2/2 적합. ticket_id/event_key는 생략 또는 null 허용. app event_key=request_id:ticket-created. practice에는 생략 |
| `/dlq` / DlqCreate | 계획 표본 2종: 티켓 실패 request_id 문자열, 예상 밖 오류 request_id=null. workflow, node, reason, safe_payload 객체, execution_ref | 2/2 적합. 아직 P1-1에서 보내지 않는 계획 표본이며 실제 전송/저장 검증은 아님 |

실제 매핑 표본(발급 ticket_id는 모델 대조용 합성값):

```json
{"key":"wm-p11-handoff-normal","title":"VPN 현장 점검 요청","requester":"박서연","category":"network","priority":"normal"}
```

```json
{"workflow":"oke-handoff","node":"H06 Keep Ticket","message":"담당자 이관 티켓이 접수되었습니다.","severity":"normal","ticket_id":"T-2001","event_key":"wm-p11-handoff-normal:ticket-created"}
```

```json
{"request_id":null,"workflow":"oke-errors","node":"E02 Safe Context","reason":"unexpected","safe_payload":{"stage":"unexpected","priority":"normal"},"execution_ref":"local-review-only"}
```

`DlqCreate.request_id`는 **필수이면서 null 허용**이다. 키 자체를 생략한 표본은 실제 모델에서 거절됐다. Error Trigger에서 ID를 얻을 수 없으면 null을 명시해야 한다. `safe_payload`는 객체 타입만 확인하며 개인정보 제거는 모델이 보장하지 않으므로 호출자가 수행해야 한다.

## 응답과 상태

| 항목 | 지혜님 구현 / 원민 소비 | 판단 |
| --- | --- | --- |
| 신규/중복 티켓 | TicketCreated는 ticket_id·duplicate. 라우터가 false→201, true→200으로 반환 | 적합. priority가 응답에 없으므로 원민이 입력값을 복원하는 현재 방식 유지 |
| 신규 알림 | StoredResponse는 엄격한 비음수 정수 stored/count, 기본 HTTP200. 원민은 stored=1 및 count>=1 확인 | 적합. DTO가 stored=0 또는 count=0을 허용해도 개별 이벤트 저장 성공을 뜻하지 않음 |
| 중복 알림 | 원민은 stored=0/count>=1/duplicate=true일 때 ACK. 지혜님 StoredResponse에는 duplicate가 없음 | **현재 연결 불일치. 아래 재현 참조** |
| DLQ 응답 | 현재 라우터는 StoredResponse, 기본 HTTP200. 원민 SPEC에는 신규201/중복200 기대 기록 | 시험 기대 정리가 필요하다. 루트 C05에는 DLQ의 201/200이 별도로 명시되어 있지 않으므로 원민 내부 기대를 확정 공통 계약으로 강요하지 않는다. P1-2 구현 전 200 기준 여부를 지혜님·오현님과 확인 |

## WM-C05-01 · 중복 알림 ACK 불일치 재현

백엔드가 다음 결과를 만들더라도:

```json
{"stored":0,"count":1,"duplicate":true}
```

현재 `StoredResponse.model_validate(...).model_dump()` 결과는 다음과 같다. 공통 부모 모델의 extra=ignore와 응답 DTO 필드 제한으로 duplicate가 제거된다.

```json
{"stored":0,"count":1}
```

원민 H10을 실제 실행한 로컬 관측: 직렬화 전 alerted=true/reason=null → 직렬화 후 alerted=false/reason=alerts_down. 두 경우 모두 확인된 티켓은 유지된다. 신규 알림은 영향이 없고, event_key 중복 ACK에 영향을 준다. 실제 서버를 호출한 재현은 아니다.

요청 DTO를 바꿀 필요는 현재 없다. 지혜님·오현님께 중복 ACK의 응답 필드/의미를 확정해 달라는 검토 자료다. 예를 들어 선택 duplicate를 명시적으로 계약·응답 모델에 반영하거나 해당 이벤트 저장 확인 방법을 제공해야 한다. **제안이며 승인/공통 반영이 아니다.** 원민이 `stored=0,count>=1`만 보고 성공으로 바꾸지는 않았다. count는 누적 건수라 현재 이벤트 저장을 단독으로 증명하지 못한다. 상대 모델과 공통 계약은 수정하지 않았다.

## 인증·저장과 검증 경계

지혜님 세 라우터는 X-Api-Key 의존성을 사용한다. 현재 deps.py는 키 누락401, 키가 있어도 실제 키 대조 미구현으로501이며 backend.execute도 기본501이다. 따라서 모델 준비 완료와 실제 저장 API 가동을 구분한다. n8n의 app HTTP 노드는 X-Api-Key Credential 연결이 필요하고 X-Team-Key는 handoff 입구용이다. 실제 키 값은 이번 검토에서 쓰거나 출력하지 않았다.

티켓 UNIQUE/동시 거래·소유권 거절, event_key 멱등 저장, DLQ 중복·ACK, 실제 누적 count, safe_payload 마스킹·DB 영속성은 미확인이다. 기존 원민 HTTP Mock 결과를 지혜님 실제 저장 결과로 해석하지 않는다.

재현(저장소 루트, 환경은 develop/wonmin/.venv에만 생성하며 Git에서 제외):

```bash
uv venv develop/wonmin/.venv
uv pip install --python develop/wonmin/.venv/bin/python 'pydantic==2.14.2'
develop/wonmin/.venv/bin/python -B develop/wonmin/tools/check-c05-models.py
```

`--output`은 own runs 안의 새 JSON 파일명만 허용하고 기존 증거는 덮어쓰지 않는다. 기본 검토 ref는 위 커밋으로 고정되어 있다. 검증 종료0은 7개 요청 적합 및 알려진 ACK 불일치가 그대로 재현됐다는 뜻이며 C05 전체 호환/실연결 PASS가 아니다.
