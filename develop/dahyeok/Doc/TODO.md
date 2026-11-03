# 문의 처리 자동화 · TODO

읽는 순서: [README](../README.md) → 이 문서 → [SPEC](SPEC.md) → [IMP-PLAN](IMP-PLAN.md). 변경 요청만 [HANDOFF](HANDOFF.md)에 쓴다.

## 목적과 사용자

제공 직원 6명이 IT 문제를 물었을 때 잘못된 입력·주입·타인 접수 조회를 먼저 막고, 자기 권한의 규정과 접수 상태로 답을 받도록 한다. 자동 답변할 근거가 없거나 검증이 실패하면 추측하지 않고 한 번만 티켓을 접수한다. 직원에게는 보완할 내용과 접수 성공/실패를 사실대로 알려 준다.

주 담당은 다혁님이며 지원 담당은 미배정이다. 아래 체크는 **향후 구현·실제 검증 완료** 표시다. 현재 모두 미실행이다.

## 반드시 할 일

| 우선 | 할 일과 이유 | 연결 요구 | 시작 단계 |
| --- | --- | --- | --- |
| 필수 | 공통 웹훅 필드·5개 route·400 codes를 유지해 화면/공통 시험과 같은 본체를 사용 | SUP-01 | P0-1 |
| 필수 | 직원 부서로 권한을 만들고 입력·주입을 LLM 전에 검사해 권한 주장과 공격을 차단 | SUP-02 | P0-1 |
| 필수 | triage/writer/verifier를 분리하고 JSON 파싱·검증을 Code가 담당 | SUP-03 | P0-2, P1-2 |
| 필수 | 정보 부족은 attempt 1·2에서 질문하고 3 이상에서 이관; 새 차례는 새 ID | SUP-04 | P0-2 |
| 필수 | 검색과 자기 접수 조회를 두 갈래로 연결하고 권한·빈 검색·실패를 구별 | SUP-05 | P1-1 |
| 필수 | 근거·검증·점수 기준이 충족된 답만 자동 응답하고 연락처를 가림 | SUP-06 | P1-2 |
| 필수 | 긴급·보안 사고, 근거 없음, 검증/LLM 실패를 handoff로 보내고 부분 실패를 정확히 표시 | SUP-07 | P1-3 |
| 필수 | 같은 request_id는 새 티켓을 만들지 않고, 타인 결과는 반환하지 않음 | SUP-08 | P1-4 |
| 필수 | 하위 timeout·인증 실패·5xx에서 응답을 수습하고 예상 밖 오류만 Error Workflow로 전달 | SUP-09 | P1-3, P1-4 |
| 필수 | 공통 14유형과 팀 예외·LLM 반복·검색 품질·처리시간을 실제 측정 자료로 전달 | SUP-10 | P1-5 |

- [ ] P0 입력/보완/규칙 차단을 실제 확인한다.
- [ ] P1 검색·검증·긴급·하위 실패를 실제 확인한다.
- [ ] P1 후속 단계에서 중복·권한·장애·회귀·측정 증거를 넘긴다.

## P2 선택 고도화 · 필수 통합/시험 이후

- 검색어 재작성은 기본 구현의 검색 1회가 완성된 뒤 최대 **추가 1회**까지만 검토한다. 권한 목록은 유지하고 오류/인증 실패에는 재검색하지 않는다.
- writer 재작성 루프, 별도 guard Agent, 비동기 큐·차단기, 텔레그램은 필수 시나리오와 실제 측정 뒤 검토한다. 기본 검증 실패는 바로 이관한다.
- 모델·차원·벡터 저장소·API 변경은 개인 최적화로 선행하지 않는다.

## 적용할 기준과 남은 정책

분류 대상은 [TOPIC](../../../docs/TOPIC.md)의 6개 문의 범위, API/하위 호출은 [API-CONTRACT](../../../docs/API-CONTRACT.md), 문의 문맥 저장은 [DATA-AND-DB](../../../docs/DATA-AND-DB.md)의 `app.inquiries`를 적용한다. 검색 권한은 all 또는 all+it, top_k=3, 자동 답변 임계값은 실측 뒤 반영한다.

공통 문서에 없는 세부 오류 코드·결과 재사용 API·시간 예산·중복 응답 표시 제안은 HANDOFF의 DH-CHG-01~04다. 이것은 새 정책의 승인 기록이 아니다. 확정 기준 범위의 노드와 계약 Mock부터 만들며 전체 개발을 대기시키지 않는다. 검토자·검토일은 실제 검토 후 기록한다.

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [팀 헌장·역할](../../../docs/TEAM-CHARTER.md)
- [수업 방식과 연결 규칙](../../../docs/COORDINATION.md)
- 수업 원문: [04-REFERENCE-ARCHITECTURE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md) · [03-SCENARIOS-AND-DATA.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/03-SCENARIOS-AND-DATA.md) · [09-AGENT-WORKING-RULES.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/09-AGENT-WORKING-RULES.md)
