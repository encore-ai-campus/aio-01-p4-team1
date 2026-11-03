# 유빈님 · 구현 계획

담당 범위·변경 검토 상대·결과물은 [내 README](../README.md), 통과 요구는 [SPEC](SPEC.md)을 따른다.
공통 기준대로 구현하며 변경할 때만 [HANDOFF](HANDOFF.md)에 요청한다. 모든 단계는 아직 미실행이다.
각 단계는 확인 가능한 작은 PR로 나누고 실제 결과를 아래에 기록한다.

## P0

- [ ] 작업: 공통 계약을 적용하고 제공 규정/관리자 문서 목록과 권한을 확인한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: DB 확장/테이블·차원·검색 계약을 확인. 자료 조사·청킹 후보 비교는 먼저 가능
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## P1-1

- [ ] 작업: 청킹·임베딩·pgvector 저장·갱신을 index에 구현한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: 청크 수·메타데이터·동일 문서 재색인 중복 제어
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## P1-2

- [ ] 작업: 권한을 검색 전에 적용하는 search를 구현하고 실제 질문으로 top_k·점수 기준을 비교한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: 일반 직원에게 IT 문서가 검색/LLM 입력으로 들어가지 않음
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## P1-3

- [ ] 작업: 본체 연결과 DB 재시작 유지·원본 재색인·복구를 확인한다.
- [ ] 관련 SPEC 요구 ID·생성/수정 파일: 구현 전에 자기 폴더 기준으로 기록
- [ ] 확인 명령·입력·사전 조건: 구현 시 기록
- [ ] 완료 기준: 실제 비교 수치·복구 근거를 햄에게 전달
- [ ] 실제 확인 결과·남은 문제·커밋/PR: 실행 후 기록

## 단계 운영

구현 → 자기 기능 확인 → 결과 기록 → 작은 PR 순서다. 다른 담당자 소스·루트 공통 파일은 수정하지 않는다.
실제 서비스가 준비되기 전에는 계약 기반 Mock으로 진행하며, 연결 뒤에는 Mock 여부와 실제 응답을 구별한다.
n8n check 뒤 push·test는 사람이 수행한다. PR 전 수정·스테이징 경로와 비밀값 포함 여부를 확인한다.
새 기능의 관련 회귀를 수행하고, 제출 문서에 필요한 실제 설계/측정/보고서를 자기 Doc/SUBMISSION-NOTES.md로 전달한다.

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [팀 헌장·역할](../../../docs/TEAM-CHARTER.md)
- [수업 방식과 연결 규칙](../../../docs/COORDINATION.md)
- 수업 원문: [05-RAG-DESIGN-GUIDE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/05-RAG-DESIGN-GUIDE.md) · [04-REFERENCE-ARCHITECTURE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md) · [VIBE-Q-TDOC.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/71/VIBE-Q-TDOC.md)
