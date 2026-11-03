# n8n 역할·개발 경로

| 담당 | 개발 원본 파일 (구현 예정) | 역할 |
| --- | --- | --- |
| 임다혁 | dahyeok/workflows/oke-support.json | 입력·권한·분류·답변·검증·분기·루프 |
| 신유빈 | yubeen/workflows/oke-index.json | 원본 문서 청킹·임베딩·색인 |
| 신유빈 | yubeen/workflows/oke-search.json | 권한별 검색·근거 목록 반환 |
| 이원민 | wonmin/workflows/oke-handoff.json | 티켓·알림·DLQ·재시도·중복 |
| 이원민 | wonmin/workflows/oke-errors.json | Error Trigger 기반 예상 밖 오류 |

각자의 이름 폴더/Doc에서 TODO→SPEC→IMP-PLAN을 작성한다. 공통 웹훅 계약과 route를 유지하고, 내부 연결은 [API 계약](API-CONTRACT.md)에 먼저 맞춘다.
웹과 공통 시험 도구는 같은 support를 호출한다. 파일 위치 변경은 웹훅 이름 변경을 뜻하지 않는다.
JSON에는 비밀값을 넣지 않고 n8n Credential을 쓴다. 에이전트는 check, 사람이 push·test를 수행한다.
현재 JSON은 미구현이다. 제출 직전 [취합 안내](../hyun/SUBMISSION.md)에 따라 루트 workflows/에 사본을 모으며 개발 수정은 개인 원본에서 한다.

수업 원문: [참조 구조 5절](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md).
