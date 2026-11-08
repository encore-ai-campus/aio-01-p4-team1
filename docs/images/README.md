# 제출 캡처

실제 실행 근거는 `live/`의 웹 화면 8장과 n8n 실행 화면 6장이다. 아래 목록에서 이미지와 해당 시험 기록을 함께 확인할 수 있다.

캡처에는 비밀번호·키·연락처를 넣지 않으며, 실제 응답·티켓·실행 ID가 원본 보고서와 일치해야 한다. 제출 기준과 시험 범위는 [제출 취합 안내](../../SUBMISSION.md), [실행 결과서](../EXECUTION-RESULT.md)를 따른다.

## 실제 배포 서비스 화면

`live/`는 배포된 서비스에 로그인해 직접 캡처한 화면이다. 새 질문 전송·티켓 수정·장애 재설정 없이 기존 시험 기록을 열어 촬영했다. 가상 직원 이름은 제공 데이터이며 계정·비밀번호·키는 화면에 넣지 않았다.

| 화면 | 파일 | 기존 시험 근거 |
| --- | --- | --- |
| 빈 로그인 화면 | [01-login.png](live/01-login.png) | 계정·비밀번호 미입력 |
| 직원 질문 입력 | [02-employee-question.png](live/02-employee-question.png) | 실제 로그인 후 입력 화면, 질문 미전송 |
| VPN 자동 안내 | [03-normal-answer.png](live/03-normal-answer.png) | 기존 svc-normal-vpn 요청 |
| 정보 부족 보완 질문 | [04-clarification.png](live/04-clarification.png) | 기존 svc-clarification 요청 |
| 완료 티켓·담당자 답변 재조회 | [05-employee-completed.png](live/05-employee-completed.png) | 기존 T-2037 |
| 장애 시험 후 복구된 접수 | [06-fault-recovered-request.png](live/06-fault-recovered-request.png) | 기존 T-2040. 장애 진행 중 화면과 구분 |
| 관리자 처리 결과 | [07-admin-ticket.png](live/07-admin-ticket.png) | 기존 T-2037. 저장 동작 없음 |
| 실패·복구 알림 | [08-admin-alerts.png](live/08-admin-alerts.png) | 기존 요청별 장애·복구 알림 |

캡처 파일 해시·요청 ID·로그인/로그아웃·쓰기 차단 확인은 [캡처 기록](../../runs/ui-captures-20261108.json)에 있다. 실제 응답·DB 근거는 캡처 기록의 evidence 경로로 연결한다.

## 실제 n8n 실행 화면

기존 `oke-support` 실행 이력 3건을 열어 흐름과 `N23 Respond` 최종 응답을 각각 촬영했다. 새 실행·재시도·편집·게시를 하지 않았다.

| 기존 실행 | 흐름 화면 | 최종 응답 화면 | 확인한 결과 |
| --- | --- | --- | --- |
| 정상 · ID 256 | [실행 흐름](live/09-n8n-normal-execution.png) | [응답](live/10-n8n-normal-result.png) | `password-policy` 근거, 자동 답변, 티켓 없음 |
| 인젝션 차단 · ID 271 | [실행 흐름](live/11-n8n-injection-execution.png) | [응답](live/12-n8n-injection-result.png) | 차단 응답, 티켓 없음 |
| 긴급 이관 · ID 276 | [실행 흐름](live/13-n8n-handoff-execution.png) | [응답](live/14-n8n-handoff-result.png) | 담당자 접수, 긴급 티켓 `T-2039` |

실행 ID·요청 ID·기존 시험 근거·이미지 해시·로그인/로그아웃·워크플로우 변경 없음은 [n8n 캡처 기록](../../runs/n8n-ui-captures-20261108.json)에서 확인한다. n8n의 노드 실행 시간과 호출자의 HTTP 응답 시간은 측정 구간이 다르다.

## 과거 화면 설계안

`planned/`의 4장은 구현 전 화면 설계 이력이다. [화면 설계 설명](../PREVIEW.md)에서 사용하며, 실제 구현·시험 증거에는 포함하지 않는다.

| 설계 화면 | 파일 |
| --- | --- |
| 직원 질문·내 문의 | [ui-employee.png](planned/ui-employee.png) |
| 관리자 티켓·알림 | [ui-admin.png](planned/ui-admin.png) |
| 관리자 계정 발급 | [ui-accounts.png](planned/ui-accounts.png) |
| 로그인 | [ui-login.png](planned/ui-login.png) |

화면 설계 원본은 [미리보기 HTML](../previews/screens.html)이다. 현재 워크플로우 구조는 [워크플로우 설계서](../WORKFLOW-DESIGN.md)에서 확인한다.
