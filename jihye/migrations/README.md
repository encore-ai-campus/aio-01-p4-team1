# PostgreSQL 스키마 변경

- **작성:** 계정·세션·문의·티켓·알림 테이블의 생성·변경 이력을 순서대로 기록한다.
- **규칙:** 기본키·외래키·`request_id` 고유 제약을 DB에 둔다. 비밀번호 원문·실제 비밀값을 넣지 않는다. 스키마 변경은 API 모델과 함께 맞춘다.
- **결과:** 새 환경에서 스키마 생성 후 API가 실행되고, 재시작 뒤 문의·티켓이 유지되어야 한다.
- **참고:** [팀 API 계약](../../docs/API-CONTRACT.md), [전체 아키텍처 수업자료](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/tree/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project).
