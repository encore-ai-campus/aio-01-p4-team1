# 문의 처리 자동화 · IMP-PLAN

> 상태: 단계 구성 초안. 모든 단계 미실행. 담당자가 SPEC의 요구 ID·실제 수정 파일·확인 명령을 채운 뒤 한 단계씩 구현한다.

## 파일 경계

`workflows/oke-support.json`만 주 수정한다. 검색은 RAG의 `oke-search`, 이관은 안정성의 `oke-handoff`를 호출한다.

## 1단계 · 계약·역할 카드

- [ ] 할 일: 공통 웹훅·Agent 역할·search/handoff 연결 표와 기대 결과를 적는다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: 역할별 입력·출력·하지 않는 일 확인
- [ ] 실제 확인 결과·남은 문제·커밋: 실행 뒤 기록

## 2단계 · 웹훅 골격

- [ ] 할 일: Webhook→검사→임시 분류→Respond를 만들고 차단·400을 먼저 확인한다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: WF-08·WF-13 실제 확인
- [ ] 실제 확인 결과·남은 문제·커밋: 실행 뒤 기록

## 3단계 · 정상·검색·분류·검증

- [ ] 할 일: RAG 검색·접수 조회·답변·검증을 연결하고 정상과 근거 없음·보완·긴급을 구현한다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: 관련 공통 시나리오 및 하위 장애 응답 확인
- [ ] 실제 확인 결과·남은 문제·커밋: 실행 뒤 기록

## 4단계 · 전체 회귀

- [ ] 할 일: 안정성 담당과 장애·보안·중복을 통합하고 VM 결과를 설계서에 연결한다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: 공통 전체·팀 시험 결과를 runs에 연결
- [ ] 실제 확인 결과·남은 문제·커밋: 실행 뒤 기록

## 단계별 에이전트 요청 예시

```text
이 역할의 SPEC.md와 IMP-PLAN.md, 공통 API-CONTRACT.md를 읽어.
내가 지정한 한 단계만 구현해. 담당 경로를 지키고 공통 계약 변경이 필요하면 영향을 알려줘.
수정 파일·검사 결과·내가 실행할 확인 명령을 보고해.
구현과 실제 확인을 구분하고, 확인 전 통과 체크를 하지 마.
```

단계 완료 후 담당자가 직접 확인하고 커밋한다. n8n push·test는 수업 규칙대로 사람이 수행한다. 다음 단계 진행 여부는 담당자가 판단하며, 기능이 연결되면 관련 회귀 시험을 한다.

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [역할표](../../../docs/ROLE-PLAN.md)
- [수업 방식과 연결 규칙](../../../docs/DEVELOPMENT-FLOW.md)
- 수업 원문: [04-REFERENCE-ARCHITECTURE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md) · [03-SCENARIOS-AND-DATA.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/03-SCENARIOS-AND-DATA.md) · [09-AGENT-WORKING-RULES.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/09-AGENT-WORKING-RULES.md)
