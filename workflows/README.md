# n8n 워크플로우

- **작성:** `oke-support.json`(본체), `oke-index.json`(색인), `oke-search.json`(검색), `oke-handoff.json`(티켓·알림·DLQ), `oke-errors.json`(예상 밖 오류).
- **규칙:** 공통 웹훅 요청·응답과 `route` 값을 유지한다. 키는 Credential에 두고 JSON에 넣지 않는다. 같은 JSON은 한 명이 맡아 병합 충돌을 막는다.
- **결과:** `flow.py check`를 통과하고, 팀 VM에서 공통·팀 시나리오와 오류 처리를 실제 실행한다. 실행 기록은 `runs/`에 남긴다.
- **강사 자료:** [참조 워크플로우·공통 계약](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md), [RAG](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/05-RAG-DESIGN-GUIDE.md), [안정성·보안](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/06-RELIABILITY-AND-SECURITY.md).

## 역할별 개발 문서

| 담당 | TODO → SPEC → IMP-PLAN | 소유 JSON |
| --- | --- | --- |
| 문의 처리 | [TODO](Doc/support/TODO.md) · [SPEC](Doc/support/SPEC.md) · [계획](Doc/support/IMP-PLAN.md) | oke-support |
| RAG | [TODO](Doc/rag/TODO.md) · [SPEC](Doc/rag/SPEC.md) · [계획](Doc/rag/IMP-PLAN.md) | oke-index · oke-search |
| 안정성·시험 | [TODO](Doc/reliability/TODO.md) · [SPEC](Doc/reliability/SPEC.md) · [계획](Doc/reliability/IMP-PLAN.md) | oke-handoff · oke-errors |

JSON은 아직 구현되지 않았다. 담당자는 문서 초안부터 검토하고, 실제 결과물을 이 폴더 바로 아래에 추가한다. 검색·이관 호출의 정확한 페이로드는 관련 담당자가 [공통 계약](../docs/API-CONTRACT.md)에 먼저 적는다.
