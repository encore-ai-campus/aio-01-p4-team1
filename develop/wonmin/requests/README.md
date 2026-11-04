# 시연 요청

- **작성:** 발표에서 재현할 정상 답변·보완 질문·이관·장애 요청 JSON.
- **규칙:** 공통 웹훅 형식인 `request_id`, `user`, `question`을 지킨다. 동일 요청을 재시도할 때만 같은 `request_id`를 쓴다. 비밀값을 넣지 않는다.
- **결과:** README의 시연 순서대로 요청을 보내면 팀 VM에서 같은 흐름을 재현할 수 있어야 한다.
- **기준 문서:** [공통 API 계약](../../../docs/API-CONTRACT.md), [시나리오·평가 가이드](../../../docs/EVALUATION-GUIDE.md), [제출 안내](../../ohyun/SUBMISSION.md).
