# 지식 검색 RAG · TODO

주 담당: **신유빈**. 지원 담당은 추가 배정.

> 상태: 팀 합의 내용을 옮긴 참고 초안. 담당자가 자기 말로 고치고 필수·나중을 구분한 뒤 SPEC을 작성한다. 체크는 구현 완료가 아니라 요구 이해·검토 완료 표시다.

## 먼저 이해할 일

- [ ] 제공 규정 문서의 절·권한 정보를 보존해 청킹·임베딩·색인한다.
- [ ] PostgreSQL+pgvector에 문서 청크·벡터를 저장하고 검색한다. 지혜님과 테이블·차원·권한·마이그레이션을 맞춘다.
- [ ] 직원의 권한으로 검색 전 문서를 제한하고 출처가 있는 근거를 반환한다.
- [ ] 청킹·검색 설정을 비교 측정해 답변 가능한 기준을 제안한다.
- [ ] 재색인·재시작 복구·실패 처리를 기록하고 RAG 설계서를 작성한다.

## 담당 경로 · 저장소 루트 기준

`yubeen/workflows/oke-index.json`과 `yubeen/workflows/oke-search.json`. 본체 JSON의 검색 연결 변경은 문의 담당이 한다.

## 담당자가 채울 것

- 내가 이해한 목적·사용자: 작성 필요
- 이번 일정에서 반드시 할 것 / 나중에 할 것: 작성 필요
- 의문·필요한 자료·다른 역할의 도움이 필요한 것: 작성 필요
- 요구 검토자·검토일: 미정

## 공통 자료

- [주제](../../docs/TOPIC.md) · [공통 API 계약](../../docs/API-CONTRACT.md) · [역할표](../../docs/ROLE-PLAN.md)
- [수업 방식과 연결 규칙](../../docs/DEVELOPMENT-FLOW.md)
- 수업 원문: [05-RAG-DESIGN-GUIDE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/05-RAG-DESIGN-GUIDE.md) · [04-REFERENCE-ARCHITECTURE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md) · [VIBE-Q-TDOC.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/71/VIBE-Q-TDOC.md)
