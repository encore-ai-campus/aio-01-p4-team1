# 제출 캡처

## 예상 화면·설계 그림

planned/는 개발 전에 그린 화면과 노드 설계다. [PREVIEW](../PREVIEW.md)와 [워크플로우 설계](../WORKFLOW-DESIGN.md)에서 사용하며 실제 구현·시험 증거로 집계하지 않는다. 화면 원본은 previews/screens.html, SVG 생성 원본은 previews/generate_diagrams.py다.

## 실제 실행 증거

- **작성:** 설계·실행 결과서와 발표에 실제 사용하는 n8n·웹 화면 캡처.
- **규칙:** 비밀번호·키·연락처를 가리고, 파일명에 시나리오와 장면을 드러낸다. 사용하지 않는 캡처는 넣지 않는다.
- **결과:** 관련 문서에서 각 캡처를 링크하고, 캡처가 실제 실행 보고서와 같은 결과를 보여야 한다.
- **기준 문서:** [제출 취합 안내](../../SUBMISSION.md), [실행 결과서](../EXECUTION-RESULT.md).

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
