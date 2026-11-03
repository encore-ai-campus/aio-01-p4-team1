# 문의 처리 자동화 · TODO

> 운영 기준: 팀장 배포 기본안으로 바로 구현한다. 이 문서의 기존 "합의·협의" 항목은 기준 적용 여부 확인이며, 기본안을 바꿀 때만 상대와 협의한다. 기준은 저장소 루트 docs/API-CONTRACT.md와 docs/DATA-AND-DB.md를 따른다.
작업 기준: [내 작업·협의 안내](../README.md) · [내 협의 기록](HANDOFF.md). 공통 파일과 상대 폴더는 직접 고치지 않고 소유자에게 요청한다.

주 담당: **다혁님**. 지원 담당은 추가 배정.

> 상태: 팀 합의 내용을 옮긴 참고 초안. 담당자가 자기 말로 고치고 필수·나중을 구분한 뒤 SPEC을 작성한다. 체크는 구현 완료가 아니라 요구 이해·검토 완료 표시다.

## 먼저 이해할 일

- [ ] 공통 웹훅으로 문의를 받아 입력·직원·권한·중복·주입을 검사한다.
- [ ] 분류·답변·검증 Agent를 역할별로 나누고 근거에 따라 답한다.
- [ ] 정보 부족·긴급·근거 없음·권한 제한을 정해진 route로 처리한다.
- [ ] RAG 검색과 접수 조회를 모아 답하고 외부 실패에도 정해진 응답을 낸다.

## 담당 경로 · 저장소 루트 기준

`develop/dahyeok/workflows/oke-support.json`만 주 수정한다. 검색은 RAG의 `oke-search`, 이관은 안정성의 `oke-handoff`를 호출한다.

## 담당자가 채울 것

- 내가 이해한 목적·사용자: 작성 필요
- 이번 일정에서 반드시 할 것 / 나중에 할 것: 작성 필요
- 의문·필요한 자료·다른 역할의 도움이 필요한 것: 작성 필요
- 요구 검토자·검토일: 미정

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [팀 헌장·역할](../../../docs/TEAM-CHARTER.md)
- [수업 방식과 연결 규칙](../../../docs/COORDINATION.md)
- 수업 원문: [04-REFERENCE-ARCHITECTURE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md) · [03-SCENARIOS-AND-DATA.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/03-SCENARIOS-AND-DATA.md) · [09-AGENT-WORKING-RULES.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/09-AGENT-WORKING-RULES.md)
