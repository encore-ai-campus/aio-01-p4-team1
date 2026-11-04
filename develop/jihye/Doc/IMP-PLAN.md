# 지혜님 · IMP-PLAN

[README](../README.md) → [TODO](TODO.md) → [SPEC](SPEC.md) → **IMP-PLAN**. 여기서 첫 미완료 단계부터 실행한다. 공통 기본안을 적용할 때 별도 승인을 기다리지 않는다. 누락 정책은 [HANDOFF](HANDOFF.md)에 제안으로 두고 그 정책과 무관한 작업을 계속한다.

**전체 상태: 구현·설치·시험·DB 적용·배포 미실행.** 아래 생성 파일과 확인 명령은 모두 구현 예정이다. 코드 경로는 현재 존재하는 링크가 아니다. 각 단계의 체크는 실제 확인 증거를 남긴 뒤에만 한다. 이 문서 보완 작업에서는 코드·SQL·JSON·패키지를 생성하지 않는다.

모든 아래 로컬 명령의 작업 디렉터리는 저장소 기준 `develop/jihye`다. 의존성이 없는 모델/Mock 시험부터 시작한다. DB 시험은 본인 전용 검증 DB, 실제 연결은 제공자 준비 후에 수행한다.

## P0-1 · FastAPI 골격과 공통 검증 타입부터

- [ ] 연결 SPEC: BE-02·05, C01/C07.
- 생성 예정: `pyproject.toml`, 설치 검증 후 `uv.lock`, `app/__init__.py`, `app/main.py`, `app/core/config.py`, `app/api/errors.py`, `app/api/routes/health.py`, `app/schemas/common.py`, `tests/test_contract_basics.py`.
- 작업: FastAPI/Pydantic·uvicorn·SQLAlchemy·psycopg·Alembic·pgvector 타입·HTTPX·비밀번호 해시 라이브러리와 시험 도구를 본인 프로젝트에 선언한다. config는 공통 변수 이름을 읽고 잘못된 SERVICE_MODE를 거절한다. secret 필드를 출력하지 않는다. liveness와 400 웹 오류 외형, 질문/ID/attempt 공통 제약 타입을 만든다. DB·n8n 없이 작동하는 골격부터 만든다.
- 확인 예정: `uv sync --dev` → `uv run pytest tests/test_contract_basics.py -q`. 공백 질문/501자/ID65자/attempt0·문자열/boolean 거절, 500자/64자/attempt1 수락, 검증 오류에 입력 비밀값이 없는지 확인한다. 요구가 정해지지 않은 세부 코드값은 H03 미확정으로 표시한다.
- 넘길 결과: 다음 단계에 설치된 버전·잠금 파일·공통 타입과 기대 오류 예시. 설치 성공이나 시험 통과는 실제 실행 후 기록한다.

## P0-2 · 요청/응답 모델과 계약 Mock

- [ ] 연결 SPEC: BE-01~04, C01/C02/C05.
- 생성 예정: `app/schemas/auth.py`, `users.py`, `support.py`, `inquiries.py`, `tickets.py`, `alerts.py`; `app/api/deps.py`; `app/api/routes/auth.py`, `users.py`, `ask.py`, `requests.py`, `tickets.py`, `alerts.py`; `tests/test_api_models.py`, `tests/test_support_contract.py`, `tests/conftest.py`.
- 작업: SPEC 3~5절 모델과 라우터 시그니처를 연결한다. 응답에서 비밀 필드를 제외하고 support의 reason/timings와 추가 응답 필드를 보존한다. 미구현 라우터를 성공 응답으로 위장하지 않는다. Mock은 tests 안의 HTTP transport/fixture로 만들며 다른 역할의 워크플로우를 복제하지 않는다.
- 확인 예정: `uv run pytest tests/test_api_models.py tests/test_support_contract.py -q`. 12개 웹 경로·2개 내부 경로의 모델을 검증하고 정상5 route·400 codes passthrough·요청ID 불일치/잘못된 응답 검출·원문 암호 미직렬화를 확인한다. OpenAPI는 `app.openapi()` 결과를 시험에서 검사하고 외부 호출을 하지 않는다.
- 넘길 결과: 수언님에게 확정 계약 필드의 OpenAPI/예시, 다혁님에게 세션→user 변환 입력과 공통 응답 fixture, 원민님에게 /tickets·/alerts 예시. H03/04의 미확정 세부는 ‘제안’으로 함께 표시하며 실제 연결 확인으로 쓰지 않는다.

## P0-3 · DB 컨테이너와 마이그레이션 실행 기반

- [ ] 연결 SPEC: BE-05·06, C06/C07.
- 생성 예정: `deploy/compose.yaml`의 postgres 부분, `deploy/.env.example`, `migrations/alembic.ini`, `env.py`, `script.py.mako`, `app/db/base.py`, `session.py`, `tests/integration/test_db_connection.py`.
- 작업: [deploy 안내](../deploy/README.md)의 서비스명/포트를 그대로 사용하고 pgvector 포함 이미지·named volume·healthcheck를 준비한다. 실제 설치 검증 후 태그/digest를 기록한다. Alembic 대상은 app/rag만, URL은 DATABASE_URL에서 읽는다. 공개 postgres 포트나 루트 설정을 만들지 않는다.
- 확인 예정: 비밀 파일 준비 후 `docker compose --env-file deploy/.env -f deploy/compose.yaml config --quiet`, `up -d postgres`, `ps`를 각각 수행한다. `uv run pytest tests/integration/test_db_connection.py -q`로 본인 검증 DB 접속과 잘못된 자격증명 거절을 확인한다. pg_isready와 schema 적용 확인을 구분한다.
- 넘길 결과: 다음 단계/유빈님에게 검증한 이미지·확장 가용성·접속 방법(비밀 제외), 오현님에게 실제 네트워크/충돌 여부. 미가용 서비스는 미실행으로 남긴다.

## P0-4 · 확장→업무 테이블 생성

- [ ] 연결 SPEC: BE-01·03~05, C05/C06.
- 생성 예정: `migrations/versions/0001_extensions_and_schemas.py`, `0002_app_tables.py`, `app/db/models/employees.py`, `users.py`, `sessions.py`, `inquiries.py`, `tickets.py`, `alerts.py`, `dlq.py`와 모델 등록 파일; `tests/integration/test_migrations.py`.
- 작업: [migrations 안내](../migrations/README.md)의 타입/NULL/기본값/FK/고유키를 적용한다. vector·app/rag 생성 후 employees→users→sessions, inquiries→tickets→alerts, dlq 순으로 만든다. T-2001 별도 시퀀스와 request_key UNIQUE를 둔다. 계정 seed를 DDL 안에 섞지 않는다.
- 확인 예정: `uv run alembic -c migrations/alembic.ini history`, `upgrade head`, `current`를 순서대로 수행한다. `uv run pytest tests/integration/test_migrations.py -q`로 카탈로그를 확인하고 같은 upgrade 재실행이 무변경인지 검사한다. 자동 생성 결과의 확장·스키마·제약은 직접 검토한다.
- 넘길 결과: 원민님에게 티켓/알림/DLQ 구조·중복 제약·nullable inquiry, 다음 단계에 적용 revision과 실제 오류. H02 추가 보안 컬럼은 기본 revision에 미승인으로 넣지 않는다.

## P0-5 · RAG 테이블·인덱스·접속 권한

- [ ] 연결 SPEC: BE-05·06, C06.
- 생성 예정: `migrations/versions/0003_rag_tables.py`, `0004_indexes_and_grants.py`, `app/db/models/rag.py`, `tests/integration/test_pgvector.py`, `tests/integration/test_db_permissions.py`.
- 작업: rag.documents/chunks·vector(3072)·all/it·FK·UNIQUE를 적용하고 FK/조회 인덱스를 만든다. 정확 cosine·score=1-distance·top_k3 기준을 유지한다. 마이그레이션/업무/색인/검색 권한을 구분한다. 필요한 DB role은 관리 권한으로 비밀 입력을 사용해 준비하고 암호를 revision에 넣지 않는다.
- 확인 예정: `uv run alembic -c migrations/alembic.ini upgrade head`, `heads`, `current`로 단일0004 head를 확인한다. `uv run pytest tests/integration/test_pgvector.py tests/integration/test_db_permissions.py -q`로3072차원 수락/3071거절·권한 누락 거절·정확 검색 전 all/it 필터·권한별 쓰기/DDL 거절을 확인한다. 가상 벡터 시험은 실제 모델 품질 시험과 분리한다.
- 넘길 결과: 유빈님에게 head·열/차원·모델·권한·인증 주입 방법과 가상 벡터 검사 결과. 유빈님이 실제 문서/임베딩/재색인을 구현한다. HNSW·다른 모델·차원은 추가하지 않는다.

## P0-6 · 직원 seed와 첫 관리자

- [ ] 연결 SPEC: BE-01·05, C01/C07.
- 생성 예정: `app/clients/data_api.py`, `app/cli.py`, `app/services/bootstrap.py`, `app/core/security.py`, `tests/test_bootstrap.py`, `tests/integration/test_bootstrap_db.py`.
- 작업: SPEC 6절의 원본6명 대조→직원만 적재→명시한 IT팀 직원의 첫 계정 생성 순으로 만든다. GET /employees를 Mock으로 먼저 확인한다. bootstrap은 BOOTSTRAP_ADMIN_PASSWORD만 읽고 기존 계정 해시/역할을 덮어쓰지 않는다. 명령 이름은 아래와 같이 구현한다.
- 확인 예정: `uv run pytest tests/test_bootstrap.py tests/integration/test_bootstrap_db.py -q`. 정상6명, 누락/추가/부서불일치, 비IT bootstrap 거절, 암호 누락, 재실행 생성0건·기존 해시 유지, 비밀번호 미출력을 확인한다.
- 실제 seed 예정 명령: `uv run python -m app.cli seed-employees` 후 직원6명 확인. 이어 `uv run python -m app.cli bootstrap-admin --employee-name <제공 IT팀 이름> --login-id <선택한 ID>`를 실행하는 인터페이스다. `<…>`는 비밀을 제외한 선택값으로 치환하고 암호 인자는 만들지 않는다.
- 넘길 결과: 오현님에게 최초1회/재실행 조건과 일회성 암호 제거 절차. 나머지5명 발급은 P1-1 관리자 API에서 수행한다. 세션·비밀번호 규정·최후 관리자 보호는 H01·02·05 미확정 상태를 구분한다.

## P0-7 · backend 이미지·준비 상태·배포 묶음

- [ ] 연결 SPEC: BE-05·06, C07.
- 생성 예정: `deploy/backend.Dockerfile`, `deploy/.dockerignore`; `deploy/compose.yaml`의 backend/frontend/n8n/data-api 연결; `app/api/routes/health.py` 준비 상태 확장; `tests/integration/test_readiness.py`.
- 작업: [deploy 안내](../deploy/README.md)의 컨테이너/로컬 포트·build context·비밀 제외·프로세스/DB 준비 상태를 적용한다. backend는 본인 폴더를 context로 사용한다. frontend Dockerfile·프록시는 수언님 소유이며 아직 없으면 DB/backend까지만 확인한다. n8n/data-api 기존 환경 재사용 여부·실제 모드를 기록한다.
- 확인 예정: `docker compose --env-file deploy/.env -f deploy/compose.yaml build backend`, DB 적용 후 `up -d backend`, `curl --fail http://127.0.0.1:8000/health/ready`, `uv run pytest tests/integration/test_readiness.py -q`. DB 중단/미적용 revision/vector 누락을 준비 완료로 표시하지 않고 오류에 비밀값을 노출하지 않는지 확인한다. 전체 웹/AI 기능 완료 확인은 P1이다.
- 넘길 결과: 오현님에게 검증한 설치/기동/마이그레이션/seed/health 순서·버전·모드·서비스 대상·남은 의존성. 배포나 VM 회귀를 완료했다고 기록하지 않는다.

## P1-1 · 세션·관리자 발급·권한

- [ ] 연결 SPEC: BE-01, C01.
- 생성/수정 예정: `app/services/auth.py`, `accounts.py`, `app/repositories/users.py`, `sessions.py`, auth/users 라우터·deps·security; `tests/test_auth_permissions.py`, `tests/integration/test_accounts.py`.
- 작업: 로그인/로그아웃/me/암호 변경과 관리자 생성/비활성화/초기화를 연결한다. 모든 보호 경로에 활성 계정·역할 검사를 적용한다. 미확정 H01·02·03·05는 초안 모델/정책 분리로 준비하고 공통 반영 전 외부 동작으로 확정하지 않는다. 기본401/403·응답 비밀 제거는 바로 구현한다.
- 확인 예정: `uv run pytest tests/test_auth_permissions.py tests/integration/test_accounts.py -q`. 직원403·미로그인401·로그아웃 토큰 재사용401·비IT admin 불가·제공직원만 발급·계정 중복을 확인한다. 확정된 정책의 첫 변경/만료/초기화/비활성화 경계도 확인한다. 첫 관리자 변경 후 나머지5명 발급해 admin2/employee4인지 확인한다.
- 넘길 결과: 수언님에게 실제 로그인/첫 변경/계정 발급 응답·쿠키 조건·화면 오류. 오현님에게 미반영 정책과 실제 검증 범위.

## P1-2 · 문의 선저장·support 어댑터·본인 조회

- [ ] 연결 SPEC: BE-02·03, C01/C02.
- 생성 예정: `app/services/inquiries.py`, `app/repositories/inquiries.py`, `app/clients/support.py`; ask/requests 라우터; `tests/test_ask_adapter.py`, `tests/integration/test_request_ownership.py`.
- 작업: 서버 신원→공통 user, 문의 선저장→짧은 거래 종료→support 호출→검증된 응답 저장 순서로 만든다. 동일 키는 소유권부터 검사하고 원문 입력의 변조 재사용/실행중 재시도는 H04 검토 결과로 처리한다. DB 거래를 HTTP 대기 동안 유지하지 않는다.
- 확인 예정: `uv run pytest tests/test_ask_adapter.py tests/integration/test_request_ownership.py -q`. 두 직원의 타인 request_id403·결과 미노출·support 미호출, 본인 목록 분리, 입력400, 공통400 codes,5 route와 reason/timings 보존을 확인한다. timeout/잘못된 JSON은 Mock으로 검증하고 실제 서비스와 구분한다.
- 넘길 결과: 다혁님에게 실제 수신 페이로드·응답 보존/오류 결과, 수언님에게 본인 문의/재시도 사용법. H04 수치가 미확정이면 시간 목표 통과를 쓰지 않는다.

## P1-3 · 티켓·알림·관리자 처리와 실패 거래

- [ ] 연결 SPEC: BE-03·04, C05.
- 생성 예정: `app/services/tickets.py`, `alerts.py`, `storage_mode.py`, `app/repositories/tickets.py`, `alerts.py`; tickets/alerts 라우터; `tests/integration/test_ticket_idempotency.py`, `tests/test_storage_mode.py`.
- 작업: 내부 X-Api-Key와 세션을 분리하고 요청 직원 확인·문의 연결·T-번호 발급·UNIQUE 충돌 회수를 구현한다. 알림 거래를 분리하고 app/practice 한 대상만 호출한다. DLQ는 H06 채택/공통 반영 후 해당 API/테스트를 연결하며 그 전에는 테이블 준비로만 기록한다.
- 확인 예정: `uv run pytest tests/integration/test_ticket_idempotency.py tests/test_storage_mode.py -q`. 동일 key 동시2회→티켓1건·같은ID·신규201/중복200, 타인 key403, 내부키401, 티켓 commit 뒤 알림 실패에도 티켓 유지, 관리자 수정/직원403/없는 티켓404를 확인한다.
- 넘길 결과: 원민님에게 실제 저장 결과·재시도/중복·장애 경계·실제 관측 대상과 DLQ 미해결 상태. 상대로부터 실제 확인이 없으면 연결 완료로 표시하지 않는다.

## P1-4 · 실연결·재시작·측정·인계

- [ ] 연결 SPEC: BE-01~07, C01/C02/C05/C06/C07/C08/C09.
- 생성 예정: `tests/integration/test_persistence.py`, `tests/integration/test_web_flow.py`; 실제 실행 후 `Doc/SUBMISSION-NOTES.md`. 상대 코드/워크플로우·공통 사례 기대값은 수정하지 않는다.
- 확인 예정: `uv run pytest tests/integration/test_persistence.py tests/integration/test_web_flow.py -q`, volume 유지 postgres/backend 재시작 후 revision·문의/티켓·RAG 청크/검색 재확인. frontend→FastAPI→동일support, handoff→같은 저장대상, 유빈님 실제 색인/재색인을 각각 확인한다.
- 측정: SPEC 8절대로 품질·지연 원자료를 수집한다. 개발 호출 예산과 최종 검증을 구분한다. 최종 제출용 LLM 시나리오는 **3회 반복(`--repeat 3`)**하고 회차별 실패도 보고한다. 처리시간 측정은 최대5회 표본과 계산 방법을 남긴다. n8n push/test와 팀 VM 실행은 담당 사람이 수행한다.
- 넘길 결과: 각 상대에게 실제 입출력·Mock 여부·실패/재시험 보고서, 오현님에게 검증한 명령/버전/head·재시작/복구·정책 미반영·미실행을 전달한다. 설계/결과 취합은 본인 SUBMISSION-NOTES를 통해 하고 공통 docs는 직접 고치지 않는다.

## 단계별 실제 기록 방식

구현한 단계 아래에 실행일·요구/계약ID·생성파일·작업 디렉터리·명령·종료 상태·기대/실제 차이·Mock/실연결·마스킹한 증거 경로·남은 문제를 기록한다. 아직 실행하지 않은 단계는 체크하지 않는다. 실패가 있으면 같은 조건 재시험 결과도 남긴다. 미검토 제안을 ‘합의 완료’로 적거나 설치/시험 PASS를 미리 채우지 않는다.

## 참고

[주제](../../../docs/TOPIC.md) · [공통 API](../../../docs/API-CONTRACT.md) · [DB](../../../docs/DATA-AND-DB.md) · [협업](../../../docs/COORDINATION.md) · [팀 헌장](../../../docs/TEAM-CHARTER.md) · [전체 아키텍처](../../../docs/ARCHITECTURE.md) · [평가·시나리오 가이드](../../../docs/EVALUATION-GUIDE.md).
