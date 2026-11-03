# 오케퐁 사내 IT 헬프데스크

직원 문의를 받아 규정 문서의 근거로 답하고, 필요한 경우 IT팀에 티켓으로 이관하는 팀 프로젝트다.

## 처음 볼 순서

1. [주제·범위](docs/TOPIC.md): 우리가 해결할 문제와 기능 범위
2. [폴더별 작업 안내](docs/WORKSPACE-GUIDE.md): 각 폴더에서 작성할 내용·규칙·결과물·강사님 자료
3. [역할별 작업표](docs/ROLE-PLAN.md): 역할마다 맡는 파일과 완료 기준
4. [API 계약 초안](docs/API-CONTRACT.md): 화면·서버·n8n 사이에 주고받을 값
5. [역할별 개발 순서](docs/DEVELOPMENT-FLOW.md): 자기 TODO → SPEC → IMP-PLAN 작성과 단계별 개발

## 폴더 안내 · 작업을 이해할 때 보는 순서

| 순서 | 폴더 | 쉽게 말하면 | 여기서 나와야 할 것 | 구분 |
| --- | --- | --- | --- | --- |
| 1 | [`docs/`](docs/README.md) | 프로젝트 설명서와 제출 문서 | 주제·팀 규칙, 설계서 2종, 실행 결과서, 일일 기록 | 수업 필수 + 팀 기획 |
| 2 | [`workflows/`](workflows/README.md) | n8n에서 문의를 처리하는 자동화 | 문의 본체·색인·검색·이관·오류 처리 JSON 5개 | 팀의 역할별 분리안 |
| 3 | [`backend/`](backend/README.md) | 화면과 자동화 사이의 서버 | FastAPI 로그인·권한·문의·티켓 API, PostgreSQL 저장 | 우리 팀 C형 선택 |
| 4 | [`frontend/`](frontend/README.md) | 직원과 IT팀이 보는 웹 화면 | 로그인, 질문, 내 문의, 관리자 티켓 화면 | 우리 팀 C형 선택 |
| 5 | [`cases/`](cases/README.md) | 시험 문제지 | 우리 팀 질문·예상 결과 5개 이상 | 수업 필수 |
| 6 | [`requests/`](requests/README.md) | 시연 때 보낼 질문 예시 | 발표 순서에 맞춘 요청 JSON | 시연 준비 |
| 7 | [`runs/`](runs/README.md) | 시험 성적표의 원본 | 실제 시험·반복·장애·속도 보고서 | 수업 필수 |
| 8 | [`deploy/`](deploy/README.md) | 팀 VM 실행 방법과 설정 | 화면·서버·DB 실행 설정과 재현 절차 | 우리 팀 C형 선택 |

큰 흐름: **직원 화면 → FastAPI → n8n 문의 처리 → FastAPI·DB에 티켓 저장 → 직원 화면에 결과 표시**. 규정 검색은 n8n의 RAG가 하고, 시험은 `cases/`의 질문을 실행해 `runs/`에 결과를 남긴다.

GitHub의 실제 파일 목록은 이름순으로 표시돼 `docs/`를 물리적으로 맨 위로 옮길 수는 없다. 강사님 제출 경로가 `docs/`로 정해져 있어 폴더 이름은 유지하고, 이 안내에서 먼저 보이게 했다.

현재는 기획·폴더 구조를 준비한 상태다. 구현·시험 결과는 아직 없다.

팀장·통합: **오현**. 사람별 담당 범위는 [역할표](docs/ROLE-PLAN.md)를 따른다.

## 담당자가 작성할 개발 문서

각 위치에 `TODO.md`(목적·할 일), `SPEC.md`(통과 기준), `IMP-PLAN.md`(단계·파일·확인 방법) 세 파일이 있다. 현재 내용은 참고 초안이며 담당자가 자기 말로 수정·구체화한다.

| 역할 | 개발 문서 위치 | 구현 경로 |
| --- | --- | --- |
| 화면 · 이수언 | [frontend/Doc](frontend/Doc/TODO.md) | frontend/ |
| 업무 API·DB · 박지혜 | [backend/Doc](backend/Doc/TODO.md) | backend/ · deploy/ |
| 문의 처리 · 임다혁 | [workflows/Doc/support](workflows/Doc/support/TODO.md) | oke-support.json |
| RAG · 신유빈 | [workflows/Doc/rag](workflows/Doc/rag/TODO.md) | oke-index.json · oke-search.json |
| 안정성·시험 · 이원민 | [workflows/Doc/reliability](workflows/Doc/reliability/TODO.md) | oke-handoff.json · oke-errors.json · cases/ · requests/ · runs/ |

워크플로우 JSON·실행 코드·시험 보고서는 담당자가 구현한 뒤 추가한다. 빈 JSON을 완성 파일처럼 넣지 않는다. 필수 제출 문서 3종은 강사 템플릿으로 준비했으며 실제 설계·측정·실행 결과로 채워야 한다.

```text
docs/                        공통 기획·계약·제출 문서
frontend/Doc/                화면 담당 TODO·SPEC·IMP-PLAN
backend/Doc/                 백엔드 담당 TODO·SPEC·IMP-PLAN
backend/migrations/          DB 변경 이력 (구현 예정)
workflows/Doc/support/       문의 담당 TODO·SPEC·IMP-PLAN
workflows/Doc/rag/           RAG 담당 TODO·SPEC·IMP-PLAN
workflows/Doc/reliability/   안정성·시험 담당 TODO·SPEC·IMP-PLAN
workflows/oke-*.json         역할별 5개 결과물 (구현 예정)
cases/                      시험 시나리오 (작성 예정)
requests/                   시연 요청 (작성 예정)
runs/                       실제 시험 보고서 (실행 후 생성)
deploy/                     백엔드 담당이 실행 설정 작성, 리드가 VM 배포
```

## 제출 전 갖출 파일

- `AGENTS.md`, `docs/TOPIC.md`, `docs/TEAM-CHARTER.md`
- `docs/WORKFLOW-DESIGN.md`, `docs/RAG-ARCHITECTURE.md`, `docs/EXECUTION-RESULT.md`
- `docs/daily/DAY80.md`, `DAY81.md`, `DAY82.md`
- `workflows/`의 n8n JSON, `cases/team.json`, `runs/`의 시험 보고서

기본 주제의 규정·직원·기존 티켓과 공통 시나리오는 수업 키트를 사용한다. 비밀값은 저장소에 올리지 않는다.
