# 오케퐁 사내 IT 헬프데스크

직원 6명의 사내 IT 문의에 규정의 근거로 답하고, 필요한 경우 IT팀 티켓·알림으로 이관한다.
Next.js 화면 → FastAPI → n8n으로 연결한다. 업무 데이터는 PostgreSQL, 문서 임베딩은 pgvector에 저장한다. 계정은 관리자가 발급한다.

## 개발 시작

저장소 전체를 clone하고 [develop/README](develop/README.md)에서 자기 폴더로 이동한다.
개인 README → TODO → SPEC → IMP-PLAN 순서로 읽고 한 단계씩 구현·확인·커밋한다.
현재는 개발 준비 문서 단계다. 코드·워크플로우·실행 명령·시험 보고서는 담당자가 구현·확인한 뒤 추가한다.

## 공통 기준 · 항목마다 한 문서를 따른다

| 내용 | 기준 문서 |
| --- | --- |
| 주제·문의 범위·사용자 기능 | [TOPIC](docs/TOPIC.md) |
| 담당자·소유 파일·팀 규칙 | [TEAM-CHARTER](docs/TEAM-CHARTER.md) |
| API·하위 연결·서비스명·포트·환경변수 | [API-CONTRACT](docs/API-CONTRACT.md) |
| 데이터·DB·pgvector 구조 | [DATA-AND-DB](docs/DATA-AND-DB.md) |
| 개발·변경 협의·PR·통합 | [COORDINATION](docs/COORDINATION.md) |
| 코딩 에이전트 공통 규칙 | [AGENTS](AGENTS.md) |

각 담당자는 자기 폴더만 수정한다. 기준대로 개발할 때 사전 협의는 필요 없다. 변경할 때만 지정 상대와 검토하고 공통 문서는 오현님이 반영한다.
개인 결과물은 [오현님 제출 안내](develop/ohyun/SUBMISSION.md)에 따라 취합한다.

## 필수 제출 문서

- [워크플로우 설계서](docs/WORKFLOW-DESIGN.md)
- [RAG 설계서](docs/RAG-ARCHITECTURE.md)
- [실행 결과서](docs/EXECUTION-RESULT.md)

필수 3종은 작성 중인 문서이며 실제 구현·측정·시험 결과로 완성한다. 주제·헌장·데일리 3장·캡처·JSON·시나리오·시험 보고서도 제출한다.
세부 문서 위치는 [docs/README](docs/README.md)를 따른다.
