# 화면 작업

시작: [TODO](Doc/TODO.md) → [SPEC](Doc/SPEC.md) → [IMP-PLAN](Doc/IMP-PLAN.md). 담당자가 참고 초안을 자기 말로 고치고 백엔드와 계약을 맞춘 뒤 한 단계씩 구현한다.

- **작성:** 직원 로그인·질문·내 문의 화면과 IT팀 관리자 티켓 화면. 답변에는 근거, 보완 질문, 이관 상태를 구별해 표시한다.
- **규칙:** 모든 업무 데이터는 FastAPI `/api/*`에서 받는다. 브라우저가 DB·n8n·비밀키에 직접 접근하지 않는다. 세션의 직원 신원은 서버가 판단한다.
- **결과:** 직원 질문부터 답변/이관과 내 문의 조회, 관리자의 티켓 처리까지 시연 가능해야 한다.
- **계약:** [API 요청·응답 초안](../docs/API-CONTRACT.md). **강사 자료:** [C형 입구·뒷단 안내](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/11-TOPIC-GUIDE.md).

전체 완료 기준은 [폴더별 작업 안내](../docs/WORKSPACE-GUIDE.md)를 따른다.
