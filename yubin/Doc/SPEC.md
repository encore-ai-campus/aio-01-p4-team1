# 지식 검색 RAG · SPEC

주 담당: **신유빈**. 지원 담당은 추가 배정.

> 상태: 검토용 요구 초안. 아래 확인 기준을 담당자가 실제 입력·출력·오류 예시와 확인 방법으로 구체화한다. 테스트 통과 기록은 아니다.

## 요구와 확인 기준

| ID | 요구 | 기대 결과·확인할 것 |
| --- | --- | --- |
| RAG-01 | 색인 | 규정 8종과 키트 관리자 전용 문서 제공 여부를 확인. doc·section·access_level·청크 식별 메타데이터와 청크 수·길이 분포 기록. |
| RAG-02 | 권한 | IT팀 전용 문서는 검색 전에 제한. 접근 권한이 없는 청크가 LLM 입력에 들어가지 않음. |
| RAG-03 | 검색 응답 | 본체와 합의한 evidence의 doc·section·text·score 반환. 검색 결과 없음은 빈 목록, 장애는 구별 가능한 실패 결과. |
| RAG-04 | 비교·복구 | 청킹·top_k·점수 의미를 실제 질문으로 비교. 색인 재실행 중복과 In-Memory 재시작 후 복구 확인. 측정 전 수치 확정 금지. |

## 구현 전에 담당자가 정할 것

- [ ] 문서 실제 목록·관리자 문서·문서 버전 확인
- [ ] 청킹 방식·길이·겹침·임베딩 설정·top_k·거리/점수의 의미
- [ ] 검색 임계값은 측정 후 제안하고 문의 담당과 합의
- [ ] index/search의 저장소 ID·권한별 키와 n8n 실행 방식의 호환성 확인

## 각 요구에 추가할 실행 예시

- 요구 ID / 필수·나중:
- 입력·사전 조건:
- 예상 HTTP 상태·출력 JSON 또는 화면 상태:
- 실패·권한·경계 사례:
- 확인 명령·시나리오 ID:
- 연결 담당자와 합의한 날짜:

공통 계약과 중복되는 스키마는 [API-CONTRACT.md](../../docs/API-CONTRACT.md)를 참조한다. 바꾸면 해당 문서와 연결된 담당자 SPEC도 함께 갱신한다. 기준을 바꾸지 않고 구현을 고쳐야 하는 실패와, 요구 변경을 구분한다.

## 공통 자료

- [주제](../../docs/TOPIC.md) · [공통 API 계약](../../docs/API-CONTRACT.md) · [역할표](../../docs/ROLE-PLAN.md)
- [수업 방식과 연결 규칙](../../docs/DEVELOPMENT-FLOW.md)
- 수업 원문: [05-RAG-DESIGN-GUIDE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/05-RAG-DESIGN-GUIDE.md) · [04-REFERENCE-ARCHITECTURE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md) · [VIBE-Q-TDOC.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/71/VIBE-Q-TDOC.md)
