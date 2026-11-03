# 안정성·이관·시험 · SPEC

작업 기준: [내 작업·협의 안내](WORK-GUIDE.md) · [내 협의 기록](HANDOFF.md). 공통 파일과 상대 폴더는 직접 고치지 않고 소유자에게 요청한다.

주 담당: **원민님**. 지원 담당은 추가 배정.

> 상태: 검토용 요구 초안. 아래 확인 기준을 담당자가 실제 입력·출력·오류 예시와 확인 방법으로 구체화한다. 테스트 통과 기록은 아니다.

## 요구와 확인 기준

| ID | 요구 | 기대 결과·확인할 것 |
| --- | --- | --- |
| REL-01 | 이관·중복 | key=request_id로 티켓 생성. 재요청 시 티켓 한 건·같은 ticket_id·duplicate 상태를 확인. 긴급은 high+알림. |
| REL-02 | 장애 수습 | 401/403은 재시도 안 함. 429/5xx/timeout은 상한 있는 재시도. 티켓 장애 시 ticket=null·사유·DLQ/알림 확인. |
| REL-03 | 오류 워크플로우 | Error Trigger를 지정·게시하고 실제 예상 밖 오류로 동작 확인. 예상된 외부 실패와 구분하며 로그·알림의 개인정보를 가림. |
| REL-04 | 시험 증거 | 공통 14유형·팀 5개 이상·LLM 경로 3회 반복·bench·VM 회귀 기록. 실패·재시험을 모두 기록하고 기대값을 바꾸지 않음. |
| REL-05 | 실행 모드 | 공통 시험의 data-api 고장·reset·ops 관측 대상과 실제 요청 경로 일치 확인. FastAPI 어댑터 연결 뒤 저장·권한·중복도 별도 통합 시험. |

## 구현 전에 담당자가 정할 것

- [ ] handoff의 정확한 입출력·실패 사유·본체 전달 방식
- [ ] DLQ·알림·실행 로그의 저장 위치와 중복 정책
- [ ] data-api 기준 공통 시험 설정과 FastAPI 연동 설정·전환 방법을 관련 담당과 합의
- [ ] 팀 5개 이상 사례·시간 한도·반복·보고서 파일명과 시연 순서

## 각 요구에 추가할 실행 예시

- 요구 ID / 필수·나중:
- 입력·사전 조건:
- 예상 HTTP 상태·출력 JSON 또는 화면 상태:
- 실패·권한·경계 사례:
- 확인 명령·시나리오 ID:
- 연결 담당자와 합의한 날짜:

공통 계약과 중복되는 스키마는 [API-CONTRACT.md](../../../docs/API-CONTRACT.md)를 참조한다. 바꿀 내용은 내 HANDOFF에 제안한다. 오현님이 공통 문서를 반영한 뒤 각 담당자는 자기 SPEC만 갱신한다. 기준을 바꾸지 않고 구현을 고쳐야 하는 실패와, 요구 변경을 구분한다.

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [역할표](../../../docs/ROLE-PLAN.md)
- [수업 방식과 연결 규칙](../../../docs/DEVELOPMENT-FLOW.md)
- 수업 원문: [06-RELIABILITY-AND-SECURITY.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/06-RELIABILITY-AND-SECURITY.md) · [07-TESTING-GUIDE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/07-TESTING-GUIDE.md) · [08-SUBMISSION.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/08-SUBMISSION.md) · [VIBE-Q-TRETRY.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/76/VIBE-Q-TRETRY.md)
