# 팀 VM 배포

작성 담당: 업무 API·DB. [백엔드 구현 계획](../Doc/IMP-PLAN.md)에 실행 환경 준비를 포함한다. 리드는 기본 브랜치의 설정으로 팀 VM에 배포·회귀 시험한다.

- **작성:** Next.js·FastAPI·PostgreSQL 실행 설정, 환경변수 이름, DB 초기화·재시작 절차. n8n·data-api와 연결할 서비스 주소를 명시한다.
- **규칙:** 실제 `.env`, 관리자 초기 비밀번호, 팀 VM 주소·토큰을 커밋하지 않는다. 볼륨을 지우는 명령을 기본 절차에 넣지 않는다.
- **결과:** 팀 VM에서 README대로 시작하고 `flow.py doctor` 확인 후 웹 시연·공통 시험을 다시 할 수 있어야 한다.
- **강사 자료:** [환경·팀 VM](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/02-ENVIRONMENT-AND-SERVICES.md), [제출·시연](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/08-SUBMISSION.md).
