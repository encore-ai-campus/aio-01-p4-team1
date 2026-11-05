# P1-3 oke-errors 결과·실제 연결 절차 · 2026-11-05

**Error Trigger·독립 알림/DLQ 수습을 구현했고 전체 로컬89개 시험이 통과했다. 실제 부모 errorWorkflow 연결·자동 Error Trigger 발화·backend/DB 통합은 미실행이다.**

## 구현한 범위

`workflows/oke-errors.json`의14개 노드가 E01 Error Trigger → E02 Safe Error Context/실행설정 → E03 Alert/ACK → E04 DLQ/ACK → E05 Outcome으로 이어진다. Credential은 기존 WONMIN_APP_STORE_AUTH/WONMIN_PRACTICE_STORE_AUTH를 사용하고 mode/주소도 handoff와 같은 실행설정으로 선택한다. 이벤트 본문으로 모드/URL을 고르지 않는다.

알림·DLQ는 각1회·0.6초·리다이렉트 추적 없음·노드 재시도 없음·continueRegularOutput이다. 알림 실패/timeout/인증 거절에도 DLQ를 시도하고, 두 sink의 ACK를 따로 판단한다. 알림 신규/중복은 승인된 duplicate 의미를 유지하고 DLQ는 승인된 HTTP200/stored=1/양의 정수 count를 확인한다. 티켓 생성·HTTP응답 노드·자동replay·추가throw는 없다.

| 내부 outcome | 의미 |
| --- | --- |
| success | 알림·DLQ 두 ACK 확인. 부모업무 성공/복구를 뜻하지 않음 |
| partial_failure | 두 sink 중 하나만 확인 |
| failed | 두 sink 모두 ACK 미확인. 실제 저장0건을 단정하지 않음 |
| skipped_self | source 이름이 oke-errors이거나 source ID가 현재 errors ID와 같아 재진입 종료. 외부호출0 |
| configuration_error | 실행 모드·주소를 안전하게 선택할 수 없어 외부호출 없이 종료 |

## 원문 제거·부모 추적·재귀 차단

Error Trigger의 message/stack/URL/headers/context와 임의 request_id를 전달하지 않는다. source_workflow는 프로젝트4종 허용목록, source_node는 알려진 노드이름 허용목록에서만 선택하고 그 밖에는 unknown이다. 이름 자체에 개인정보/키가 들어 있어도 그대로 복사하지 않는다. 분류는 execution_error/trigger_error/unknown 세 값만 쓴다.

표준 오류 이벤트에는 검증된 inquiry request_id가 없어 **항상 null**로 둔다. 부모execution.id는1~20자리 숫자 참조일 때만 유지한다. 없거나 다른 형식이면null이며 URL에서 ID를 추출하거나 임의ID를 만들지 않는다. 알림 메시지도 허용된 source/노드·부모참조로만 구성하므로 DLQ가 실패하고 알림만 남아도 부모를 추적할 수 있다. 실제 실행ID가 없으면 알림에 미상으로 표시한다.

app의 부모execution.id가 있으면 event_key=n8n-execution:{id}:unexpected-error로 알림 중복ACK를 확인한다. ID가 없으면 event_key를 만들지 않는다. practice에도 event_key를 강제하지 않는다. DLQ는 request_id=null, 고정 workflow/node/reason, safe_payload(stage=unexpected, 허용 source/노드/error_kind), 있을 때만 execution_ref를 보낸다. DLQ 중복 정책/자동복구는 확정하거나 구현하지 않았다.

errors의 settings.errorWorkflow를 자기ID로 설정하지 않았다. n8n 문서에는 Error Trigger가 있는 워크플로우의 기본 오류 처리가 자기 자신일 수 있다고 되어 있으므로, 설정에만 의존하지 않고 source 이름과 문자열/숫자 ID로 **코드 재진입 가드**를 둔다. 예상 가능한 sink 실패는 받아서 종료하고 다시throw하지 않는다. 원래 부모의 실패 상태를HTTP200으로 바꾸지 않는다.

원본 오류 이벤트가 들어오는 E01도 있으므로 자동 실행 데이터 저장은 껐다. 이는 수동 편집기·외부 프로세스 로그까지 가려 준다는 의미는 아니다. 공유 증거에는 후속 안전한 요청/Outcome·실행ID·ACK만 남기고 원문 오류/headers를 통째로 내보내지 않는다.

## 실제 로컬 결과

저장소 루트 `node --test` — 기존65개+P1-3 추가24개 = **89/89·실패0·종료0**.

- 최종 원 출력: [p1-3-final-20261105T024732Z.txt](../runs/p1-3-final-20261105T024732Z.txt)
- 최종 실제 안전한 요청/Outcome·관측·코드해시: [p1-3-final-20261105T024732Z.json](../runs/p1-3-final-20261105T024732Z.json)
- 최초 통과 보고서도 p1-3-local-20261105T024621Z.json/.txt로 보존했다. 이후 숫자형 자기ID 가드와 알림 단독성공 시 부모참조를 보완하고 최종 재시험했다.

추가24개는 독립 Mock을 기동하는20개 시나리오(자기재진입/설정 오류는 외부호출0)와 그래프/컨텍스트/ACK 경계4개다. 표준 실행 오류·trigger 오류·메타데이터 누락, 두 sink의 정상/개별/전체 실패·timeout, app 중복알림 ACK, practice 분기, 자기 이름/ID 재진입, 설정/인증 거절, 원문 미노출을 확인했다. 같은 run에서 handoff65개 회귀도 통과했다. 이는 payload를 주입하는 로컬 어댑터와 실제 C05 HTTP Mock 시험이며 n8n의 자동 Error Trigger·실제DB 시험은 아니다.

워크플로우가 없을 때 시험 실패를 먼저 확인했다. 이후 숫자형 parent workflow ID를 놓쳐 재수습하던 경계와 알림 단독성공 시 메시지의 부모참조 누락도 실패 시험으로 확인하고 수정했다. 해당 개발 중 실패 raw 출력은 따로 파일로 보존하지 않았고 공통 실패2건 요구의 증거로 세지 않는다.

로컬 재현:

```bash
node --test
WONMIN_ERRORS_REPORT_BASENAME=p1-3-new-run.json node --test
```

새 basename만 사용하고 기존 보고서는 덮어쓰지 않는다. requests/error-execution.json·error-trigger-failure.json은 합성 **Error Trigger item** 예시이며 HTTP 웹훅에 보내는 요청 파일이나 실제 실행ID 증거가 아니다. cases/errors.json은 수동 검토 기대표다. API키는 테스트 중 메모리에서 만들고 보고서/요청 파일에 저장하지 않는다.

## 사람이 수행할 실제 n8n 연결·복구 절차

1. **공식 check·Credential:** 80일차 flow.py/common 원본·버전·해시를 준비해 두 JSON을 공식 check한다. 전용 n8n에 errors를 import·저장하고 E03/E04 App/Practice Credential·SERVICE_MODE·실제저장주소를 연결한다. errors 자체를 publish해야 한다고 가정하지 말고 설치버전의 Error workflow 선택/실행 동작을 확인한다.
2. **부모 소유자가 연결:** 저장된 errors 실제ID를 확보해 다혁·유빈 등 각 부모 소유자에게 전달한다. 각 소유자가 부모 Settings→Error workflow에 해당ID를 선택/저장하고 설정 근거를 기록한다. 원민 handoff도 실제ID 확보 후에만 설정한다. 이번 작업에서는 가짜ID나 테스트용 오류 분기를 부모JSON에 넣지 않았다.
3. **전용 시험 부모에서 자동 실패:** 원민 handoff의 임시 시험복제본에서 H02 뒤에 비민감 고정 `throw new Error('wonmin-p13-controlled-error')` Code를 둔다. 그 복제본만 전용 webhook 자동 실행으로 호출한다. 수동Execute/Code 단독 실행은 Error Trigger 발화 증거가 아니다. 운영 입력에 오류 발생 스위치를 남기지 않는다.
4. **연결·ACK 관측:** 부모 실패실행과 errors 실행ID, 안전한 E02 컨텍스트, E03/E04 상태·ACK, 동일 실제저장소의 전후 건수를 대조한다. 정상수습→알림만 실패→DLQ만 실패→둘다 실패에서 유한 종료·부모상태/참조 유지·재귀 없음·키/원문 미노출을 확인한다. 장애는 전용Mock/시험설정으로 주입하며 공유/운영 저장소를 초기화하지 않는다.
5. **원상복구:** 임시 오류 Code를 제거하고 부모/하위 정상 호출로 복구를 확인한다. 테스트복제본 정리·fault 해제·Credential/선택버전 확인을 기록한다. 실패 보고서와 수정/동일 조건 재시험 결과는 각각 보존한다.

공식 문서상 Error Trigger에는 부모가DB에 저장되지 않거나 trigger 단계에서 실패하면 execution.id가 없을 수 있다. 현재 handoff의 자동 실행 데이터 저장도 꺼져 있으므로 실제시험에서 ID 관측 가능 여부부터 확인해야 한다. 필요한 실행 메타데이터 확보 방식은 전용 비민감 시험부모에서 소유자가 정하며, 실행ID를 얻기 위해 실제 키가 담긴 전체 입력/headers를 공유용으로 저장하지 않는다. 참조가 없으면 수습은 진행하되 부모연결 확인을 완료로 표시하지 않는다.

근거: n8n 공식 [Error Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.errortrigger)와 [Error workflows](https://docs.n8n.io/build/flow-logic/handle-errors-gracefully.md). Error Trigger 자체 게시 불필수, 자동부모 실패로 발화, 누락 가능한 실행 메타데이터 및 부모 Settings 연결을 확인했다. 설치된 팀 n8n에서의 실제 동작은 아직 시험하지 않았다.

## 남은 범위와 인계

원민 P1-3 중 errors 로컬 구현은 완료했다. **실제 부모 설정/자동 발화·수습/복구와 app X-Api-Key·세션/권한·DB 영속성·동시/재시작 통합은 별도 미완료**다. 지혜님 실제 C05 duplicate 응답 반영·DLQ200·DB가 준비되면 같은 사례를 실제서비스에서 대조한다. 이후 P1-4 공통14종·팀·LLM3회·bench·실패재시험, P1-5 VM 회귀를 진행한다. 외부 메시지 전송·상대확인/승인·공통파일 변경·VM 배포는 하지 않았다.
