# 지혜님 · 마이그레이션 작업 지시

[IMP-PLAN P0-3~6](../Doc/IMP-PLAN.md)에서 이 절차를 사용한다. 기준은 [DATA-AND-DB](../../../docs/DATA-AND-DB.md)다. 아래 파일·명령·검사는 P0 단계에서 순서대로 생성·검증한다.

## 현재 범위와 전제

P0-6 갱신: 직원 seed·첫 관리자 CLI를 구현했으며 DDL revision은 `0004`를 유지한다. 거래 rollback 기반 실제 PostgreSQL 검증은 완료했지만 상시 직원/계정 적재와 실제 원본/VM 실행은 미실행이다. 실행 순서·필수 설정은 [배포 안내](../deploy/README.md)의 P0-6 인계를 따른다. seed는 revision에서 실행하지 않는다.

P0-5 갱신(2026-11-05): 아래 P0-4 설명은 당시 상태다. 현재 전용 검증 DB에 `0003→0004`를 적용해 `rag.documents/chunks`, `vector(3072)`, 두 조회 인덱스와 비밀번호 없는 NOLOGIN 그룹 역할 `oke_app/oke_rag_index/oke_rag_search`의 ACL을 확인했다. 현재 head는 `0004`이며 실제 검증 결과는 IMP-PLAN P0-5 기록을 따른다. 런타임 LOGIN 자격증명/비밀은 이 DDL에 포함하지 않았고 오현님 비밀 설정과 실제 서비스 연결 시 확인한다.

2026-11-05 현재 전용 검증 DB에 P0-4 `0001→0002`를 적용해 vector 확장·app/rag 스키마·업무 테이블 7개를 확인했다. 개인 [SPEC 1절](../Doc/SPEC.md#1-적용할-기준--새로-선정하지-않음)에 적용 기준과 공통 대조 커밋을 모았다. rag 테이블/권한은 P0-5다. 다른 환경에서 적용 전에는 권한·비밀 설정을 별도로 확인한다.

alembic.ini/env.py/script.py.mako와 Base/session factory 및 업무 모델을 생성했다. history/heads는 단일 체인·`0002 (head)`이고 전용 DB의 current도 `0002 (head)`다. env.py의 include_schemas/include_name은 app/rag만 autogenerate 대상으로 삼으며, public.alembic_version은 관리 이력용 예외 위치다. P0-5의 RAG 모델 등록은 후속 단계다.

DB 접속은 환경변수 DATABASE_URL의 명시적 postgresql+psycopg 드라이버를 사용한다. 설정 누락/형식 오류는 접속 문자열 없이 실패하고, 실제 migration 명령도 SQLAlchemy 예외 원문을 출력하지 않는다. 기본 앱 시작 시 DB 접속/create_all/seed는 하지 않는다. P0-4 실제 DB 검사40개, 전체155개 통과·기존 경고1건이며 자세한 명령은 IMP-PLAN에 있다.

알림 event_key UNIQUE와 DLQ 테이블은 확정된 DB 기반이다. H07의 응답 duplicate 확장은 새 DB 컬럼을 요구하는 제안이 아니며, ACK 명문화 대기로 기본 DDL을 중단하지 않는다. inquiries.context는 nullable text로 두고 API의 최대2,000자 검증은 확정 입력 기준으로 적용한다. 추가 DB CHECK는 공통 논리표와 구별해 물리 구현에서 검토한다.

## 생성 순서

| 순서 / 예정 파일 | 적용 작업 | 확인할 결과 |
| --- | --- | --- |
| 0: migrations/alembic.ini, env.py, script.py.mako; app/db/base.py·session.py·models/*.py | Alembic script_location을 migrations로 고정. models 메타데이터 import, include_schemas로 app/rag만 관리, URL은 DATABASE_URL에서 읽고 출력하지 않음 | 본인 폴더에서 history/heads가 단일 체인. 다른 스키마를 autogenerate 삭제 대상으로 포함하지 않음 |
| 1: versions/0001_extensions_and_schemas.py | vector 확장, app/rag 스키마. 확장 권한은 마이그레이션 실행 계정으로만 수행 | pg_extension의 vector 버전, app/rag 존재, 빈 DB에서 시작 가능 |
| 2: versions/0002_app_tables.py | employees→users→sessions, inquiries→tickets→alerts, dlq 순서 생성. 외부 ticket_id용 시퀀스를2001부터 별도 생성 | 표의 PK/FK·NULL·기본값·고유키/검사 제약을 카탈로그로 확인 |
| 3: versions/0003_rag_tables.py | documents→chunks, vector(3072), source_hash/권한 메타데이터 | documents/chunks 분리, 차원3072, 3071차원 거절, 미정 access_level 거절 |
| 4: versions/0004_indexes_and_grants.py | FK/조회 인덱스와 런타임 최소 권한 부여. UNIQUE/체크는 해당 테이블 생성 revision에 둠 | app 런타임·색인·검색 계정의 허용/거절을 실제 접속으로 검사. 근사 벡터 인덱스 없음 |
| 5: app/services/bootstrap.py, app/cli.py | DDL과 별개로 직원6명 적재→첫 관리자1명 생성 | 재실행 무변경·원문 비밀번호/쿠키 DB 저장 없음 |

revision 순서는 0001→0002→0003→0004 단일 head로 한다. autogenerate는 초안 생성 도구이며 extension·schema·vector 타입·시퀀스·grant·명명된 제약·서버 기본값을 수동 검토한다. 스키마 변경마다 새 revision을 만들고 이미 적용된 파일을 덮어쓰지 않는다. seed는 revision 안에서 data-api를 부르지 않는다.

## 업무 테이블 적용표 · BE-01·03~05

기본 PK는 모든 표에서 bigint identity, 시간은 timestamptz다. 아래는 공통 논리 구조를 DDL로 옮길 **물리 구현안**이다. 공통에 없는 외부 정책이나 비밀번호 이력 컬럼을 이 기본 revision에 섞지 않는다. FK는 별도 사유 없이 cascade 삭제하지 않고 보존한다. 사용자 비활성화는 삭제가 아니다.

| 테이블 | NOT NULL / 기본값 | NULL 허용 | 관계·제약·인덱스 |
| --- | --- | --- | --- |
| app.employees | name text, dept text | 없음 | name UNIQUE. name/dept 원본을 유지 |
| app.users | employee_id bigint, login_id text, password_hash text, role text, is_active bool=true, must_change_password bool=true, created_at=현재시각 | 없음 | employees FK, employee_id/login_id 각각 UNIQUE, role employee/admin CHECK. IT팀 검사는 서버에서 실시 |
| app.sessions | user_id bigint, token_hash text, expires_at | revoked_at | users FK, token_hash UNIQUE, user_id·expires_at 인덱스. 토큰 원문 없음 |
| app.inquiries | request_id text, requester_id bigint, question text, attempt integer=1, status text, created_at=현재시각 | context text, result JSONB | employees FK, request_id UNIQUE·길이1~64, question1~500·attempt>=1 CHECK, (requester_id,created_at) 인덱스. status의 초기/전이값은 H04 초안 |
| app.tickets | ticket_id text, request_key text, requester_id bigint, title text, category text, priority text, status text=open, created_at/updated_at=현재시각 | inquiry_id bigint, assignee_id bigint, reply text | request_key/ticket_id 각각 UNIQUE, inquiry→inquiries·requester→employees·assignee→employees FK. request_key1~64·priority normal/high·status open/in_progress/resolved CHECK. 관련FK·(status,created_at) 인덱스 |
| app.alerts | workflow/node/message/severity text, created_at=현재시각 | ticket_id bigint, event_key text | ticket_id→tickets.id FK, event_key nullable UNIQUE(중복 알림 억제). 외부 T-번호를 직접 bigint에 넣지 않음. FK·created_at 인덱스 |
| app.dlq | workflow/node/reason/status text, safe_payload JSONB, created_at=현재시각 | request_id text, execution_ref text | request_id·execution_ref 인덱스, 민감 입력 원문 없음 |

공통 표의 nullable 필드(context/result/reply, alerts.event_key, dlq.request_id/execution_ref)와 FK 대상(`tickets.assignee_id` → `app.employees.id`)을 위 표대로 일치시킨다. inquiries.status·dlq.status에는 초기부터 과도한 CHECK enum을 강제하지 않는다.

updated_at은 티켓 수정 거래에서 갱신한다. T-2001 번호는 별도 시퀀스와 UNIQUE로 보장하며 로우 수+2001 방식은 쓰지 않는다. 같은 request_key의 티켓 생성 경쟁은 제약 위반을 처리해 기존 소유자 확인 후 기존 티켓을 반환한다. 문의 없이 들어온 직접 웹훅은 inquiry_id=null로 저장할 수 있다.

## RAG 적용표 · BE-06

| 테이블 | NOT NULL / 기본값 | NULL 허용 | 제약·검증 |
| --- | --- | --- | --- |
| rag.documents | id bigint identity, doc_key/title/access_level/source_hash text, updated_at=현재시각 | source_url text | doc_key UNIQUE, access_level all/it CHECK. 권한값 누락·미정을 all로 바꾸지 않음 |
| rag.chunks | id bigint identity, document_id bigint, chunk_no integer, section/content/content_hash text, embedding vector(3072), embedding_model text, metadata JSONB | 없음 | documents FK, (document_id,chunk_no) UNIQUE, FK 인덱스. 모델 text-embedding-3-large·차원 일치 검사 |

metadata에는 검색/색인 담당이 doc/title/section/chunk/type/updated_at/version 등을 보존한다. access_level의 권한 원본은 documents에서 join해 사용한다. content_hash/source_hash로 같은 원본 재색인을 식별한다. 유빈님은 한 문서의 새 청크 준비 후 거래로 교체하고 실패 시 기존 청크를 유지하도록 색인을 구현한다. 다른 모델 벡터와 섞지 않는다.

처음에는 정확 cosine 조회와 score=1-distance, top_k=3을 사용한다. app에서 직원 조회 후 검증한 all 또는 all+it를 검색 대상 조건에 넣는다. 실제 SQL 쿼리는 유빈님 소유이며 여기서 복제하지 않는다. DB grants만으로 직원별 권한 필터가 완성되었다고 판단하지 않는다.

## 접속 권한과 비밀값

- 마이그레이션 계정은 확장/DDL·grant용이다. 웹 앱이나 n8n에 같은 권한을 주지 않는다.
- 구현용 역할 이름은 `oke_app`(app 업무 DML·필요 시퀀스), `oke_rag_index`(rag 색인 DML), `oke_rag_search`(rag SELECT)로 계획한다. PUBLIC의 불필요한 쓰기/생성 권한을 회수하고 schema USAGE·향후 객체 기본 권한도 확인한다.
- role 생성은 오현님이 제공하는 DB 관리 접속으로, 비밀번호는 비밀 입력으로 준비한다. 마이그레이션에는 비밀번호 리터럴을 쓰지 않는다. 역할이 없으면 grant 오류를 명확히 보고한다. 운영 URL은 각 프로세스의 DATABASE_URL 또는 n8n Credential에 넣고 문서/예제에는 이름만 둔다.
- 검색 계정의 INSERT·DROP, 앱 계정의 rag DDL·확장 변경은 거절되어야 한다. 변경이 필요하면 C06 유빈님/C07 오현님에게 HANDOFF로 요청한다.

## 구현 후 확인 순서 · 전부 미실행

작업 디렉터리는 저장소 기준 `develop/jihye`다. DATABASE_URL은 **개별 빈 검증 DB**를 가리키게 하고 공유/운영 DB에 downgrade를 실행하지 않는다.

1. `uv run alembic -c migrations/alembic.ini heads`와 `history`로 순서·단일 head를 확인한다.
2. `uv run alembic -c migrations/alembic.ini upgrade head` 후 `current`로0004 head를 확인한다. 동일 upgrade 재실행에서 추가 DDL/데이터 변경이 없어야 한다.
3. `uv run pytest tests/integration/test_migrations.py -q`로 카탈로그 타입·NULL·기본값·FK·UNIQUE·인덱스·vector 확장/차원·권한을 검사할 예정이다. 이 파일은 본인 DB 검사 전용으로 구현한다.
4. `uv run pytest tests/integration/test_persistence.py tests/integration/test_pgvector.py -q`로 본인 문의/티켓·일반/IT 테스트 문서·차원 거절·정확 검색을 확인한다. 테스트용 가상 벡터 결과를 실제 임베딩 품질로 보고하지 않는다.
5. named volume을 유지한 postgres 재시작 전후 revision/행 수/키/벡터 차원·조회 결과를 비교한다. DB 재시작과 재색인은 별도 확인이다. 기본 절차에 volume 삭제를 넣지 않는다.
6. rollback 검증은 폐기 가능한 DB에서만 revision 한 단계씩 내렸다 올려 의존 순서를 확인한다. 공유 데이터가 있는 적용 후 rollback은 사전 백업·복원 또는 새 수정 revision으로 오현님이 판단한다. 다운그레이드가 데이터를 복구해 준다고 쓰지 않는다.
7. P1-4에서 별도 DB 백업을 다른 격리 DB에 복원한 뒤 revision·관계·행 수·해시를 대조한다. 유빈님이 복원 후 권한별 검색을 확인한다. 문서 갱신 실패의 이전 성공본 유지와 권한 축소/삭제 시 이전 공개본 차단을 함께 시험한다. 전체 원본 API 장애를 문서 전체 삭제로 해석하지 않는다. volume 유지 재시작과 백업·복원은 다른 확인이다.

## 전달 결과

유빈님에게 head·테이블/열·모델/차원·role 권한·접속 방식(비밀값 제외)과 실제 검사 결과를 넘긴다. 원민님에게 중복 제약·티켓/알림 거래·DLQ 저장 및 ACK 세부 미정 상태를, 오현님에게 새 환경 생성/재시작/백업·복구 확인 자료를 넘긴다. H02의 비밀번호 이력/잠금용 확장은 공통 반영 후 별도 revision으로 만든다.

[팀 API](../../../docs/API-CONTRACT.md) · [데이터·DB 기준](../../../docs/DATA-AND-DB.md) · [전체 아키텍처](../../../docs/ARCHITECTURE.md).
