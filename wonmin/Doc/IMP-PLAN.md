# 안정성·이관·시험 · IMP-PLAN

주 담당: **이원민**. 지원 담당은 추가 배정.

> 상태: 단계 구성 초안. 모든 단계 미실행. 담당자가 SPEC의 요구 ID·실제 수정 파일·확인 명령을 채운 뒤 한 단계씩 구현한다.

## 파일 경계 · 저장소 루트 기준

`wonmin/workflows/oke-handoff.json`, `wonmin/workflows/oke-errors.json`, `wonmin/cases/`, `wonmin/requests/`, `wonmin/runs/`. 본체의 검사·호출 설정은 문의 담당에게 반영을 요청한다.

## 1단계 · 기대 결과·연결 계약

- [ ] 할 일: 팀 시나리오 초안과 handoff↔본체↔FastAPI 계약을 먼저 적는다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: 정상·인증·장애·중복 기대 결과 검토
- [ ] 실제 확인 결과·남은 문제·커밋: 실행 뒤 기록

## 2단계 · 티켓·알림·DLQ

- [ ] 할 일: data-api로 이관을 확인하고 FastAPI 호환 API에 연결할 수 있도록 설정을 나눈다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: 정상·동일 key·티켓 500·시간 초과·알림 확인
- [ ] 실제 확인 결과·남은 문제·커밋: 실행 뒤 기록

## 3단계 · 오류 처리·장애 시험

- [ ] 할 일: oke-errors 지정·게시와 주입·권한·개인정보·LLM 중단·외부 장애를 확인한다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: 고장 켜기→요청→고장 해제와 실제 보고서
- [ ] 실제 확인 결과·남은 문제·커밋: 실행 뒤 기록

## 4단계 · 전체 시험·결과서

- [ ] 할 일: 팀 VM 공통/팀/반복/bench와 FastAPI 통합 시험 후 수치를 결과서에 옮긴다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: runs 근거와 결과서·캡처의 일치
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

- [주제](../../docs/TOPIC.md) · [공통 API 계약](../../docs/API-CONTRACT.md) · [역할표](../../docs/ROLE-PLAN.md)
- [수업 방식과 연결 규칙](../../docs/DEVELOPMENT-FLOW.md)
- 수업 원문: [06-RELIABILITY-AND-SECURITY.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/06-RELIABILITY-AND-SECURITY.md) · [07-TESTING-GUIDE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/07-TESTING-GUIDE.md) · [08-SUBMISSION.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/08-SUBMISSION.md) · [VIBE-Q-TRETRY.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/76/VIBE-Q-TRETRY.md)
