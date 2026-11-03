# 오케퐁 역할별 작업표

> 상태: 사람 배정 전. 한 역할에 한 사람을 반드시 고정한다는 뜻은 아니다. 각 역할에 주 담당과 지원 담당을 배정한다.

| 역할 | 담당 범위 | 주 소유 경로 | 완료 기준 |
| --- | --- | --- | --- |
| 기획·통합 | 범위·계약 관리, PR 병합, 팀 VM 배포, 발표·문서 취합 | `README.md`, `docs/TOPIC.md`, `docs/TEAM-CHARTER.md`, `docs/daily/` | 기본 브랜치와 VM이 일치하고 배포 후 공통 시나리오 결과를 기록 |
| 직원·관리자 화면 | 로그인, 질문, 답·근거, 내 문의, 관리자 티켓·알림 화면과 API 연결 | `frontend/` | 직원과 관리자가 FastAPI만 호출해 주요 흐름을 끝까지 시연 |
| 업무 API·DB | Pydantic 계약, 로그인·세션·권한, 계정 생성, 문의·티켓·알림·상태 저장, 중복 방지, 공통 실행 설정 | `backend/`, `backend/migrations/`, `deploy/` | 화면·n8n API와 인증 API가 계약대로 응답하고 재시작 뒤 기록이 유지 |
| 문의 처리 자동화 | 웹훅 입력 검사, 분류, 보완 질문, 답변·검증, 자동 답변·이관 분기 | `workflows/oke-support.json` | 공통 요청·응답 형식을 지키고 정상·정보 부족·근거 없음 경로가 동작 |
| 지식 검색(RAG) | 문서 청킹·임베딩·색인, 권한별 검색, 출처·점수 측정 | `workflows/oke-index.json`, `workflows/oke-search.json` | 규정 8종의 색인·재색인과 권한별 근거 검색을 실제 결과로 확인 |
| 안정성·시험 | 티켓 연동, Error Workflow, 재시도·DLQ·알림·중복·보안 시험, 팀 시나리오와 결과 기록 | `workflows/oke-handoff.json`, `workflows/oke-errors.json`, `cases/`, `requests/`, `runs/` | 공통 14유형·팀 5개 이상, LLM 3회 반복과 실패 후 재시험 기록 |

## 역할 사이의 연결

1. 기획·통합과 각 담당은 [API 계약](API-CONTRACT.md)의 요청·응답을 먼저 확인한다.
2. 화면은 FastAPI를, FastAPI는 같은 `oke-support` 웹훅을 호출한다. 공통 시험 도구도 이 웹훅을 직접 호출한다.
3. 문의 처리 자동화는 RAG 검색 결과와 티켓·알림 API의 형식에 맞춰 연결한다. 같은 워크플로우 파일은 동시에 수정하지 않는다.
4. 설계서와 결과서는 각 역할이 자기 부분의 실제 노드·설정·시험 결과를 제공하고 기획·통합이 취합한다.

## 문서 책임

| 문서 | 내용을 제공할 역할 |
| --- | --- |
| `docs/WORKFLOW-DESIGN.md` | 문의 처리 자동화, 업무 API·DB, 안정성·시험 |
| `docs/RAG-ARCHITECTURE.md` | 지식 검색(RAG) |
| `docs/EXECUTION-RESULT.md` | 안정성·시험, 각 기능 담당의 실행 결과 |

사람별 배정·파일 경계·완료 시각은 팀원 희망을 확인한 뒤 팀 헌장에 확정한다.

## 역할별 개발 문서

화면은 `frontend/Doc/`, 백엔드는 `backend/Doc/`, 문의·RAG·안정성은 `workflows/Doc/support/`·`rag/`·`reliability/`의 세 문서를 직접 검토·작성한다. [개발 순서](DEVELOPMENT-FLOW.md)의 문서 링크와 단계별 연결 기준을 따른다.

`oke-search`와 `oke-handoff`를 추가로 분리해 한 JSON의 공동 수정을 줄인다. 구체적인 내부 코드 경로는 담당자가 IMP-PLAN에 적는다. 배포 설정 작성은 백엔드 담당, 실제 팀 VM 배포는 리드가 맡는다.
