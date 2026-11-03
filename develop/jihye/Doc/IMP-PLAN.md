# 지혜님 · 구현 계획

담당 범위·변경 검토 상대·결과물은 [내 README](../README.md), 통과 요구는 [SPEC](SPEC.md)을 따른다.
공통 기준대로 구현하며 변경할 때만 [HANDOFF](HANDOFF.md)에 요청한다. 모든 단계는 아직 미실행이다.
각 단계는 확인 가능한 작은 PR로 나누고 실제 결과를 아래에 기록한다.

## P0

- [ ] 작업: C01/C02/C05/C06/C07 기준을 자기 계획에 반영하고 서버·DB·pgvector 실행 골격과 healthcheck를 준비한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: 서버/DB 준비 상태, 마이그레이션·초기 관리자·설치/실행 명령 재현
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## P1-1

- [ ] 작업: 로그인·로그아웃·첫 비밀번호 변경·관리자 계정 발급/관리·본인 권한을 구현한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: 정상·401·403·비활성 계정·세션 정책 확인
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## P1-2

- [ ] 작업: 문의 저장·티켓·알림·관리자 처리와 n8n 어댑터를 구현한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: 같은 request_id의 티켓 한 건, 타인 문의 차단, 서버 오류 수습
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## P1-3

- [ ] 작업: 실제 화면·handoff·pgvector·팀 VM을 연결하고 재시작/초기화 절차를 검증한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: 기록 유지·관련 담당자 실제 연결·배포 인수인계
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## 단계 운영

구현 → 자기 기능 확인 → 결과 기록 → 작은 PR 순서다. 다른 담당자 소스·루트 공통 파일은 수정하지 않는다.
실제 서비스가 준비되기 전에는 계약 기반 Mock으로 진행하며, 연결 뒤에는 Mock 여부와 실제 응답을 구별한다.
n8n check 뒤 push·test는 사람이 수행한다. PR 전 수정·스테이징 경로와 비밀값 포함 여부를 확인한다.
새 기능의 관련 회귀를 수행하고, 제출 문서에 필요한 실제 설계/측정/보고서를 자기 Doc/SUBMISSION-NOTES.md로 전달한다.

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [팀 헌장·역할](../../../docs/TEAM-CHARTER.md)
- [수업 방식과 연결 규칙](../../../docs/COORDINATION.md)
- 수업 원문: [02-ENVIRONMENT-AND-SERVICES.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/02-ENVIRONMENT-AND-SERVICES.md) · [04-REFERENCE-ARCHITECTURE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md)
