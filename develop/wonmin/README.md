# 원민님 · 이관·오류 수습·시험

**목표:** 티켓 중복과 저장 실패를 안전하게 처리하고 시험으로 동작을 증명한다. 작업 폴더는 develop/wonmin. 아래 그림은 구현 전 설계다.

<img src="../../docs/images/planned/flow-handoff.svg" width="620" alt="이관 설계">

[예상 밖 오류 설계 그림](../../docs/images/planned/flow-errors.svg) · [평가 기준](../../docs/EVALUATION-GUIDE.md)

## 내가 만들 것

- workflows/oke-handoff.json: 같은 키 티켓1건·알림·DLQ·제한 재시도·부분 실패.
- workflows/oke-errors.json: Error Trigger·가린 오류·독립 수습·유한 종료.
- cases/team.json 5개 이상·요청 파일·공통14유형/LLM3회/bench·실제 runs.
- 실패→수정→동일 조건 재시험 자료와 실행 결과서 집계.

## 지금 첫 작업 · P0

저장소 루트에서 cd develop/wonmin 후 [IMP-PLAN P0](Doc/IMP-PLAN.md)의 팀 사례·handoff 사례·시연 요청을 먼저 쓴다. SPEC의 TM 사례를 가져와 입력·조건·기대·부작용·정리를 고정한다. 공통 common.json·flow.py는 실제 키트가 준비되면 원본을 확보하고 버전·실행 위치를 기록한다.

## 정해진 것과 내가 정할 것

| 구분 | 적용·결정 |
| --- | --- |
| 확정 | C04/C05, request_id 멱등, /dlq·app event_key, 예상 오류와 Error Trigger 분리, 실제 ACK·14+5이상·LLM3회 |
| 담당자 검증 | 모드별 DLQ 변환·실제 호출/관측 일치·시간 예산 검증·실패 재현. 지혜님 저장/관측, 다혁님 결과 매핑과 확인. 미정 부분실패 필드·진행 중 응답은 공통 계약에 반영 후 최종 판정 |
| 선택 고도화 | 자동 replay·알림 묶음·추가 대시보드는 필수 시험 뒤 |

## 바로 볼 예제

[티켓 처리](../../docs/references/workflows/intake.json.example) · [오류 알림](../../docs/references/workflows/errors.json.example) · [재처리](../../docs/references/workflows/replay.json.example)

키·오류 출력·Error Trigger·성공 건 해제를 참고한다. 오류 예제는 알림만 있으므로 우리 독립 DLQ·마스킹·모드별 계약을 추가한다. replay는 복구 방식 참고이며 P1에서 새 자동 복구 서비스를 만들라는 뜻이 아니다. [적용표](../../docs/references/README.md).

## 누구에게 받고 무엇을 넘기나

- 지혜님에게 저장 API·모드·실제 관측법을 받고 다혁님에게 C04 성공/실패 JSON과 errors 설정 정보를 넘긴다.
- 기능 담당자에게 재현 입력·기대/실제·보고서를 전달하고 소유자가 수정한 뒤 같은 조건으로 재시험한다.
- 오현님에게 실제 JSON·팀 사례·요청·runs·실패/재시험·시연 순서와 결과서 집계를 넘긴다.
- 완료 기준: 티켓1건·부분 실패 티켓 보존·무한 재귀 없음·모드 일치·필수 실제 보고서. HTTP200만으로 PASS 처리하지 않는다.
- 보고: 변경 파일 / 확인 입력·명령 / 기대와 실제 / 실패·수정 소유자·다음 상대. n8n 게시·시험은 사람이 확인한다.

## 내 CLI 첫 요청

    내 README·AGENTS·평가 기준·SPEC TM 사례를 읽고 IMP-PLAN P0의 시험 입력부터 작성해.
    develop/wonmin 밖은 수정하지 말고 원본 공통 판정을 바꾸지 마.
    입력·기대·부작용·정리와 미정 정책을 구분해서 보고해.

상세: [TODO](Doc/TODO.md) · [SPEC](Doc/SPEC.md) · [IMP-PLAN](Doc/IMP-PLAN.md) · [HANDOFF](Doc/HANDOFF.md).
