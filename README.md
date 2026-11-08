# 오케퐁 · 사내 IT 헬프데스크

직원이 질문하면 사내 규정 근거로 안내하고, 자동 답변이 어려운 문의는 IT팀 티켓으로 접수해 처리 결과까지 확인하는 서비스다.

이 `main`은 루트 표준 경로에 코드·데이터·배포·평가 자산을 갖춘 독립 제출본이다. 다른 브랜치나 별도 강의 저장소에서 파일을 가져올 필요가 없다. 실행에는 Docker와 비공개 환경 설정이 필요하며, 실제 LLM·임베딩 호출에는 설정한 OpenAI API를 사용한다.

| 경로 | 내용 |
| --- | --- |
| [frontend/](frontend/README.md) | Next.js 직원·관리자 웹 화면 |
| [backend/](backend/README.md) | FastAPI 인증·업무 API, DB 마이그레이션·검사 |
| [rag/](rag/README.md) | 색인·검색 HTTP 서비스, 권한 매핑·설정 |
| [data-api/](data-api/server.py), [data/](data/README.md) | 제공 API와 가상 초기 데이터·스키마 |
| [knowledge/](knowledge/README.md), [prompts/](prompts/README.md) | 규정 8종과 프롬프트 3종 |
| [workflows/](workflows/README.md) | n8n 워크플로우 5종 |
| [cases/](cases/README.md), [requests/](requests/README.md), [eval/](eval/README.md) | 시나리오·요청·오프라인 평가 |
| [runs/](runs/README.md) | 기존 시험·측정 영수증 |
| [deploy/](deploy/README.md) | VM Compose와 격리 로컬 환경 |
| [docs/](docs/README.md), [daily/](daily/README.md) | 계약·설계·실행 결과·일일 기록 |

로컬 실행은 [deploy/LOCAL-MAC.md](deploy/LOCAL-MAC.md), VM 설정은 [deploy/README.md](deploy/README.md), 제출·정적 검증은 [SUBMISSION.md](SUBMISSION.md)를 따른다. 폴더 정규화는 VM 배포나 실제 서비스 재시험 완료를 뜻하지 않는다.

필수 설계·결과 문서: [워크플로우 설계](docs/WORKFLOW-DESIGN.md) · [RAG 설계](docs/RAG-ARCHITECTURE.md) · [실행 결과](docs/EXECUTION-RESULT.md).

웹 화면 → FastAPI의 신원·권한·저장 → 같은 n8n 문의 본체 → RAG 답변 또는 IT팀 이관 → 관리자 처리 → 직원 재조회 흐름이다. 공개 회원가입은 없으며 관리자가 계정을 발급한다. 제공 직원 6명·규정 8종·FAQ 6종·기존 티켓 4건의 의미를 유지한다.

기존 결과와 미완료·제약은 실행 결과서에 기록돼 있다. 개발 당시 경로가 나오는 과거 일일 기록·영수증은 당시 실행 이력이며 현재 실행 경로는 위 표를 따른다.
