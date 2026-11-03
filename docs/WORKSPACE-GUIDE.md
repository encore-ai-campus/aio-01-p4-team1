# 오케퐁 저장소 작업 안내

> 상태: 개발 시작 전 작업 지침. 아래의 “나와야 할 결과”는 완료 주장이나 빈 파일 생성 지시가 아니다. 실제 구현·시험 후 파일을 채운다.

선생님 저장소 [해당 커밋의 프로젝트 자료 전체](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/tree/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project)를 기준으로 했다. 이 커밋은 로컬 수업 저장소 HEAD와 일치한다. GitLab 페이지 내용은 이 문서의 연결을 따라 확인하고, 실제 80일차 실습 키트가 배포되면 명령·시나리오 파일을 다시 확인한다.

## 1. 공통 작업 순서

1. [주제·범위](TOPIC.md), [API 계약](API-CONTRACT.md), [역할표](ROLE-PLAN.md)를 먼저 읽는다.
   [역할별 개발 순서](DEVELOPMENT-FLOW.md)의 링크로 자기 TODO·SPEC·IMP-PLAN을 열어 참고 초안을 검토·구체화한다.
2. 한 작업에 담당 경로·입력·출력·통과시킬 시나리오를 적는다. 파일 소유자가 겹치면 먼저 나눈다.
3. 설계 표를 고친 뒤 구현하고, 자기 영역을 실행·확인한다. `workflows/`를 바꾼 뒤에는 `flow.py check → push → test` 순서로 확인한다.
4. PR에는 실제 확인 결과와 관련 문서의 변경을 함께 넣는다. 리드가 병합·팀 VM 배포 후 공통 시나리오를 다시 돌린다.
5. 81일차 8교시에 기능을 동결하고 82일차에는 시험·수정·문서·발표에 집중한다.

근거: [일정과 팀 역할](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/01-SCHEDULE-AND-TEAMS.md), [CLI 작업 규칙](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/09-AGENT-WORKING-RULES.md).

## 2. 폴더별 작성 내용·규칙·결과물

### `frontend/` · 직원·관리자 화면

- **작성:** Next.js 로그인, 질문하기(`/ask`), 내 문의, 관리자 티켓 화면. 답·근거·보완 질문·이관·로딩·오류 상태를 표시한다.
- **규칙:** FastAPI `/api/*`만 호출한다. DB·n8n·비밀키에 브라우저에서 직접 접근하지 않는다. 화면이 보낸 직원 이름으로 권한을 결정하지 않는다.
- **나와야 할 결과:** 로그인한 직원의 질문→답변/티켓→내 문의 확인, IT팀 관리자의 티켓 조회·답변·상태 변경을 화면에서 시연한다. 자동화 판단은 n8n 결과를 사용한다.
- **참고:** [C형 구성·화면 예시(전체 아키텍처 PDF 18~19쪽)](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/%EA%B8%B0%EC%88%A0%EC%A7%80%EC%9B%90%EC%9E%90%EB%8F%99%ED%99%94_%EC%A0%84%EC%B2%B4%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98.pdf), [입구·뒷단 조합](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/11-TOPIC-GUIDE.md).

### `backend/` · FastAPI와 업무 규칙

- **작성:** Pydantic 요청·응답 모델, 로그인·로그아웃·비밀번호 변경, 관리자 직원 계정 생성, `/api/ask`, 내 문의·관리자 티켓 조회·변경, n8n이 호출할 `/tickets`·`/alerts`.
- **규칙:** 공개 회원가입 없음. 관리자만 제공 직원의 계정을 만든다. 로그인한 신원으로 본인·IT팀 권한을 서버에서 검사한다. n8n 호출 시간 제한과 실패 응답을 둔다. 비밀번호 원문과 키는 저장·출력하지 않는다.
- **나와야 할 결과:** 화면 없이 API만 호출해 로그인, 본인 조회, 관리자 제한, 티켓 생성·중복 방지, 상태 변경을 확인할 수 있다.
- **참고:** [C형 어댑터·인증](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/02-ENVIRONMENT-AND-SERVICES.md), [공통 페이로드](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md).

### `backend/migrations/` · PostgreSQL 변경 이력

- **작성:** 계정·세션·문의·티켓·알림 테이블의 스키마 변경. 필요하면 담당자·상태 변경 이력.
- **규칙:** 기본키·외래키·중복 방지 `request_id` 고유 제약을 DB에 둔다. 비밀번호는 해시만 저장한다. 동일 마이그레이션을 팀 VM에서 반복 실행해도 상태가 예측 가능해야 한다.
- **나와야 할 결과:** 새 환경에서 스키마 생성과 API 실행, 서비스 재시작 뒤 문의·티켓 유지. 실제 마이그레이션 도구·파일명은 백엔드 담당이 정한다.

### `workflows/` · 역할별 n8n JSON 다섯 종류

| 파일 | 작성 내용 | 완료 결과 | 참고 |
| --- | --- | --- | --- |
| `oke-support.json` | Webhook → 입력·권한 검사 → 분류 → RAG 검색 → 답변·검증 → 자동 답변/보완 질문/이관 → 공통 응답 | 공통 웹훅 계약과 정상·예외 분기를 시나리오로 확인 | [참조 구조·페이로드](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md) |
| `oke-index.json` | 규정 `/docs` 가져오기 → 청킹 → 임베딩 → 권한 메타데이터와 함께 색인 | 규정 8종의 색인·재색인, 청크 수·길이 분포 기록 | [RAG 설계 가이드](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/05-RAG-DESIGN-GUIDE.md), [71일차 실습](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/tree/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/71) |
| `oke-search.json` | 권한별 검색·근거 목록·검색 실패 결과 반환 | 문의 본체가 공통 검색 계약으로 호출 | [하위 워크플로우 분리](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md) |
| `oke-handoff.json` | 티켓·알림·DLQ·재시도·중복 처리 | 본체에 티켓 또는 구별 가능한 실패 결과 반환 | [안정성·보안](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/06-RELIABILITY-AND-SECURITY.md) |
| `oke-errors.json` | Error Trigger → 알림·DLQ·개인정보 제거 | 예상하지 못한 오류를 실제로 일으켜 알림·DLQ 기록 확인 | [안정성·보안](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/06-RELIABILITY-AND-SECURITY.md), [76일차 실습](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/tree/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/76) |

**공통 규칙:** JSON에 키를 넣지 않고 n8n Credential을 쓴다. 같은 `oke-support`를 공통 시험 도구와 FastAPI가 호출한다. RAG는 index·search, 안정성은 handoff·errors, 문의 담당은 support를 맡는다. 역할별 세 문서는 `workflows/Doc/` 아래 support·rag·reliability에 둔다. 예제 JSON을 가져오면 원본과 바꾼 부분을 설계서에 적는다. 현재 JSON은 미구현이다.

### `docs/` · 기획과 제출 문서

| 파일 | 채울 내용 | 완료 기준 | 선생님 자료 |
| --- | --- | --- | --- |
| `TOPIC.md` | 회사·사용자·기술지원 범위, 5가지 주제 조건, 조합·데이터·이관 기준 | 80일차 강사 승인 내용 반영 | [주제 가이드](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/11-TOPIC-GUIDE.md), [주제 템플릿](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/templates/TOPIC-PROPOSAL-TEMPLATE.md) |
| `TEAM-CHARTER.md` | 목표 한 문장, 사람별 주·지원 역할, 파일 소유권, 회의·PR·막힘 공유 규칙 | 팀 합의 후 작성 | [팀 헌장 템플릿](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/templates/TEAM-CHARTER-TEMPLATE.md) |
| `API-CONTRACT.md` | 화면↔FastAPI↔n8n, n8n↔티켓·알림 요청·응답·권한·오류 | 실제 API 모델·워크플로우 페이로드와 일치 | [참조 구조 3절](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md) |
| `ROLE-PLAN.md` | 역할별 소유 파일·완료 기준, 확정 전후 구분 | 팀원 배정 뒤 헌장과 일치 | [일정·역할 4절](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/01-SCHEDULE-AND-TEAMS.md) |
| `WORKFLOW-DESIGN.md` | 업무·흐름도, 역할 카드, 분기·병렬·루프, 노드 인증·오류, **연결선별** 페이로드 | 실제 n8n JSON과 노드·값이 일치 | [설계서 템플릿](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/templates/WORKFLOW-DESIGN-TEMPLATE.md) |
| `RAG-ARCHITECTURE.md` | 원본 문서, 청킹 비교·길이 분포, 임베딩·차원·거리, 권한 메타데이터, 재색인·복구·확장 | 예시 수치를 실제 측정값으로 교체 | [RAG 템플릿](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/templates/RAG-ARCHITECTURE-TEMPLATE.md) |
| `EXECUTION-RESULT.md` | 시나리오별 기대·실제·PASS/FAIL·시간·노드, 실패 원인·조치·재시험 | 모든 숫자에 `runs/` 근거, 원본 체크리스트 포함 | [결과서 템플릿](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/templates/EXECUTION-RESULT-TEMPLATE.md) |

`WORKFLOW-DESIGN.md`, `RAG-ARCHITECTURE.md`, `EXECUTION-RESULT.md`가 핵심 **필수 산출물 3종**이다. `TOPIC.md`·`TEAM-CHARTER.md`·데일리 3장·README·워크플로우·시나리오·실행 보고서도 함께 제출한다. `API-CONTRACT.md`·`ROLE-PLAN.md`·이 안내서는 팀 개발을 돕는 추가 문서다. [제출 안내](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/08-SUBMISSION.md).

### `docs/daily/`, `docs/images/`

- `daily/DAY80.md`, `DAY81.md`, `DAY82.md`: 그날 목표·실제 통과 수·막힌 점·결정·다음 행동. [데일리 템플릿](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/templates/DAILY-LOG-TEMPLATE.md)을 따른다.
- `images/`: 제출·발표에 실제 사용하는 n8n/웹 화면 캡처만 넣는다. 키·연락처·비밀번호를 가리고 문서에서 캡처를 가리킨다.

### `cases/`, `runs/`, `requests/`

- `cases/team.json`: 우리 팀 질문 **5개 이상**, 각 입력·조건·기대 결과. 정상·경계·권한·이관·장애를 포함한다. 기본 주제의 공통 `cases/common.json`은 수업 키트 원본을 사용하며 기대값을 바꾸지 않는다.
- `runs/`: `flow.py test`·반복·장애·bench의 **실제 JSON 보고서**를 저장한다. 빈 `PASS` 보고서를 만들지 않는다. 실패와 재시험을 결과서에 연결한다.
- `requests/`: 시연·bench에서 재현할 요청 JSON. 발표 순서에 맞춰 정상→보완 질문→이관→장애 요청을 준비한다.
- **시험 기준:** 공통 14유형 + 팀 5개 이상, LLM 경로는 3회 반복, 팀 VM 배포 뒤 회귀 시험. [공통 데이터·시나리오](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/03-SCENARIOS-AND-DATA.md), [시험 가이드](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/07-TESTING-GUIDE.md).

### `deploy/`, 루트 설정 파일

- `deploy/`: 팀 VM에서 Next.js·FastAPI·PostgreSQL을 같은 설정으로 실행하는 Compose/배포 파일과 필요한 초기화 절차. 선생님 제공 n8n·data-api와 포트·서비스명을 맞춘다.
- `.env.example`: 필요한 변수 이름만 적는다. 실제 `.env`와 첫 관리자 비밀번호는 Git에 올리지 않는다.
- `.gitignore`: 환경값·빌드 산출물·로컬 캐시를 제외한다. `runs/`의 제출 보고서는 제외하지 않는다.
- `AGENTS.md`: 팀의 CLI 코딩 에이전트 작업 범위·검증·비밀값 규칙.
- `README.md`: 팀·역할, 실행·배포 순서, 웹훅 경로, 공통·팀 시험 명령, VM 시연 순서와 한계. **최종 제출 시 이 문서만 따라 재실행 가능해야 한다.**

## 3. 제출 전 확인

- [ ] `docs/TOPIC.md` 강사 승인과 팀 헌장 사람별 역할이 반영됐다.
- [ ] 필수 산출물 3종·데일리 3장·n8n JSON·`cases/team.json`·`runs/`가 실제 내용으로 채워졌다.
- [ ] 설계서의 노드·페이로드·수치와 구현·시험 보고서가 일치한다.
- [ ] 팀 VM에서 같은 README 명령으로 동작하고 시연 순서를 리허설했다.
- [ ] `tscan scan .` 등으로 키·실제 연락처 노출 0건을 확인했다.
- [ ] 82일차(11/09) 14:50 전 기본 브랜치의 마지막 커밋으로 제출했다.
