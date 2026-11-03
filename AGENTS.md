# 오케퐁 프로젝트 작업 규칙

이 파일은 팀의 CLI 코딩 에이전트 작업 규칙 초안이다. 팀이 역할과 API 계약을 확정하면 함께 갱신한다.

## 시작 전

1. `README.md`, `docs/TOPIC.md`, `docs/API-CONTRACT.md`, `docs/ROLE-PLAN.md`, `docs/WORKSPACE-GUIDE.md`를 읽는다.
2. 이번 요청의 담당 경로, 입력·출력, 완료 기준을 3~5줄로 정리한다.
3. 다른 담당 경로나 공통 계약을 바꿔야 하면 먼저 변경 이유와 영향을 알린다. 설계 문서와 코드를 함께 고친다.
4. `docs/DEVELOPMENT-FLOW.md`와 해당 역할 폴더의 `TODO.md`, `SPEC.md`, `IMP-PLAN.md`를 읽는다. 담당자가 지정한 단계만 구현하고 확인 전 통과 체크를 하지 않는다.

## 구현 경계

- `sueon/`는 FastAPI만 호출한다. 브라우저에서 DB, n8n 내부 주소, API 키에 직접 접근하지 않는다.
- `jihye/`는 로그인 세션으로 직원을 확인하고 Pydantic으로 입력·출력을 검증한다. 공개 회원가입을 만들지 않는다.
- `dahyeok/workflows/oke-support.json`은 공통 웹훅의 요청·응답 필드와 route 값을 유지한다. 시험용 문의 처리 본체를 복제하지 않는다.
- `yubeen/workflows/oke-index.json`은 규정의 청킹·임베딩·색인과 재색인을 담당한다. 문서 권한은 검색 전에 적용한다.
- `yubeen/workflows/oke-search.json`은 RAG 담당이 소유한다. 본체 담당은 이 파일을 복제하지 않고 합의한 검색 계약으로 호출한다.
- `wonmin/workflows/oke-handoff.json`은 안정성 담당이 소유하며 티켓·알림·DLQ를 처리한다. 백엔드의 저장 API와 계약을 맞춘다.
- `wonmin/workflows/oke-errors.json`은 Error Trigger 기반 마지막 오류 경로다. 예상 가능한 오류는 본체에서도 처리한다.
- 같은 워크플로우 JSON을 여러 사람이 동시에 수정하지 않는다.
- RAG 저장은 PostgreSQL+pgvector를 사용한다. In-Memory로 대체하지 않는다. RAG 담당과 백엔드 담당이 확장·청크/벡터 테이블·권한·마이그레이션을 함께 맞춘다.

## 보안과 데이터

- 키, 토큰, 비밀번호, 실제 연락처를 코드·JSON·문서·캡처·실행 보고서에 쓰지 않는다. `.env.example`에는 이름만 둔다.
- 테스트를 통과시키려고 `wonmin/cases/common.json`의 기대값을 바꾸지 않는다.
- 같은 `request_id`의 티켓은 한 건만 생성한다. 직원은 자기 문의만, IT팀 관리자는 관리자 기능만 사용한다.
- 제공된 직원 6명·규정 8종·FAQ 6종·기존 티켓 4건의 의미를 임의로 바꾸지 않는다.

## 확인과 보고

- 워크플로우 JSON은 수업 키트 `flow.py check`로 검사하고, 사람이 n8n에 push·test해 결과를 확인한다. 80일차 키트가 도착하기 전에는 실행했다고 쓰지 않는다.
- 코드를 바꾼 역할은 자기 기능의 정상·오류·권한 경계를 확인하고, 실제 실행 결과를 담당 문서에 남긴다.
- 변경 보고에는 수정 파일, 동작 차이, 확인 방법과 결과, 남은 문제를 적는다. 실패를 통과로 적지 않는다.
- 팀 VM 배포와 기본 브랜치 병합은 팀의 리드가 관리한다.

교사 원문: [CLI 코딩 에이전트 작업 규칙](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/09-AGENT-WORKING-RULES.md).
