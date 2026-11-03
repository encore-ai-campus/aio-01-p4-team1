# FastAPI 작업

시작: [TODO](Doc/TODO.md) → [SPEC](Doc/SPEC.md) → [IMP-PLAN](Doc/IMP-PLAN.md). 담당자가 초안을 구체화하고 화면·안정성 담당과 계약을 맞춘다. `deploy/`의 실행 설정도 이 계획에 포함하며 실제 VM 배포는 리드가 한다.

- **작성:** 로그인·권한 확인, 관리자 계정 발급, 문의·티켓·알림 API, n8n 호출 및 오류 처리. 데이터 구조는 Pydantic 요청·응답 모델로 고정한다.
- **규칙:** 공개 회원가입은 없다. 직원의 신원과 권한을 서버에서 확인한다. 티켓 생성은 `request_id`로 중복 방지하고 비밀번호는 해시만 저장한다.
- **결과:** 화면 없이 API만으로 로그인, 본인 조회, 관리자 제한, 문의 처리, 티켓 저장을 검증할 수 있어야 한다.
- **계약:** [API 요청·응답 초안](../docs/API-CONTRACT.md). **강사 자료:** [C형 FastAPI 어댑터](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/02-ENVIRONMENT-AND-SERVICES.md).

DB 변경 파일은 [`migrations/`](migrations/)에 둔다. 전체 완료 기준은 [폴더별 작업 안내](../docs/WORKSPACE-GUIDE.md)를 따른다.
