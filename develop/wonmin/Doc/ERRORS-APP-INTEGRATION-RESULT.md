# oke-errors 실제 app 저장 수습 · 2026-11-05

로컬 Ubuntu Docker Compose에서 **실제 자동 Error Trigger 5조건을 포함한 10개 시험 그룹을 통과**했다. 지혜 `ec6a735` FastAPI와 PostgreSQL `0005`의 전용 `wonmin_c05_app` DB를 사용했다. 이전 Mock/501 시험과 구별하며, 팀 VM·실제 data-api·본체 전체 시험은 아니다.

## 변경 파일과 연결

- `tools/test-errors-app-integration.py`: 자동 부모 오류 → 실제 Error Trigger → app 알림/DLQ 저장, 장애·복구, 재진입/중복/누락 메타데이터, 종료 복구를 확인하는 실행기를 추가했다.
- 정본 `workflows/oke-errors.json`의 14개 노드와 ACK 판정 코드는 수정하지 않았다. 실제 실행에서 코드 변경이 필요한 기능 오류는 발견되지 않았다.
- 전용 `wonmin-errors-app-real` 사본의 모드·주소를 app/`http://c05-proxy:8801`로 선택하고 실제 Credential ID를 연결했다. 정본 SHA-256과 backend 커밋은 [실행 보고서](../runs/errors-app-integration-20261105T102508Z.json)에 기록했다.
- 임시 부모 Settings의 `errorWorkflow`를 실제 오류 처리기 ID `wmerrapp7a38cad3f6`에 연결하고 게시한 웹훅으로 자동 실행했다. 임의 ID나 수동 노드 실행을 발화 근거로 쓰지 않았다.
- 별도 인증 웹훅 probe는 정본과 같은 Code/분기를 사용하되 Error Trigger 입구만 웹훅으로 바꿨다. 자기 이름/ID 재진입, 동일 부모 ID 재처리, 실행 ID 없음은 이 probe로 시험했으며 자동 발화 결과와 구별한다.

## 확인 방법과 실제 결과

부모 웹훅 HTTP 상태, n8n 부모/처리기 실행 기록, 프록시의 실제 전달/장애 주입 횟수, 실제 SQL 행을 대조했다. 정상 전달 대상은 실제 FastAPI이며 저장 Mock은 없다. 장애는 프록시의 통제된 HTTP 503 주입이며 PostgreSQL 자체 고장을 의미하지 않는다.

| 자동 발화 조건 | 부모 → 처리기 실행 ID | 부모 HTTP | alerted / dlq | 실제 저장 |
| --- | --- | --- | --- | --- |
| 정상 수습 | 82 → 83 | 500 | true / true | 알림 1·DLQ 1 |
| alerts_down | 84 → 85 | 500 | false / true | 알림 0·DLQ 1 |
| dlq_down | 86 → 87 | 500 | true / false | 알림 1·DLQ 0 |
| 둘 다 실패 | 88 → 89 | 500 | false / false | 알림 0·DLQ 0 |
| 장애 해제 후 복구 | 90 → 91 | 500 | true / true | 알림 1·DLQ 1 |

각 조건에서 알림·DLQ는 각각 1회 시도했고 티켓 API 호출은 0회다. 처리기는 `mode=error`, 정상 종료이며 부모 실행은 계속 `error`로 남는다. 저장소 실패가 추가 처리기 실행을 만들지 않는 것도 관측했다. 앞 sink 실패가 뒤 sink 시도를 막지 않았다.

나머지 5개 그룹은 다음과 같다.

- 인증·연결: 키 없는 임시 부모 호출은 403 거절, 실제 부모 설정의 오류 처리기 ID 일치.
- 자기 이름 `oke-errors` 및 자기 실제 ID: 각각 `skipped_self`, 외부 저장 호출 0회.
- 동일 부모 ID `82` 재처리: 알림은 1건 유지, 실제 ACK `stored=0, duplicate=true`를 성공 처리했다. DLQ는 재처리 기록으로 1건 추가돼 해당 참조 2건이다. **DLQ 멱등 저장을 보장한 결과는 아니다.**
- 실행 ID 없는 trigger 오류: `execution_ref=null`, `request_id=null`을 유지하며 알림·DLQ를 신규 저장했다. 부모 문의 ID를 추정하지 않았다.

HTTP 노드에 저장된 실제 ACK를 별도로 읽어 [ACK 근거](../runs/errors-app-acks-20261105.json)에 남겼다. 알림 신규 `stored=1, duplicate=false`, 중복 `stored=0, duplicate=true`, DLQ HTTP 200·stored=1 및 주입된 503을 확인했다. 누적 count만으로 성공을 판단하지 않았다.

DB 전후: 시험 DB 티켓 8→8, 알림 13→17, DLQ 4→9. 기존 기본 DB 티켓/알림/DLQ는 모두 0→0이다. 자동 부모 5조건의 저장은 실행 참조로 개별 대조했다. 원문 오류에는 합성 canary만 사용했고, 저장된 알림·DLQ에 canary/합성 비밀번호 표식/실제 인증키가 없음을 검사했다. 임시 부모 이름은 허용목록 밖이므로 source_workflow=unknown, 허용된 노드 이름만 저장되는 것도 확인했다.

관련 기존 Node 회귀는 **24/24 통과**했다. [실제 출력 집계](../runs/errors-app-regression-20261105.json). 이번 실행기는 공식 `flow.py` 대체 도구가 아니다.

## 종료 상태와 재현

- 임시 부모·probe 게시 해제, 두 웹훅 모두 404 확인.
- 임시 부모의 의도적 throw 코드를 정상 반환 코드로 교체했다. 실제 저장된 workflow에서도 throw 제거를 확인했다.
- 프록시 장애 계획은 `{}`로 복구했고 n8n·두 backend의 건강 확인은 모두 HTTP 200이다.
- 기존 workflow의 게시 상태·설정·버전은 전후 동일하다. 기존 전역 practice 모드·Credential·볼륨을 바꾸지 않았다. 시험 DB 행과 합성 n8n 실행 기록은 검토 근거로 보존했다.
- 전용 오류 처리기는 [n8n에서 확인 가능](http://127.0.0.1:15678/workflow/wmerrapp7a38cad3f6)하며 게시 상태다. 오류 처리를 연결한 임시 부모는 게시 해제 상태다. 기존 업무 부모의 연결을 이 전용 시험 ID로 바꾸지 않았다.

기존 [C05 app 환경](C05-APP-INTEGRATION-RESULT.md)이 준비된 Ubuntu에서 프로젝트 `develop/wonmin` 폴더로 이동해 실행한다.

```bash
python3 tools/test-errors-app-integration.py
```

이 도구는 n8n/프록시를 재시작하므로 다른 시험과 동시에 실행하지 않는다. 실행마다 새 보고서를 만들고, 종료 시 시험 웹훅 비활성화·throw 제거·프록시 복구를 수행한다. 오류 조건의 raw 입력은 합성 정보만 사용해야 한다. 시험용 사본은 진단을 위해 실행 저장을 켰으며 정본의 비저장 설정과 구별한다.

## 다음 연결 상대

지혜님께: 실제 app 오류 수습에서 `/alerts`의 신규/중복 ACK와 `/dlq` HTTP 200 저장을 확인했다. API/DB 소스 변경 요청은 없다. 공통 문서 반영은 이전 C05 HANDOFF와 같이 오현님 확인이 필요하다.

다음 원민 업무는 다혁님 **본체 C04 → handoff → C05 전체 app 연결 시험**이다. 실제 data-api 직원/권한 준비와 팀 VM 적용은 해당 담당자와 연결한다. 이번 결과로 공식 키트·공통 14유형·LLM 3회·bench·VM 시험을 완료 처리하지 않는다.
