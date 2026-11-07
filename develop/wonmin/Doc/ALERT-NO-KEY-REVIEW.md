# 지혜님 질의 회신 자료 · event_key 없음/practice · 2026-11-05

**event_key 생략/null은 매번 독립 신규 저장으로 처리하며, 같은 내용/티켓이어도 알림 멱등성을 보장하지 않는다. 원민 HTTP Mock에서 확인했고 실제 data-api/PostgreSQL 결과는 아니다.**

지혜님4904a49가 DB 실행 기반까지라는 설명과 일치한다. 알림 duplicate 응답 유지·DLQ HTTP200 팀장 승인 기준은 유지한다. 현재 원민 구현이나 상대 모델을 바꾸지 않고 요청하신 경계를 확인했다.

## 회신할 응답 기준

| 요청 | 저장 의미 | HTTP200 응답 |
| --- | --- | --- |
| event_key 생략 | 중복 여부를 확인할 키가 없으므로 매 호출 신규 저장 | stored=1, duplicate=false, count=실제 누적 수 |
| event_key=null | 생략과 동일 | stored=1, duplicate=false, count=실제 누적 수 |
| 새 event_key | 해당 key로 최초 저장 | stored=1, duplicate=false, count 증가 |
| 같은 event_key 재요청 | 해당 key의 기존 저장을 확인 | stored=0, duplicate=true, count 유지 |

신규 저장을 요청했다는 이유만으로 성공 응답을 미리 만들지 않고 실제 저장/커밋 확인 후 반환해야 한다. 누적 count만으로 성공을 판정하지 않는다. key가 없는 요청에 ticket_id/message/고정 기본키를 대신 적용해 임의로 중복 처리하지 않는다. 이 표는 현재 원민 Mock과 승인된 ACK 의미에 맞춘 구현 기준이며 실제 PG 저장 성공 확인은 지혜님 구현 후 수행한다.

원민 실제 HTTP Mock에서 같은 body를 두 번 보낸 결과:

```json
{"stored":1,"count":1,"duplicate":false}
{"stored":1,"count":2,"duplicate":false}
```

key 없이 동시8회 추가 전송도8건 모두 stored=1/duplicate=false였으며 count=3~10으로 증가했다. null key2회도 각각 신규 저장됐다. 이후 같은 key로 순차2회·기존key 동시8회는 신규1건만 저장되고 이후 stored=0/duplicate=true/count 유지였다. **이는 잠금이 있는 원민 메모리 Mock 결과이며 PostgreSQL UNIQUE/거래/동시성 검증을 대신하지 않는다.**

## practice에 대한 구분

현재 handoff practice 경로는 event_key를 보내지 않는다. 동일 request_id를 두 번 보내면 티켓은 같은 key로1건 유지되지만 알림은 각 호출에서 추가될 수 있다. 이번 로컬 어댑터+HTTP Mock 관측은 **티켓1건·알림2건**, 두 알림 모두 stored=1/duplicate=false 및 alerted=true였다. practice에서 알림까지1건이라고 주장하지 않는다.

실제80일차 data-api는 이번에 호출하지 않았다. 공통 계약의 기존 신규 알림 예시는 HTTP200 `{"stored":1,"count":1}`이고 duplicate가 없다. 원민 H08/E03 수신 코드는 이 **레거시 신규 ACK**도 허용한다. 즉 다음을 구분한다.

- 지혜님 app 구현: 신규이면 명시적으로 duplicate=false, 동일key 기존 저장이면 duplicate=true를 유지해 반환한다.
- 기존 practice 응답: stored=1과 양의 정수 count가 확인되면 duplicate 생략도 호환용으로 수용한다. 실제 API가 이렇게 반환하는지는 아직 미확인이다.
- count만 있거나 stored=0만으로는 성공으로 처리하지 않는다. 같은 key의 확인된 중복 ACK(stored=0/duplicate=true)는 현재 **app에서만** 성공으로 처리한다. practice는 key를 보내지 않으므로 그런 응답을 발견하면 실제 의미/스키마를 먼저 확인해야 한다.

errors app에서도 부모execution.id가 없으면 event_key를 만들지 않는다. 같은 합성 trigger 오류를2회 처리했을 때 알림2건이 추가되었고 가짜 공통 key로 서로 다른 오류를 합치지 않았다. 부모참조가 있을 때만 n8n-execution:{id}:unexpected-error 키를 사용한다.

## 확인 근거와 재현

실제 관측8그룹: [alert-no-key-practice-review.json](../runs/alert-no-key-practice-review.json). no-key 순차/동시, null-key 순차, keyed 순차/동시, practice handoff2회, errors 무참조2회, 소비자ACK 행렬7종을 확인했다. 소스3종 SHA-256과 실제 HTTP 응답·전후 건수를 포함한다. 소비자 행렬만 Code에 합성응답을 주입한 검사이며 나머지 저장 관측은 독립 loopback HTTP Mock에 실제 요청한 결과다.

```bash
node develop/wonmin/tools/check-alert-ack.mjs
```

공유/프로젝트 data-api·n8n·DB를 호출/초기화하지 않았고 임시 Mock과 임시 키는 종료/폐기했다. 기존 워크플로우/Mock·팀원 코드·공통 계약은 수정하지 않았다. 실제 data-api의 응답/인증/저장 동작과 지혜님 PG 결과는 여전히 미확인이다.

## 실제 DB 연결 후 함께 확인할 항목

1. key 없음/null은 두 요청이 각각 stored=1/duplicate=false로 저장되는지 확인. 동일 ticket_id라도 임의 중복 억제를 하지 않는지 대조.
2. 새 key→동일 key 순차/동시 호출의 알림1건·stored/duplicate 조합·실제 count와 커밋 완료 대조. 키가 없는 요청의 동시 결과와 별도로 집계.
3. 티켓 저장 후 알림 실패 시 티켓 ID/건수 유지, 알림 미확인과 stage=alert DLQ ACK 확인.
4. DLQ HTTP200/stored/count 확인. stored=0/중복 DLQ ACK 의미는 별도 확정 전까지 성공으로 추정하지 않음.
5. practice 실제 data-api의 안전한 응답 표본과 인증/모드·호출/관측 대상의 일치 확인. 이전 Mock 동시8건·티켓1건과 실제 PG 결과를 분리 기록.

이 문서는 지혜님께 전달할 회신 자료이며 외부 메시지는 보내지 않았다. 상대 확인·실제 연결 완료로 표시하지 않는다.
