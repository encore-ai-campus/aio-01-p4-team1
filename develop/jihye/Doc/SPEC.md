# 업무 API·DB·공통 실행 설정 · SPEC

> 운영 기준: 팀장 배포 기본안으로 바로 구현한다. 이 문서의 기존 "합의·협의" 항목은 기준 적용 여부 확인이며, 기본안을 바꿀 때만 상대와 협의한다. 기준은 저장소 루트 docs/API-CONTRACT.md와 docs/DATA-AND-DB.md를 따른다.
작업 기준: [내 작업·협의 안내](../README.md) · [내 협의 기록](HANDOFF.md). 공통 파일과 상대 폴더는 직접 고치지 않고 소유자에게 요청한다.

주 담당: **지혜님**. 지원 담당은 추가 배정.

> 상태: 검토용 요구 초안. 아래 확인 기준을 담당자가 실제 입력·출력·오류 예시와 확인 방법으로 구체화한다. 테스트 통과 기록은 아니다.

## 요구와 확인 기준

| ID | 요구 | 기대 결과·확인할 것 |
| --- | --- | --- |
| BE-01 | 로그인·계정 관리 | 공개 회원가입 없음. 관리자 계정 발급, 첫 비밀번호 변경, 로그아웃·계정 비활성화·초기화 처리. 직원의 관리자 기능 접근은 403. |
| BE-02 | 문의 어댑터 | /api/ask의 user는 로그인 세션에서 결정. n8n 공통 필드로 호출하고 route·sources·ticket을 보존. 시간 초과 응답 정의. |
| BE-03 | 권한·저장 | 본인 문의만 조회. 직원의 다른 사용자 request_id 재사용으로 타인 결과가 반환되지 않음. 서비스 재시작 뒤 기록 유지. |
| BE-04 | 티켓·알림 어댑터 | /tickets·/alerts는 수업 data-api와 호환되는 계약과 내부 인증 사용. 동일 key의 티켓 생성은 한 건, 재시도는 같은 ticket 반환. |
| BE-05 | 초기화·실행 | 마이그레이션·초기 관리자 생성·서비스 실행 절차 작성. 비밀번호 원문과 실제 .env 미커밋. 새 환경에서 절차 재현. |
| BE-06 | RAG 저장 기반 | PostgreSQL에 pgvector를 준비하고 유빈님과 청크·벡터 테이블·메타데이터·권한·차원을 합의. 업무 테이블과 분리하고 재시작 뒤 데이터 유지 확인. |

## 구현 전에 담당자가 정할 것

- [ ] 세션 만료·비밀번호 규칙·쿠키 설정 및 오류 JSON
- [ ] 공개 API와 n8n 내부 API의 정확한 스키마·HTTP 상태·인증 방식
- [ ] 관리자 계정 비활성화·초기화·알림 조회 API를 API-CONTRACT에 보완
- [ ] 테이블·외래키·고유키·마이그레이션 도구, inquiry와 ticket의 연결
- [ ] 서비스 포트·Compose 서비스명·실행 위치를 리드와 합의

## 각 요구에 추가할 실행 예시

- 요구 ID / 필수·나중:
- 입력·사전 조건:
- 예상 HTTP 상태·출력 JSON 또는 화면 상태:
- 실패·권한·경계 사례:
- 확인 명령·시나리오 ID:
- 연결 담당자와 합의한 날짜:

공통 계약과 중복되는 스키마는 [API-CONTRACT.md](../../../docs/API-CONTRACT.md)를 참조한다. 바꿀 내용은 내 HANDOFF에 제안한다. 오현님이 공통 문서를 반영한 뒤 각 담당자는 자기 SPEC만 갱신한다. 기준을 바꾸지 않고 구현을 고쳐야 하는 실패와, 요구 변경을 구분한다.

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [팀 헌장·역할](../../../docs/TEAM-CHARTER.md)
- [수업 방식과 연결 규칙](../../../docs/COORDINATION.md)
- 수업 원문: [02-ENVIRONMENT-AND-SERVICES.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/02-ENVIRONMENT-AND-SERVICES.md) · [04-REFERENCE-ARCHITECTURE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md)
