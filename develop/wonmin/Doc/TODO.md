# 안정성·이관·시험 · TODO

작업 기준: [내 작업·협의 안내](WORK-GUIDE.md) · [내 협의 기록](HANDOFF.md). 공통 파일과 상대 폴더는 직접 고치지 않고 소유자에게 요청한다.

주 담당: **원민님**. 지원 담당은 추가 배정.

> 상태: 팀 합의 내용을 옮긴 참고 초안. 담당자가 자기 말로 고치고 필수·나중을 구분한 뒤 SPEC을 작성한다. 체크는 구현 완료가 아니라 요구 이해·검토 완료 표시다.

## 먼저 이해할 일

- [ ] 이관 티켓·알림·실패 대기열과 예상 밖 오류 처리를 구현한다.
- [ ] 외부 지연·장애·인증 실패·중복에서도 안전하게 처리한다.
- [ ] 공통 14유형과 팀 5개 이상 시나리오의 기대 결과를 먼저 정한다.
- [ ] 실제 시험·반복·속도 보고서와 실패·재시험 기록을 결과서로 정리한다.

## 담당 경로 · 저장소 루트 기준

`develop/wonmin/workflows/oke-handoff.json`, `develop/wonmin/workflows/oke-errors.json`, `develop/wonmin/cases/`, `develop/wonmin/requests/`, `develop/wonmin/runs/`. 본체의 검사·호출 설정은 문의 담당에게 반영을 요청한다.

## 담당자가 채울 것

- 내가 이해한 목적·사용자: 작성 필요
- 이번 일정에서 반드시 할 것 / 나중에 할 것: 작성 필요
- 의문·필요한 자료·다른 역할의 도움이 필요한 것: 작성 필요
- 요구 검토자·검토일: 미정

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [역할표](../../../docs/ROLE-PLAN.md)
- [수업 방식과 연결 규칙](../../../docs/DEVELOPMENT-FLOW.md)
- 수업 원문: [06-RELIABILITY-AND-SECURITY.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/06-RELIABILITY-AND-SECURITY.md) · [07-TESTING-GUIDE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/07-TESTING-GUIDE.md) · [08-SUBMISSION.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/08-SUBMISSION.md) · [VIBE-Q-TRETRY.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/76/VIBE-Q-TRETRY.md)
