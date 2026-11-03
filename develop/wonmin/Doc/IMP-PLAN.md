# 원민님 · 구현 계획

담당 범위·변경 검토 상대·결과물은 [내 README](../README.md), 통과 요구는 [SPEC](SPEC.md)을 따른다.
공통 기준대로 구현하며 변경할 때만 [HANDOFF](HANDOFF.md)에 요청한다. 모든 단계는 아직 미실행이다.
각 단계는 확인 가능한 작은 PR로 나누고 실제 결과를 아래에 기록한다.

## P0

- [ ] 작업: 공통 계약을 적용하고 공통 14유형을 읽어 팀 시나리오 기대를 먼저 작성한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: 키트 원본 기대 유지·팀 정상/경계/권한/이관/장애 입력 초안
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## P1-1

- [ ] 작업: data-api 기준 handoff·중복·재시도·DLQ·알림을 구현한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: 정상/500/timeout/중복 응답과 ops 관측 일치
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## P1-2

- [ ] 작업: errors를 지정·게시하고 FastAPI 연동 설정을 따로 검증한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: 같은 본체의 설정 전환, 실제 FastAPI 저장·권한·중복 검증
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## P1-3

- [ ] 작업: 공통·팀·LLM 반복·장애·성능·VM 회귀와 시연을 정리한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: 가짜 PASS 없이 실패/재시험 포함, 고장 해제·마스킹 확인
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## 단계 운영

구현 → 자기 기능 확인 → 결과 기록 → 작은 PR 순서다. 다른 담당자 소스·루트 공통 파일은 수정하지 않는다.
실제 서비스가 준비되기 전에는 계약 기반 Mock으로 진행하며, 연결 뒤에는 Mock 여부와 실제 응답을 구별한다.
n8n check 뒤 push·test는 사람이 수행한다. PR 전 수정·스테이징 경로와 비밀값 포함 여부를 확인한다.
새 기능의 관련 회귀를 수행하고, 제출 문서에 필요한 실제 설계/측정/보고서를 자기 Doc/SUBMISSION-NOTES.md로 전달한다.

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [팀 헌장·역할](../../../docs/TEAM-CHARTER.md)
- [수업 방식과 연결 규칙](../../../docs/COORDINATION.md)
- 수업 원문: [06-RELIABILITY-AND-SECURITY.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/06-RELIABILITY-AND-SECURITY.md) · [07-TESTING-GUIDE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/07-TESTING-GUIDE.md) · [08-SUBMISSION.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/08-SUBMISSION.md) · [VIBE-Q-TRETRY.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/76/VIBE-Q-TRETRY.md)
