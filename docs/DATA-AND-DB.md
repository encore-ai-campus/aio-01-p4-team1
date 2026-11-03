# 데이터·PostgreSQL 구현 기준

직원·규정·FAQ·기존 접수는 data-api를 사용한다. 새 계정·문의·티켓·알림은 PostgreSQL에, 문서 청크·임베딩은 PostgreSQL+pgvector에 저장한다.
이 문서의 구조로 구현하고, 변경이 필요하면 지정된 연결 담당자와 검토 후 오현님에게 요청한다.

## 1. 사용할 데이터

| 데이터 | 읽는 위치 | 사용 방법 |
| --- | --- | --- |
| 직원 6명 | GET /employees | name·dept로 직원 초기 데이터를 구성한다. IT팀 2명은 관리자 권한으로 연결한다. |
| 기존 티켓 4건 | GET /tickets/{id}?requester={name} | T-1001~T-1004의 본인 조회·처리 상태·마스킹을 검증한다. |
| FAQ 6종 | GET /faq?q={question} | 반복 문의의 해결 절차를 활용한다. |
| 규정 8종·관리자 전용 문서 | GET /docs · /docs/{name} | 청킹·임베딩·색인 원본으로 사용하고 접근 권한을 메타데이터에 보존한다. 관리자 문서가 누락된 환경은 배포 전에 확인한다. |

직원 초기 데이터는 name·dept를 필수로 사용한다. 이메일·입사일은 임의로 생성하지 않는다.
기존 티켓의 status·note·contact 구조는 조회용으로 유지한다. 연락처는 응답·로그·캡처에서 가린다.
실습 검증 스키마를 업무 DB의 필수 필드로 자동 복제하지 않고 아래 테이블 기준을 적용한다.
공통 시험은 프로젝트 키트의 원본 판정을 사용한다. 실행 환경의 데이터/API가 기준과 다르면 원민님이 재현 자료를 기록하고 오현님에게 변경 요청한다.

## 2. 저장·권한 원칙

- data-api: 규정·FAQ·직원·기존 접수 조회와 공통 고장 시험.
- PostgreSQL: 실제 로그인 계정·세션·새 문의·티켓·알림·처리 상태.
- PostgreSQL+pgvector: 문서 청크·임베딩·권한 메타데이터. 업무 테이블과 분리.
- 공개 회원가입은 없다. 첫 관리자 1명을 준비하고 나머지 계정은 관리자가 발급한다.
- n8n은 AI 흐름을 처리하고 FastAPI는 인증·권한·업무 저장을 담당한다.

## 3. 업무 DB · 지혜님 구현

스키마명 app, 기본키 bigint identity, 시간은 timestamptz, 외부 요청 식별자는 request_id(text, 1~64자).
FK 컬럼에는 필요한 조회 인덱스를 둔다. 아래 표는 논리 구조이며 타입·NULL·기본값을 마이그레이션으로 정확히 옮긴다.

| 테이블 | 주요 컬럼·관계 | 제약·의도 |
| --- | --- | --- |
| app.employees | id PK, name, dept | name UNIQUE. 제공 6명만 초기 적재, 없는 이메일/입사일은 필수화하지 않음 |
| app.users | id PK, employee_id FK, login_id, password_hash, role, is_active, must_change_password, created_at | employee_id UNIQUE·login_id UNIQUE. role=employee/admin. 관리자 role은 IT팀 직원만 부여하도록 서버 검사 |
| app.sessions | id PK, user_id FK, token_hash, expires_at, revoked_at | token_hash UNIQUE. 쿠키 토큰 원문 DB 저장 금지 |
| app.inquiries | id PK, request_id, requester_id FK→employees, question, attempt, context, result JSONB, status, created_at | request_id UNIQUE. 사용자별 소유권 검사 후 조회/재시도. attempt>=1, question 1~500자 |
| app.tickets | id PK, ticket_id, request_key, inquiry_id FK nullable, requester_id FK, title, category, priority, status, assignee_id FK nullable, reply, created_at, updated_at | request_key UNIQUE·ticket_id UNIQUE. 일반 웹 요청은 inquiry 연결, 교사 직접 웹훅 시험은 inquiry 없이 생성 가능 |
| app.alerts | id PK, ticket_id FK nullable, event_key nullable UNIQUE, workflow, node, message, severity, created_at | 티켓 생성 실패도 기록 가능. 선택 event_key로 중복 알림 억제. 민감정보를 가린 message 저장 |
| app.dlq | id PK, request_id nullable, execution_ref nullable, workflow, node, reason, safe_payload JSONB, status, created_at | 실패 재처리 대기. 비밀값·개인정보를 제거한 입력만 저장 |

웹 티켓의 내부 status는 open/in_progress/resolved, 화면 표시는 접수/처리 중/완료로 매핑한다.
기존 data-api 티켓의 처리 완료·접수됨·반려 등 상태는 원본을 유지한다. 두 데이터의 상태 집합을 같다고 가정하지 않는다.
priority는 API에서 normal/high로 시작하고 화면 보통/긴급으로 표시한다.
새 ticket_id는 접수 원본 T-1001~1004와 충돌하지 않도록 별도 시퀀스로 T-2001부터 발급한다.
동일 request_key의 재시도는 같은 티켓을 반환한다. 타인이 같은 키를 재사용하면 타인 기록 반환 없이 거절한다.
티켓/알림의 DLQ·중복 처리는 거래와 재시도 경계를 지혜님 구현에서 보장하고 원민님이 시험한다.

## 4. RAG DB · 유빈님 사용, 지혜님 마이그레이션

| 테이블 | 주요 컬럼·관계 | 제약·의도 |
| --- | --- | --- |
| rag.documents | id PK, doc_key, title, access_level, source_url nullable, source_hash, updated_at | doc_key UNIQUE. access_level은 all/it, 미정 권한 문서는 색인 거절 |
| rag.chunks | id PK, document_id FK, chunk_no, section, content, content_hash, embedding vector(3072), embedding_model, metadata JSONB | (document_id,chunk_no) UNIQUE. FK 조회 인덱스, 업무 기록과 분리 |

기본 임베딩은 수업 모델 text-embedding-3-large, 기본 출력 3072차원이다.
초기 검색은 cosine 거리의 정확 검색, 반환 score는 1-cosine distance, top_k=3을 사용한다.
권한 조건을 SQL의 검색 대상에 먼저 적용한다. 초기에는 근사 벡터 인덱스를 필수로 만들지 않는다.
3072차원에 HNSW vector 인덱스를 그대로 만들 수 있다고 가정하지 않는다. 근사 검색을 추가하면 타입/차원 제약과 품질을 별도 검토한다.
모델·차원이 달라지면 기존 벡터와 섞지 않고 마이그레이션/재색인을 계획한다.
자동 답변 점수 기준은 측정 뒤 확정한다. 설정 파일에 값을 분리하고 측정 전에는 검증 실패·근거 없음에서 이관한다.

유빈님은 문서→청크→임베딩→저장·검색을 구현하고 지혜님은 확장·스키마·마이그레이션·접속 권한을 구현한다.
문서 권한(`access_level`)은 `/docs` 응답이 제공하는 권한 메타데이터를 우선 사용하며, 메타데이터가 없는 경우 일반 사내 규정 8종은 `all`, IT/관리자 전용 운영 문서는 `it`로 매핑하고 미확인 문서는 색인을 거절한다. 재색인은 문서 단위 트랜잭션으로 교체하며 권한 축소(`all`→`it`) 또는 삭제 문서는 이전 공개 청크를 남기지 않는다.
이 표를 적용하는 데 사전 재협의는 필요 없다. 표를 바꾸려 할 때만 C06 상대와 변경 요청한다.
확장 활성화·named volume·재색인·새 환경 생성·DB 재시작 유지의 실제 확인은 아직 수행하지 않았다.

근거: [수업 RAG](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/05-RAG-DESIGN-GUIDE.md), [pgvector 공식 사용법·거리·검색·인덱스](https://github.com/pgvector/pgvector).
