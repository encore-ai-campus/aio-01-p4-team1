# 시연 요청

- **작성:** 발표에서 재현할 정상 답변·보완 질문·이관·장애 요청 JSON.
- **규칙:** 공통 웹훅 형식인 `request_id`, `user`, `question`을 지킨다. 동일 요청을 재시도할 때만 같은 `request_id`를 쓴다. 비밀값을 넣지 않는다.
- **결과:** README의 시연 순서대로 요청을 보내면 팀 VM에서 같은 흐름을 재현할 수 있어야 한다.
- **강사 자료:** [요청·응답 계약](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md), [발표 순서](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/08-SUBMISSION.md).
