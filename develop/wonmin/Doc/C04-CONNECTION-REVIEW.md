# C04 support → handoff 연결 확인 · 2026-11-04

이 문서는9bda763/P0-2 당시 기록이다. 2026-11-05 최신aac0dbf의 요청 생성·응답 매핑 구현 및 로컬 경계 검증은 [C04-PAIR-REVIEW.md](C04-PAIR-REVIEW.md)를 따른다. 아래 원 관측은 보존한다.

**다혁님 SPEC의 요청 표본은 원민 입력 검사에 적합하다. 최신 본체에는 C04 HTTP 호출·결과 매핑이 아직 없어 실제 연결 완료로 처리할 수 없다.**

확인 대상은 fetch 후 `origin/feat/dahyeok-p0`의 `9bda7639aaeee3f6dca59f6aabd91e61fa05a847`이다. `oke-support.json`은 P0-1 보존본이고 최신 개발본은 `workflows/oke-support-02.json`(P0-2)이다. 두 버전의 웹훅 경로는 같아 동시에 게시하면 안 된다는 상대 README/HANDOFF를 확인했다. 이번에는 어떤 버전도 게시하지 않았다.

원민은 `ceb8efe`의 P1-1 `oke-handoff.json`을 대조했다. 워크플로우·다혁님 파일·공통 계약을 변경하지 않았다. 코드와 문서의 해시·원본 관측은 [c04-dahyeok-9bda763-review.json](../runs/c04-dahyeok-9bda763-review.json)에 기록했다.

## 요청·응답 연결표

| 항목 | 다혁님 현재 상태 | 원민 수신/결과 | 판단 |
| --- | --- | --- | --- |
| 주소 | SPEC에 POST `http://n8n:5678/webhook/oke-handoff`, 실제 HTTP 노드 없음 | H01 POST 경로 oke-handoff | 문서상 일치, 실제 호출 미구현 |
| 인증 | SPEC·공통은 X-Team-Key, C04 호출 노드/Credential은 없음 | H01 Header Auth·WONMIN_X_TEAM_KEY 교체용 참조 | 실제 같은 키 연결 확인 대기. 본체 입구 인증 설정과 C04 발신 인증은 별개 |
| request_id/requester | SPEC 표본 dh-urgent-001 / 박서연. N20 생성부 없음 | ID 보존→C05 key, 제공 직원 이름 확인 | 문서 표본 수신 검사 적합. 실제 user→requester 변환 미검증 |
| title/category/priority/reason | 가린 요약 / security / high / urgent 표본 | 필수 문자열, normal/high, H02 마스킹 | 표본 적합. title 요약·category/priority/reason 생성 코드 미구현 |
| evidence_summary | 선택 문자열 표본 | 수신 타입 확인 후 C05로 전달하지 않음 | 선택 필드 적합 |
| timeout/재시도 | C04 HTTP 노드 없음 | 원민 티켓 1초·알림0.6초, 자동 재시도0. 공통 support→handoff 초기값은5초 | 본체의 실제 5초 설정·재시도0 검증 불가 |
| 정상/중복 응답 | SPEC는 ticket 보존·최종 reason=원래 이관 사유. 실제 mapper 없음 | HTTP200, ticket(ticket_id/priority/duplicate), reason=null, alerted=true, dlq=false | 문서상 일치, 실제 매핑·duplicate 유지 미검증 |
| tickets_down | SPEC는 route=담당자 이관, ticket=null, 실패 사유와 안내 | 현재 P1-1은 안전 실패 응답만 있음 | HTTP200 실패 형태는 대조 가능. 독립 알림/DLQ 수습은 원민 P1-2 미구현 |
| alerts_down | SPEC 예시는 ok=true와 ticket 유지 | 원민은 ticket 유지, alerts_down, alerted=false, 보수적 임시 ok=false | **WM-04 미정 경계.** 구현될 본체가 ok=false만 보고 ticket을 버리면 안 됨. 현재 본체 mapper가 없어 실제 버그로 확정하지 않음 |

다혁님 SPEC에서 그대로 추출한 [긴급 C04 요청](../requests/c04-dahyeok-urgent.json):

```json
{"request_id":"dh-urgent-001","requester":"박서연","title":"피싱 링크 클릭 신고 및 VPN 접수 문의","category":"security","priority":"high","reason":"urgent","evidence_summary":"보안 사고 문의. 세부 개인정보는 제외."}
```

이 표본을 원민 실제 H02 Code에 넣은 결과 valid=true, key=dh-urgent-001/requester=박서연/priority=high로 매핑됐다. 문서 표본 1개 수신 적합 결과이며, 다혁님 생성 코드나 C04 HTTP 호출을 실행한 결과는 아니다.

## 최신 P0-2 로컬 관측 6건

저장된 원격 JSON의 Code·표현식·분기를 원민 로컬 어댑터에서 실행했다. 다혁님 원격 JSON 전체를 본인 프로젝트로 복제하지 않았고 Git에서 메모리로 읽었다. 실제 Agent·Header Auth·n8n 엔진·HTTP 연결을 실행한 도구가 아니다.

| 입력 | 실제 로컬 결과 | C04 발신 |
| --- | --- | --- |
| 다혁 clarify-1 / clarify-2 | 각각 보완 질문, ticket=null | 각0회 |
| 다혁 clarify-3 (attempt=3) | N07 decision=handoff_mock, reason=max_attempts. 최종 담당자 이관/ticket=null/reason=not_implemented | 0회 |
| 다혁 clarify-context | decision=pending, 최종 담당자 이관/ticket=null/reason=not_implemented | 0회 |
| 원민 합성 긴급 문의 | N07 handoff_mock/urgent/high. 최종 담당자 이관/ticket=null/reason=not_implemented | 0회 |
| 다혁 injection | 차단, ticket=null | 0회 |

6/6은 **현재 P0-2 골격의 예상 상태를 확인**했다는 의미다. 최신 개발본에는 발신 HTTP Request 노드가 0개이고 N20 Prepare/Call/Map도 없다. attempt>=3에서 티켓이 생기는 최종 기능이나 공통 WF-02b 통과를 뜻하지 않는다. 특히 route=담당자 이관만으로 접수 성공 판정하지 않았다.

## 다혁님·오현님께 넘길 연결 항목

다혁님 계획상 P0-3의 새 번호판에 N20을 구현할 때 다음을 확인해야 한다.

- 검증한 user→requester, request_id 유지, 가린 title, triage.type→category 및 normal/high·reason을 C04로 전송. X-Team-Key Credential 연결, HTTP timeout5초·중첩 자동 재시도0 확인.
- HTTP200은 처리 결과이므로 ticket과 reason을 검증한다. 성공 reason=null이면 urgent/no_evidence 등 본체 원래 사유를 유지하고, tickets_down/alerts_down이면 하위 사유를 보존한다.
- 신규·중복의 같은 ticket_id와 원래 priority/duplicate를 유지한다. alerts_down에서 ok 값과 무관하게 확인된 ticket을 보존하는 경계를 WM-04와 함께 확정한다. 긴급 후속 검색·출력 실패 때문에 재접수하지 않는다.
- timeout 후 실제 저장 가능성이 있으므로 같은 ID 재요청 원칙과 확인 불가 안내를 유지한다. alerted/dlq를 HTTP200만으로 추정하지 않는다.
- 게시 버전은 오현님과 하나만 선택한다. 공식 80일차 flow.py/common 원본은 아직 미확보다. 다혁님 tools/flow.py도 명시적으로 자체 P0 도구라 공식 키트로 대체하지 않았다.

원민이 대신 N20을 만들거나 상대 파일을 고치지 않았다. 이는 후속 검토 자료이며 외부 메시지 전송·상대 동의·실제 연결 완료가 아니다. C04의 실제 인증/timeout/응답 매핑과 n8n 실행 ID·저장 관측은 제공자 구현과 사람이 게시·시험한 뒤 확인한다.

재현(저장소 루트, Node 내장 기능만 사용):

```bash
node develop/wonmin/tools/check-c04-dahyeok.mjs
```

`--output NEW_BASENAME.json`은 원민 runs 아래 새 보고서만 생성한다. 고정 커밋과 알려진 미구현 상태를 확인하는 조사 스크립트이며 향후 본체 구현을 통과시키는 범용 판정기가 아니다.
