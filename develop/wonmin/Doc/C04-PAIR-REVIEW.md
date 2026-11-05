# C04 최신 재확인 · 2026-11-05

**다혁님 C04 요청 생성·응답 매핑은 구현되었으며 원민 P1-1과 로컬 경계 검증에서 호환된다. 발신 노드는 여전히 Mock이므로 실제 C04 HTTP·n8n 연결 완료는 아니다.**

## 기준과 이전 검토 대비 변경

fetch 후 최신 `origin/feat/dahyeok-p0`는 `aac0dbf12e030ad7622fe3057654f866545c983b`다. 상대 README의 최신 개발본 `develop/dahyeok/workflows/oke-support-08.json`을 검토했다. P0-3 `f149ad0`에서 N20이 추가되었고, P1-1 `07`과 최신 `08`에서 원민 응답 대조·매핑 수정이 반영되어 있다.

이전 9bda763/P0-2 검토의 'N20 생성·매핑 미구현'은 당시 기록이다. **현재는 N20 Prepare handoff·Handoff gate·Map handoff가 존재한다.** ok=false/ticket 보존/alerts_down과 503/tickets_down도 처리한다. 이전 WM-04 알림 부분실패 매핑 우려는 현재 원민 임시 응답을 기준으로 해소되었다. 공통 ok 의미의 최종 합의까지 완료된 것으로 해석하지 않는다.

다만 현재 그래프의 실제 연결선은 다음과 같다.

```text
N20 Prepare handoff → N20 Handoff gate → N20 Mock C04 → N20 Map handoff
```

N20 Mock C04는 request_id 해시로 합성 ticket_id를 만들며 저장 API를 호출하지 않는다. 최신 JSON 전체의 HTTP Request 노드는 0개다. 따라서 상대가 C04를 '구현했다'는 설명은 요청 생성·Mock·결과 매핑에 해당하며 실제 발신 URL·X-Team-Key Credential·5초 timeout 설정까지 구현했다는 뜻은 아니다. 상대 README도 하위 호출이 Mock이고 프로젝트 n8n 게시·시험은 미실행이라고 명시한다.

## 이번 검증 방식

[check-c04-pair.mjs](../tools/check-c04-pair.mjs)에서 양쪽 원본 Code·JSON을 실행했다. 다혁님 브랜치 파일은 Git에서 메모리로 읽었고 원민 워크플로우·상대 그래프를 수정하지 않았다.

```text
다혁 N02~N07(직원·triage Mock 포함)
 → C04 진입 fixture(검색/LLM 전체 실행 제외)
 → 다혁 N20 Prepare의 실제 생성 요청
 → 원민 oke-handoff.json 로컬 어댑터
 → 원민 C05 HTTP Mock
 → 원민 실제 생성 응답
 → 다혁 N20 Map → N22 Finalize → Output filter
```

본체의 N20 Mock을 대체하는 부분은 **검증 스크립트 안의 경계 연결**이다. 소스 그래프에 HTTP 연결을 추가하거나 실제 n8n에 import/publish한 것이 아니다. 원민 H01의 Header Auth도 이 로컬 어댑터가 검증하지 않는다. 검색·Merge·writer/verifier·전체 문의 흐름은 이번 범위에서 실행하지 않았다. 수신/저장 서버로는 임시 키와 임의 loopback 포트의 독립 C05 HTTP Mock 하나를 사용하고 종료했다. 공유 서비스/DB는 호출하지 않았다.

## 관측 17건 결과

실제 보고서: [c04-pair-aac0dbf-review.json](../runs/c04-pair-aac0dbf-review.json). 커밋·양쪽 워크플로우·Mock·검토 스크립트 해시와 요청/응답/관측 건수를 포함한다. **17/17은 다음 경계 관측이 예상과 일치했다는 뜻이며, 전부 실제 C04 HTTP 호출이거나 공통 시나리오 PASS라는 뜻은 아니다.**

| 구분 | 관측 수 | 실제 결과 / 주입 범위 |
| --- | --- | --- |
| 정상·순차 중복 | 2 | 실제 C05 HTTP Mock 저장. 같은 ticket_id, 첫 duplicate=false→재요청 true, 저장1건. 본체 reason=no_evidence 유지 |
| 긴급·attempt3 | 2 | 실제 C05 HTTP Mock 저장. high/urgent 및 normal/max_attempts 유지, ticket 보존 |
| 알림 실패 | 1 | 티켓은 실제 C05 HTTP Mock에 저장, 알림503은 스크립트가 Response로 주입. 원민 ok=false/alerts_down의 ticket을 다혁 mapper와 최종 출력이 그대로 보존 |
| 티켓 장애·설정 오류 | 2 | C05 티켓503은 Response 주입→원민 HTTP200/tickets_down. 잘못된 모드는 원민503/tickets_down. 둘 다 본체 최종HTTP200·ticket=null·실패 안내, 저장 증가0 |
| 동일 키 동시4회 | 1 | 실제 C05 HTTP Mock 저장. 본체로 반환된 ID 동일, 신규1·중복3, 티켓 증가1건 |
| 잘못된 duplicate 타입·priority 불일치·timeout·401·403 | 5 | 합성 C04 상태/본문을 mapper에 주입. 모두 ticket=null/handoff_unavailable로 안전 출력, 성공으로 오인하지 않음. 실제 timeout/인증 시험은 아님 |
| 다혁 c04-wonmin-samples fixture | 4 | normal/duplicate/alerts_down/tickets_down을 현재 mapper에 직접 넣어 created/created/alerts_down/tickets_down 상태 확인. 합성 fixture임 |

실제 생성된 C04 요청의 필수6필드는 원민 H02를 통과했다. requester는 검증 경로의 user, category는 triage.type, title은 고정된 비민감 분류 요약, priority는 normal/high, request_id는 그대로 key로 전달된다. 원민에게서 돌아온 ticket의 ID/priority/duplicate와 alerted/dlq 타입 검증이 이루어지고, 성공 reason=null이면 본체의 원래 이관 사유를 유지했다.

본체가 실제 C04 수신 결과를 사용한다고 가정한 로컬 경계에서 `ok=false + ticket 존재 + alerts_down`을 티켓 실패로 버리지 않는 것을 확인했다. 이전 C04-01의 '요청 생성·매핑 없음'과 WM-04의 해당 매핑 우려는 **이 버전·로컬 범위에서는 갱신**한다. 실제 C05 중복 알림 ACK 필드 불일치(C05 검토)는 이번에 해결된 것이 아니다.

## 남은 연결 확인

- 다혁님: N20 Mock 대신 실제 `/webhook/oke-handoff` 호출, X-Team-Key Credential, 초기 timeout5초·중첩 자동 재시도0 및 응답 envelope 연결을 구현/설정해야 한다. 현재 code mapper가 받는 handoff_status/handoff_response를 HTTP 노드 출력에서 실제로 만들 수 있는지도 확인한다.
- 원민: P1-1의 현재 실제 결과와 mapper 호환을 확인했다. 티켓 재시도·실패 시 알림/DLQ 수습은 P1-2, Error Trigger와 실제 backend/DB 연결은 P1-3 대기다. 본 보고서는 그 기능까지 통과했다고 주장하지 않는다.
- 지혜님: C05 실제 인증·DB 저장·멱등/동시 거래·ACK 검증이 필요하다. 이번 서버는 원민 Mock이므로 백엔드 실연결 증거가 아니다.
- 오현님: 게시할 support 번호판을 하나로 선택하고 공식 키트와 전용 환경을 준비한 뒤 사람이 n8n 게시/시험해야 한다. 실제 실행 ID·HTTP 인증/timeout·동일 저장소 전후 건수·정리 결과를 기록해야 연결 완료로 판정할 수 있다.

외부 메시지 전송·상대 동의·공통 계약 변경은 수행하지 않았다. 검토 자료는 원민 폴더에만 기록했다. 이전 보고서는 삭제하지 않고 당시 상태로 보존한다.

재현(저장소 루트):

```bash
node develop/wonmin/tools/check-c04-pair.mjs
```

`--output NEW_BASENAME.json`은 own runs의 새 보고서만 생성하며 기존 증거를 덮어쓰지 않는다. Node 내장 기능과 Python 표준 라이브러리만 사용하고, 실행 중 임시 API 키를 출력/저장하지 않는다.
