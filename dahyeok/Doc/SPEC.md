# 문의 처리 자동화 · SPEC

작업 기준: [내 작업·협의 안내](WORK-GUIDE.md) · [내 협의 기록](HANDOFF.md). 공통 파일과 상대 폴더는 직접 고치지 않고 소유자에게 요청한다.

주 담당: **임다혁**. 지원 담당은 추가 배정.

> 상태: 검토용 요구 초안. 아래 확인 기준을 담당자가 실제 입력·출력·오류 예시와 확인 방법으로 구체화한다. 테스트 통과 기록은 아니다.

## 요구와 확인 기준

| ID | 요구 | 기대 결과·확인할 것 |
| --- | --- | --- |
| WF-01 | 공통 입출력 | 교사 계약의 필수 필드·route를 보존. 잘못된 입력은 HTTP 400과 codes, 주입은 차단 및 LLM 호출 없음. |
| WF-02 | 보완·이관 | attempt < 3의 정보 부족은 보완 질문, attempt >= 3이면 이관. 근거 없음은 지어내지 않고 이관. |
| WF-03 | 역할·근거 검증 | triage·writer·verifier를 분리. JSON 해석 실패는 안전하게 이관. 자동 답변은 권한 있는 sources와 검증 결과를 충족. |
| WF-04 | 하위 연결 | search·handoff 요청/응답·인증·시간 제한을 표로 정의. 하위 실패와 LLM 중단을 본체 응답으로 수습. |
| WF-05 | 공통 회귀 | WF-01~WF-13 및 WF-02b의 기대값 유지. 검색·접수 조회 병렬 구조, 보완·재검색 루프 최대 횟수를 설계서에 기록. |

## 구현 전에 담당자가 정할 것

- [ ] 분류 유형·분류 JSON·긴급 판단·검증 필드와 실패 사유
- [ ] search·handoff 연결선별 정확한 필드와 시간 제한
- [ ] 중복 처리 결과 캐시·보완 질문 문맥 저장 위치를 백엔드와 합의

## 각 요구에 추가할 실행 예시

- 요구 ID / 필수·나중:
- 입력·사전 조건:
- 예상 HTTP 상태·출력 JSON 또는 화면 상태:
- 실패·권한·경계 사례:
- 확인 명령·시나리오 ID:
- 연결 담당자와 합의한 날짜:

공통 계약과 중복되는 스키마는 [API-CONTRACT.md](../../docs/API-CONTRACT.md)를 참조한다. 바꿀 내용은 내 HANDOFF에 제안한다. 오현이 공통 문서를 반영한 뒤 각 담당자는 자기 SPEC만 갱신한다. 기준을 바꾸지 않고 구현을 고쳐야 하는 실패와, 요구 변경을 구분한다.

## 공통 자료

- [주제](../../docs/TOPIC.md) · [공통 API 계약](../../docs/API-CONTRACT.md) · [역할표](../../docs/ROLE-PLAN.md)
- [수업 방식과 연결 규칙](../../docs/DEVELOPMENT-FLOW.md)
- 수업 원문: [04-REFERENCE-ARCHITECTURE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md) · [03-SCENARIOS-AND-DATA.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/03-SCENARIOS-AND-DATA.md) · [09-AGENT-WORKING-RULES.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/09-AGENT-WORKING-RULES.md)
