# 데이터 출처와 PostgreSQL 설계 기본안

> 기존 확정: 수업 기본 데이터 활용, FastAPI+PostgreSQL 업무 저장, pgvector RAG.
> 아래 신규 테이블명·컬럼·제약은 팀장 검토·배포용 v0 설계안이다. 수업에서 완성된 우리 DB 스키마를 제공한 것으로 오해하지 않는다. SQL·마이그레이션은 아직 구현 전이다.

## 1. 수업자료에 실제로 있는 것

| 자료 | 확인된 위치 | 우리 팀 사용 |
| --- | --- | --- |
| 직원 6명 | [employees.json](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/78/data-api/data/employees.json) | name·dept를 원본으로 직원 초기 데이터 구성. IT팀 2명은 관리자 권한 연결 |
| 기존 티켓 4건 | [tickets.json](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/78/data-api/data/tickets.json) | T-1001~1004 본인 조회·마스킹·공통 시험. 현재 계획대로 data-api에서 조회 |
| FAQ 6종 | [faq.json](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/78/data-api/data/faq.json) | 제공 FAQ 활용 |
| 규정 8종 | Last3Mon/78/data-api/data/docs/ | GET /docs로 색인 원본. 프로젝트판 관리자 전용 문서 추가 여부는 80일차 키트 확인 |
| 입력 검증 스키마 3종 | [employee](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/78/data-api/data/schemas/employee.json) · [ticket](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/78/data-api/data/schemas/ticket.json) · [faq](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/78/data-api/data/schemas/faq.json) | 78일차 가져오기/품질 검사용 입력 규칙 |
| API 코드 | [server.py](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/78/data-api/server.py) | 직원/문서/접수 조회·티켓 생성·알림·장애·중복 처리의 참고 구현 |
| 프로젝트 기준 | [03 데이터 안내](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/03-SCENARIOS-AND-DATA.md) | 프로젝트의 데이터·권한·공통 시험 기준 |

78일차 JSON 스키마는 PostgreSQL CREATE TABLE이 아니다.
예를 들어 직원 검증 스키마에는 email·joined가 필요하지만 제공 직원 원본은 name·dept만 있다.
티켓 검증 스키마는 신규 가져오기 입력이고, 기존 티켓 조회 데이터의 status·note·contact 구조와 같지 않다.
따라서 스키마를 그대로 DB로 복제하거나 없는 직원 이메일·입사일을 사실처럼 채우지 않는다.

확인한 수업 커밋은 9ce9ace다. 이 버전에는 Last3Mon/80 실행 키트가 아직 없다.
현재 78일차 파일로 준비하되 실제 공통 시험은 배포되는 80일차 키트 원본으로 실행한다.
새 자료가 기존 기준과 다르면 원민님이 차이를 기록하고 오현님이 호환 방식을 공지한다.

## 2. 이미 정한 저장 방향

- data-api: 제공 규정·FAQ·직원·기존 접수 및 공통 시험의 고장/관측 대상.
- PostgreSQL: 실제 로그인 계정·세션·새 문의·티켓·알림·상태.
- PostgreSQL+pgvector: 문서 청크·임베딩·권한 메타데이터. 업무 테이블과 분리.
- 공개 회원가입 없음. 첫 관리자 1명을 안전하게 준비하고 나머지 계정은 관리자가 발급.
- n8n은 AI 흐름을 처리하고 FastAPI는 인증·권한·업무 저장을 담당.

## 3. 업무 DB v0 · 지혜님 구현

스키마명 app, 기본키 bigint identity, 시간은 timestamptz, 외부 요청 식별자는 request_id(text, 1~64자).
FK 컬럼에는 필요한 조회 인덱스를 둔다. 아래 표는 논리 구조이며 타입·NULL·기본값을 마이그레이션으로 정확히 옮긴다.

| 테이블 | 주요 컬럼·관계 | 제약·의도 |
| --- | --- | --- |
| app.employees | id PK, name, dept | name UNIQUE. 제공 6명만 초기 적재, 없는 이메일/입사일은 필수화하지 않음 |
| app.users | id PK, employee_id FK, login_id, password_hash, role, is_active, must_change_password, created_at | employee_id UNIQUE·login_id UNIQUE. role=employee/admin. 관리자 role은 IT팀 직원만 부여하도록 서버 검사 |
| app.sessions | id PK, user_id FK, token_hash, expires_at, revoked_at | token_hash UNIQUE. 쿠키 토큰 원문 DB 저장 금지 |
| app.inquiries | id PK, request_id, requester_id FK→employees, question, attempt, context, result JSONB, status, created_at | request_id UNIQUE. 사용자별 소유권 검사 후 조회/재시도. attempt>=1, question 1~500자 |
| app.tickets | id PK, ticket_id, request_key, inquiry_id FK nullable, requester_id FK, title, category, priority, status, assignee_id FK nullable, reply, created_at, updated_at | request_key UNIQUE·ticket_id UNIQUE. 일반 웹 요청은 inquiry 연결, 교사 직접 웹훅 시험은 inquiry 없이 생성 가능 |
| app.alerts | id PK, ticket_id FK nullable, workflow, node, message, severity, created_at | 티켓 생성 실패도 기록 가능. 민감정보를 가린 message 저장 |
| app.dlq | id PK, request_id, reason, safe_payload JSONB, status, created_at | 실패 재처리 대기. 비밀값·개인정보를 제거한 입력만 저장 |

웹 티켓의 내부 status는 open/in_progress/resolved, 화면 표시는 접수/처리 중/완료로 매핑한다.
기존 data-api 티켓의 처리 완료·접수됨·반려 등 상태는 원본을 유지한다. 두 데이터의 상태 집합을 같다고 가정하지 않는다.
priority는 API에서 normal/high로 시작하고 화면 보통/긴급으로 표시한다.
새 ticket_id는 접수 원본 T-1001~1004와 충돌하지 않도록 별도 시퀀스로 T-2001부터 발급한다.
동일 request_key의 재시도는 같은 티켓을 반환한다. 타인이 같은 키를 재사용하면 타인 기록 반환 없이 거절한다.
티켓/알림의 DLQ·중복 처리는 거래와 재시도 경계를 지혜님 구현에서 보장하고 원민님이 시험한다.

## 4. RAG DB v0 · 유빈님 사용, 지혜님 마이그레이션

| 테이블 | 주요 컬럼·관계 | 제약·의도 |
| --- | --- | --- |
| rag.documents | id PK, doc_key, title, access_level, source_url nullable, source_hash, updated_at | doc_key UNIQUE. access_level은 all/it, 미정 권한 문서는 색인 거절 |
| rag.chunks | id PK, document_id FK, chunk_no, section, content, content_hash, embedding vector(3072), embedding_model, metadata JSONB | (document_id,chunk_no) UNIQUE. FK 조회 인덱스, 업무 기록과 분리 |

기본 임베딩은 수업 모델 text-embedding-3-large, 기본 출력 3072차원이다.
초기 검색은 cosine 거리의 정확 검색, 반환 score는 1-cosine distance, top_k=3으로 제안한다.
권한 조건을 SQL의 검색 대상에 먼저 적용한다. 초기에는 근사 벡터 인덱스를 필수로 만들지 않는다.
3072차원에 HNSW vector 인덱스를 그대로 만들 수 있다고 가정하지 않는다. 근사 검색을 추가하면 타입/차원 제약과 품질을 별도 검토한다.
모델·차원이 달라지면 기존 벡터와 섞지 않고 마이그레이션/재색인을 계획한다.
자동 답변 점수 기준은 측정 뒤 확정한다. 설정 파일에 값을 분리하고 측정 전에는 검증 실패·근거 없음에서 이관한다.

유빈님은 문서→청크→임베딩→저장·검색을 구현하고 지혜님은 확장·스키마·마이그레이션·접속 권한을 구현한다.
이 표를 적용하는 데 사전 재협의는 필요 없다. 표를 바꾸려 할 때만 C06 상대와 변경 요청한다.
확장 활성화·named volume·재색인·새 환경 생성·DB 재시작 유지의 실제 확인은 아직 수행하지 않았다.

근거: [수업 RAG](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/05-RAG-DESIGN-GUIDE.md), [pgvector 공식 사용법·거리·검색·인덱스](https://github.com/pgvector/pgvector).
