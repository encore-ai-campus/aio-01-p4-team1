# 지혜님 · IMP-PLAN

[README](../README.md) → [TODO](TODO.md) → [SPEC](SPEC.md) → **IMP-PLAN**. 여기서 첫 미완료 단계부터 실행한다. 공통 기본안을 적용할 때 별도 승인을 기다리지 않는다. 누락 정책은 [HANDOFF](HANDOFF.md)에 제안으로 두고 그 정책과 무관한 작업을 계속한다.

**전체 상태: P0-1~2 및 P0-3 실행 기반·DB 접속 검증 완료. P0-4 이후의 테이블·확장 활성화·업무 저장·배포는 미실행.** 아래 단계별 실제 기록 외에는 구현 예정이다. 각 단계의 체크는 실제 확인 증거를 남긴 뒤에만 한다.

모든 아래 로컬 명령의 작업 디렉터리는 저장소 기준 `develop/jihye`다. 의존성이 없는 모델/Mock 시험부터 시작한다. DB 시험은 본인 전용 검증 DB, 실제 연결은 제공자 준비 후에 수행한다.

## 현재 작업 순서와 전제 조건 · 2026-11-05

현재 적용 기준은 [SPEC 1절](SPEC.md#1-적용할-기준--새로-선정하지-않음), 변경/상대 회신은 [HANDOFF](HANDOFF.md)의 현재 상태를 따른다. 공통 원문 출처는 SPEC에 남겨두며, 옛 실행 기록의 ‘미확정’ 설명은 작성 당시 이력으로만 읽는다.

1. **P0-2 보완:** 기존4bbbf49에서 빠진 context2,000자 제약과 시험을 추가한다. DB·외부 키·팀원 서비스는 필요하지 않다.
2. **개인 문서 정리:** SPEC에 확정 기준을 모으고 옛 제안/실행 이력을 구분한다. P0-3 이후는 계획 정리만 하며 이번에 구현하지 않는다.
3. **팀원 인계:** OpenAPI·fixture·저장 요청 예시와 미확정 항목을 HANDOFF에서 제공한다. 실제 공유 기준 커밋은 보완 커밋 생성 후 갱신한다. 문서 작성과 외부 전송·상대 확인을 구분한다.
4. **이번 지정 단계 P0-3:** DB 실행 기반과 실제 접속 검증까지 완료했다. 아래 실제 기록을 따른다. 다음 지정 구현은 P0-4이며 RAG 테이블/권한은 P0-5다. C05 ACK 확장은 팀장 승인 수신 상태로, 공통 문서 반영과 모델 보완은 별도 연결 작업이다.

| 단계 | 시작 전제 | 해당 단계 범위·완료 판정 | 다음 인계 |
| --- | --- | --- | --- |
| P0-2 보완 | 기존 모델·fixture 및 설치된 Python/uv, SPEC의 확정 입력 기준 | 아래 보완 파일/시험으로 제약·OpenAPI·미호출 검증. 실제 인증/HTTP/저장은 제외 | 수언/다혁/원민 모델 대조 |
| P0-3 | Docker/Compose·이미지 확보 가능, 본인 전용 검증 DB 비밀 설정·네트워크 준비 | postgres 부분·Alembic 기반·접속/인증 거절만. health와 schema 준비 구분, 업무/rag 테이블 생성은P0-4~5 | 유빈/오현 확장 가용성·접속 기반 |
| P0-4 | P0-3 접속 성공, migration 계정 권한 | vector/app/rag 및 업무 테이블·고유키·T시퀀스 적용/재실행. 계정seed 제외 | 원민 제약·nullable inquiry |
| P0-5 | 기본 스키마·관리 접속·DB 역할 준비 | rag 테이블·3072차원·최소 권한·가상 벡터 시험. 실제 문서 품질은 유빈 담당 | 유빈 DDL/head·색인/검색 권한 |
| P0-6 | 마이그레이션·직원 원본/Mock·bootstrap 전용 비밀값 | 직원6명·첫 관리자1명·재실행 덮어쓰기 없음. 실제 로그인은P1-1 | 오현 최초 기동/암호 제거 |
| P0-7 | DB/head/vector·backend 기반, FE 제공 여부 확인 | 이미지/Compose/backend readiness. 프론트가 없으면 DB/backend까지만 판정 | 수언 프록시·오현 실행법 |
| P1-1 | 직원/계정/세션 테이블·첫 관리자 | 실제 인증/회수·비밀번호·관리자 보호 경계. 추가 제안과 확정 정책 구분 | 수언 실제 쿠키/화면 시험 |
| P1-2 | 인증·inquiries·support Mock, 실제 연결 때 제공자 준비 | 소유권→선저장→짧은 거래 종료→HTTP→검증/저장. 공통400·timeout·재시도0 확인 | 다혁 C02·수언 본인 목록 |
| P1-3 | tickets/alerts/dlq·내부 인증·모드, H07 현재 상태 대조 | 저장·동시성·부분 실패·기본DLQ 구현. 미승인 ACK 확장 금지 | 원민 C05의 실제 ACK/건수 |
| P1-4 | 제공자·격리 시험 DB·공식 키트/관측 대상 확보 | 실연결·재시작·별도DB 백업/복원·재색인/반복/측정. Mock을 실측으로 집계하지 않음 | 유빈 복원검색·원민 보고서·오현 제출 |

각 단계의 파일·명령은 아래 기존 계획에 있다. 전제 미충족은 실제 실패/미실행으로 기록하고, 정상·오류·권한·경계 증거 없이 체크하지 않는다.

## P0-1 · FastAPI 골격과 공통 검증 타입부터

- [x] 연결 SPEC: BE-02·05, C01/C07의 P0-1 범위만 확인. 전체 요구 완료를 뜻하지 않음.
- 생성 예정: `pyproject.toml`, 설치 검증 후 `uv.lock`, `app/__init__.py`, `app/main.py`, `app/core/config.py`, `app/api/errors.py`, `app/api/routes/health.py`, `app/schemas/common.py`, `tests/test_contract_basics.py`.
- 작업: FastAPI/Pydantic·uvicorn·SQLAlchemy·psycopg·Alembic·pgvector 타입·HTTPX·비밀번호 해시 라이브러리와 시험 도구를 본인 프로젝트에 선언한다. config는 공통 변수 이름을 읽고 잘못된 SERVICE_MODE를 거절한다. secret 필드를 출력하지 않는다. liveness와 400 웹 오류 외형, 질문/ID/attempt 공통 제약 타입을 만든다. DB·n8n 없이 작동하는 골격부터 만든다.
- 확인 예정: `uv sync --dev` → `uv run pytest tests/test_contract_basics.py -q`. 공백 질문/501자/ID65자/attempt0·문자열/boolean 거절, 500자/64자/attempt1 수락, 검증 오류에 입력 비밀값이 없는지 확인한다. 요구가 정해지지 않은 세부 코드값은 H03 미확정으로 표시한다.
- 넘길 결과: 다음 단계에 설치된 버전·잠금 파일·공통 타입과 기대 오류 예시. 설치 성공이나 시험 통과는 실제 실행 후 기록한다.

### P0-1 실제 기록 · 2026-11-04

- 작업 위치: `develop/jihye`. 생성: `pyproject.toml`, `uv.lock`, `app/__init__.py`, `app/main.py`, `app/core/config.py`, `app/api/errors.py`, `app/api/routes/health.py`, `app/schemas/common.py`, 하위 패키지 `__init__.py` 4개, `tests/test_contract_basics.py`. 갱신: 본인 README·본 문서·HANDOFF.
- 예제 적용: FastAPI 라우터 등록·계층 분리를 참고했다. 예제의 startup create_all/자동 seed·JWT·InfluxDB는 가져오지 않았다. 후속 DB는 공통 app/rag·Alembic·명시적 bootstrap, 인증은 직원6명·관리자 발급·세션 기준을 따른다.
- `uv sync --dev`: 종료0, Python 3.12.15, 38개 resolve·35개 설치. FastAPI 0.162.0, Pydantic 2.14.2, pydantic-settings 2.16.2, Uvicorn 0.54.0, SQLAlchemy 2.1.8, psycopg 3.3.7, Alembic 1.20.1, pgvector 0.5.1, HTTPX 0.28.1, argon2-cffi 25.1.0, pytest 9.2.0. 정확한 전이 버전은 uv.lock에 고정.
- `uv run pytest tests/test_contract_basics.py -q`: 종료0, **30 passed, 1 warning in 3.20s**. 공백/501자·ID65자·attempt0/문자열/boolean/소수 거절, 500자·ID64자·attempt1 수락, 질문 trim, 잘못된 모드/URL 거절, 환경변수 이름, 비밀 설정 repr/직렬화 제외, malformed JSON/입력오류400·오류 입력 미노출, 401/403 등 오류 외형, liveness200·없는 readiness/가입404, 실제 OpenAPI 경로 범위를 확인했다.
- 시험 방식: 프로세스 내부 TestClient, 시험용 probe/오류 경로만 fixture에 추가. 외부 DB/n8n/data-api와의 연결·호출 Mock은 없으며 직원/관리자 인증 기능의 권한 시험도 아직 아니다. 오류 핸들러의 401/403 외형만 확인했다.
- 실제 기동: `uv run uvicorn app.main:app --host 127.0.0.1 --port 18000`의 startup 완료 확인. `curl --fail --silent --show-error --max-time 3 http://127.0.0.1:18000/health/live` 첫 실행은 샌드박스 소켓 차단으로 종료7(`Operation not permitted`), 같은 명령 권한 승인 후 종료0·`{"status":"ok"}` 확인. 검증 프로세스는 종료했다. 기본 실행 포트8000 계약은 유지한다.
- 남은 문제: Starlette 1.10.0 TestClient의 HTTPX 사용 폐기 예정 경고1건. 현재 시험 실패는 없으며 후속 시험 도구 갱신 시 호환성을 확인한다. `invalid_input` 등 세부 코드값은 골격 내부 임시값이며 JH-H03의 필드별 코드 제안은 미확정이다. 현재 검증 오류 예시는 HTTP400 `{"error":{"code":"invalid_input","message":"입력값을 확인해 주세요."}}`; 입력 원문·detail은 포함하지 않는다.
- 다음 연결: P0-2가 공통 Question/RequestId/Attempt·ErrorResponse와 앱 팩토리를 사용해 C01/C02/C05 모델·Mock을 연결한다. P0-3~5가 DB/pgvector를 준비한 뒤 유빈님·원민님에게 실제 연결 기반을 넘긴다. 수언님용 업무 OpenAPI는 아직 없고 상대 확인·VM 배포·n8n push/test도 미실행이다.
- 최종 경로/잠금 확인: `git diff --check` 종료0. 변경·미추적 파일은 모두 `develop/jihye/` 안이며 staging 없음. `uv lock --check --offline` 첫 실행은 기본 uv 캐시 읽기 전용으로 종료2, 같은 명령 권한 승인 후 종료0(`Resolved 38 packages in 4ms`). 잠금 파일과 프로젝트 선언이 일치한다.

## P0-2 · 요청/응답 모델과 계약 Mock

- [x] 연결 SPEC: BE-01~04, C01/C02/C05의 P0-2 모델·시그니처·Mock 범위만 확인. 실제 업무 기능 완료는 아님.
- 생성 예정: `app/schemas/auth.py`, `users.py`, `support.py`, `inquiries.py`, `tickets.py`, `alerts.py`; `app/api/deps.py`; `app/api/routes/auth.py`, `users.py`, `ask.py`, `requests.py`, `tickets.py`, `alerts.py`; `tests/test_api_models.py`, `tests/test_support_contract.py`, `tests/conftest.py`.
- 작업: SPEC 3~5절 모델과 라우터 시그니처를 연결한다. 응답에서 비밀 필드를 제외하고 support의 reason/timings와 추가 응답 필드를 보존한다. 미구현 라우터를 성공 응답으로 위장하지 않는다. Mock은 tests 안의 HTTP transport/fixture로 만들며 다른 역할의 워크플로우를 복제하지 않는다.
- 확인 예정: `uv run pytest tests/test_api_models.py tests/test_support_contract.py -q`. 웹14 operation(13개 경로)·내부3개 API의 모델을 검증하고 정상5 route·400 codes passthrough·요청ID 불일치/잘못된 응답 검출·원문 암호 미직렬화를 확인한다. OpenAPI는 `app.openapi()` 결과를 시험에서 검사하고 외부 호출을 하지 않는다.
- 넘길 결과: 수언님에게 확정 계약 필드의 OpenAPI/예시, 다혁님에게 세션→user 변환 입력과 공통 응답 fixture, 원민님에게 /tickets·/alerts 예시. H03/04의 미확정 세부는 ‘제안’으로 함께 표시하며 실제 연결 확인으로 쓰지 않는다.

### P0-2 실제 기록 · 2026-11-04

> 보존한 과거 실행 기록이다. 이때 빠진 context 상한과 미확정 분류 오류는 아래2026-11-05 보완 기록으로 정정한다. 당시75개 통과 결과 자체를 변경하지 않는다.

- 작업 디렉터리: `develop/jihye`. BE-01~04 / C01·C02·C05의 계약 모델·Mock만 구현. 예제의 APIRouter/Depends/response_model 계층을 참고하고 우리 세션·공통 응답 전체 보존·내부 키 경계를 적용했다. DB·워크플로우·실제 서비스는 생성/호출하지 않았다.
- 생성 파일: `app/schemas/{auth,users,support,inquiries,tickets,alerts}.py`, `app/api/deps.py`, `app/api/routes/{auth,users,ask,requests,tickets,alerts}.py`, `tests/conftest.py`, `tests/test_api_models.py`, `tests/test_support_contract.py`. 수정: `app/main.py`, `app/api/errors.py`, `app/schemas/common.py`, `tests/test_contract_basics.py` 및 본인 README·SPEC·TODO·IMP-PLAN·HANDOFF. 의존성 추가 없음.
- 계획 본문의 웹12/내부2 표기는 최신 공통 API와 다르다. 실제 적용은 웹14개 operation(13개 경로)·내부3개(`/tickets`, `/alerts`, `/dlq`)이며 liveness 포함18개 operation이다. 공통 파일은 수정하지 않았다.
- OpenAPI: 실제 `app.openapi()`의 경로·요청/응답 참조·쿠키/내부키 securitySchemes·계정 생성201·티켓 신규201/중복200·검증400(기본422 제거)을 시험했다. `/api/ask`의400은 웹 ErrorResponse와 공통 codes 본문 두 형식을 표시한다. 미구현501을 문서에 표시하고 실제 라우터도 성공으로 위장하지 않는다.
- 첫 `uv run pytest tests/test_api_models.py tests/test_support_contract.py -q`: 종료0, **44 passed, 1 warning in 1.30s**. 이후 중복 티켓200 시험1개와 OpenAPI codes/첫 변경 코드 검증을 보강했다.
- 최종 `uv run pytest -q`: 종료0, **75 passed, 1 warning in 2.59s**. 기존 P0-1 30개+P0-2 45개. warning은 기존 Starlette TestClient HTTPX 폐기 예정 경고1건이다. 최초 실행 실패나 숨긴 실패는 없다.
- 검증: 웹14·내부3 시그니처의 성공 응답은 tests fixture 서비스로만 확인. 계정/비밀번호/해시 미직렬화, strict bool/정수·질문 경계, patch 생략/null 구분, 관리자 dependency·첫 변경403, 실제 dependency의 쿠키/키 누락401 및 임의 값501, 실제 로그인501·쿠키 미발급을 확인했다. 활성/만료/회수 검사는 실제 세션이 없어 미실행이다.
- support Mock: HTTPX MockTransport로5 route·필수7필드·reason/timings 및 중첩/상위 추가 필드 보존, 미제공 선택 필드 미삽입, 세션 fixture 이름→user·channel=web, 입력 user/dept/role 무시, 공통400 codes 본문 보존, 요청ID 불일치·잘못된 JSON/타입/route·유한하지 않은 score 거절, 잘못된 웹 입력의 서비스/HTTP 호출0회를 확인했다. 실제 HTTP 클라이언트·문의 저장은 P1-2이며 이번 결과는 그 구현 완료 증거가 아니다.
- 미확정: H03 목록 DTO·Security 세부 타입·patch 의미는 초안. 미지 입력 필드는 무시하며400 거절 정책은 채택하지 않았다. context2000자 제한·필드별 오류코드도 추가하지 않았다. 새 비밀번호12자·3종은 모델 검사, 본인 이름/로그인ID 포함 검사는 P1 서비스에서 연결해야 한다. support 응답 미유효를 성공으로 반환하지 않는 시험은 있으나 저장소 미구현이라 DB 저장 실패 검증은 아니다.
- 다음: 수언님은 `/openapi.json`과 시험의 요청/응답 예시로 화면 Mock 개발 가능. 다혁님은 `SupportRequest/Response` 및 tests fixture의5 route/400 예시를 대조. 원민님은 `/tickets`·`/alerts`·`/dlq` 요청/응답 모델 확인 가능. 실제 저장·멱등·개인정보 마스킹·키 검증·외부 호출은 P1, DB 기반은 다음 P0-3~5다. 유빈님 data-api 응답/인증 및 C06 실저장은 이번에 확인하지 않았다. 상대 확인·메시지 전송·VM 배포·n8n push/test 없음.
- 최종 검사: `git diff --check` 종료0. `git status --short`로 수정·미추적 경로가 모두 `develop/jihye/` 내부임을 확인했고 `git diff --cached --name-only`는 빈 결과였다. 커밋·push는 수행하지 않았다.

### P0-2 보완 · 2026-11-05

- [x] 기존 모델·공통 확정 기준의 누락 보완 및 개인 문서 정리. P0-3 이후 구현은 하지 않음.
- 전제/입출력: SPEC의 context 최대2,000자 기준, 기존 nullable/생략 호환 유지. DB/n8n·실제 비밀값 불필요. UTF-8 byte 수가 아닌 문자열 문자 수로 검사하고 trim/절단하지 않는다.
- 수정: `app/schemas/common.py`의 Context 타입, `app/schemas/support.py`의 AskRequest/SupportRequest, `tests/test_support_contract.py`. 문서: README·AGENTS·TODO·SPEC·본 계획·HANDOFF·migrations/README·deploy/README.
- 변경 전 결함: 평가§3.1에 상한이 있지만 두 모델이 context2,001자를 수락했고 개인 문서는 미확정으로 오기했다. 공통 계약 변경 없이 개인 구현/문서를 바로잡았다.
- 실제 명령: `uv run pytest -q`(develop/jihye), 종료0, **100 passed, 1 warning in 7.78s**. 기존75개+context 회귀25개. 기존 Starlette TestClient의 HTTPX 폐기 예정 경고1건 유지.
- 확인: 두 모델에서 빈 문자열/공백/한글2,000자/생략/null 수락,2,001자 및 잘못된 타입 거절. 웹2000자→Mock에 그대로 전달, 초과/잘못된 타입400·서비스/HTTP호출0, 웹 응답에 입력 미포함, AskRequest OpenAPI 및 SupportRequest JSON Schema의 maxLength2000 확인. 실제 세션·네트워크·DB 시험은 없음.
- 문서 정리: 공통 대조기준db14b79와 현재 적용표, 확정/구현 상태 분리, 단계 전제·완료·인계, 수동 백업/복원 확인, 원민7/7 회신 및 미확정 H07 기록. 과거 제안/시험은 보존했다. 문서 치환 준비 중 문자열 대조2회가 실패했으나 각 사전 검사 단계에서 종료되어 해당 명령은 파일을 쓰지 않았고 수정 후 정상 적용했다. 시험 실패는 없음.
- 넘길 결과: HANDOFF의 현재 인계 패키지·요청/응답 예시를 보완 커밋과 함께 공유한다. 아직 보완 커밋·push·외부 메시지 전송 없음. 원민7/7은 기존4bbbf49에 대한 전달받은 회신이며 이번 변경에 대한 상대 재확인은 아님.
- 최종 확인: 개인 문서8개의 로컬 링크87개 대상 파일 존재 확인(누락0), `git diff --check` 종료0. 변경11개 파일은 모두 develop/jihye 내부이고 staging 없음. 공통/상대 파일 수정·DB 기동·실제 API 호출·P0-3 구현은 하지 않았다.

## P0-3 · DB 컨테이너와 마이그레이션 실행 기반

- [x] 연결 SPEC: BE-05·06, C06/C07의 P0-3 실행 기반·접속 범위만 확인. 테이블·활성화·저장 완료는 아님.
- 생성 예정: `deploy/compose.yaml`의 postgres 부분, `deploy/.env.example`, `migrations/alembic.ini`, `env.py`, `script.py.mako`, `app/db/base.py`, `session.py`, `tests/integration/test_db_connection.py`.
- 작업: [deploy 안내](../deploy/README.md)의 서비스명/포트를 그대로 사용하고 pgvector 포함 이미지·named volume·healthcheck를 준비한다. 실제 설치 검증 후 태그/digest를 기록한다. Alembic 대상은 app/rag만, URL은 DATABASE_URL에서 읽는다. 공개 postgres 포트나 루트 설정을 만들지 않는다.
- 확인 예정: 비밀 파일 준비 후 `docker compose --env-file deploy/.env -f deploy/compose.yaml config --quiet`, `up -d postgres`, `ps`를 각각 수행한다. `uv run pytest tests/integration/test_db_connection.py -q`로 본인 검증 DB 접속과 잘못된 자격증명 거절을 확인한다. pg_isready와 schema 적용 확인을 구분한다.
- 넘길 결과: 다음 단계/유빈님에게 검증한 이미지·확장 가용성·접속 방법(비밀 제외), 오현님에게 실제 네트워크/충돌 여부. 미가용 서비스는 미실행으로 남긴다.

### P0-3 실제 기록 · 2026-11-05

- 전제/범위: 개인 SPEC·계획과 공통 기준을 읽고 진행했다. 폴더 내 깨끗한 fdcd265에서 시작했으며 Docker/Compose·캐시 이미지를 확인했다. 예제의 volume/health 구조만 참고했고 host network·InfluxDB·자동 create_all/seed는 가져오지 않았다. 이번 출력은 전용 DB 접속과 빈 Alembic 기반이다. 실제 업무/rag DDL은 P0-4~5에 남겼다.
- 생성: `deploy/compose.yaml`, `compose.check.yaml`, `.env.example`, `init_db_env.py`, `check_db.py`; `app/db/__init__.py`, `base.py`, `session.py`; `migrations/alembic.ini`, `env.py`, `script.py.mako`, `versions/.gitkeep`; `tests/test_db_basics.py`, `tests/integration/test_db_connection.py`. pyproject에는 integration marker만 추가했다. helper는 비밀 설정 생성과 Docker 네트워크 시험을 재현하기 위한 P0-3 보조 도구다. 실제 `deploy/.env`는 Git 제외·권한600이며 값은 문서에 남기지 않는다.
- 환경: Docker Compose v5.6.0, 기존 postgres의 호스트5432/55432 사용 확인. 기본 공개 포트를 바꾸거나 기존 DB를 재사용하지 않고 프로젝트 `oke-jihye-p0`, 서비스 `postgres`, 컨테이너 `oke-jihye-p0-postgres-1`, 볼륨 `oke-jihye-p0_postgres_data`와 전용 네트워크로 격리했다. 호스트 ports 설정 없음. backend/n8n/data-api/프론트는 기동/수정하지 않았다.
- 검증한 DB 이미지: `pgvector/pgvector:pg16@sha256:ccc6e83d6e35e931dc7c5def2022729d5a6c370318d099181995567ff1fb4d6b`(amd64). 실제 PostgreSQL16.15, 사용 가능한 vector0.8.6. 별도 시험 컨테이너는 Python3.12 slim digest를 compose.check.yaml에 고정했다. 실제 extension CREATE는 하지 않았다.
- `uv run python deploy/init_db_env.py`: 첫 sandbox 실행은 uv 캐시 읽기 전용으로 종료2, 허용된 재실행은 종료0. private 설정을 새로 만들었으며 재실행은 기존 파일을 덮어쓰지 않는다. `git check-ignore deploy/.env`와 `stat`으로 제외·권한600을 확인했다.
- `uv run alembic -c migrations/alembic.ini history`와 `heads`: sandbox 캐시 제한 후 재실행 각각 종료0·빈 결과. revision이 없는 P0-3 상태이며 이를 head 적용 완료로 부르지 않는다. `uv run pytest tests/test_db_basics.py -q` 첫 검증8개 통과 후 출력 마스킹 회귀1개를 추가했다. 기본 접속드라이버는 postgresql+psycopg이며 실행 시 DATABASE_URL을 읽고 앱 시작에는 DB 접속을 강제하지 않는다.
- `docker compose --env-file deploy/.env -f deploy/compose.yaml config --quiet`: 종료0. `up -d --wait postgres`: 종료0·healthy. `ps`의5432/tcp는 내부포트이고 호스트 publish가 아니다. pg_isready만으로 로그인 성공을 판정하지 않았다.
- 최초 실제시험 `uv run python deploy/check_db.py`: 호스트에서 bridge IP로 접근해 5개 모두 시간 초과로 실패(종료1). 잘못된 암호 시험도 인증 거절이 아니라 연결 실패였으므로 통과로 집계하지 않았다. 실제 호스트/daemon 네트워크 경계 때문에 compose 네트워크의 시험 컨테이너로 경로를 수정했다. 비밀번호 거절은 SQLSTATE 유무뿐 아니라 인증 거절 메시지도 검사하도록 보강했다.
- 위 최초 실패의 pytest 상세 traceback에 자동생성 검증용 암호가 노출됐다. 그 값은 기록하지 않았고 전용 DB의 암호와 private env를 교체했다. 같은 볼륨으로 해당 컨테이너만 재생성해 설정을 일치시켰다. 이후 check_db.py는 subprocess 출력을 캡처해 URL/암호를 가리고 짧은 traceback을 사용한다. 출력 마스킹 회귀 시험을 추가했다. 다른 서비스의 비밀값은 조회/변경하지 않았다.
- Docker 안 재시험1회는 읽기 전용 시험 컨테이너에 임시 디렉터리가 없어 수집 전에 실패했다. `/tmp` tmpfs를 추가한 다음 같은 `uv run python deploy/check_db.py`는 종료0, **5 passed, 1 warning in 0.82s**였다.
- 실제 DB 시험5개: SELECT1·Session·현재DB 대조, vector 가용성 및 미활성화, app/rag 미생성, 잘못된 비밀번호의 실제 거절, Alembic current의 빈 revision을 확인했다. public.alembic_version은 후속 마이그레이션 bookkeeping 위치이며 P0-3 current 조회는 만들지 않았다. autogenerate 반영 대상은 app/rag만이다.
- 최종 `uv run python deploy/check_db.py --all`: 종료0, **114 passed, 1 warning in 4.11s**(기존100 + DB기반9 + 실제DB5). 기존 Starlette TestClient HTTPX 폐기 예정 경고1건 유지. 합성 Mock 시험과 실제 DB 시험을 구분하며 업무/RAG 저장·임베딩·n8n 통합 통과를 뜻하지 않는다. 두 Compose 파일을 합친 config 검사도 종료0이었다.
- 남은 상태: 전용 DB는 현재 healthy로 남기고 volume을 유지했다. 업무/rag 테이블·vector 활성화·grants·직원/계정·API 저장·readiness·VM 배포·공식flow.py 검사는 미실행이다. 기존 서비스/볼륨은 변경하지 않았다. 같은 DB를 재시작한 뒤 업무 기록 유지 시험은 P1-4에서 수행한다.
- 다음: P0-4가 확장/app/rag와 업무 테이블, P0-5가 RAG 테이블·접속 권한을 준비한다. 유빈님·다혁님에게 P0-3의 접속 기반 완료와 실저장 미준비를 구분해 공유한다. 준비 예상 시각은 후속 단계의 실제 착수/장애 확인 뒤 전달하며 임의 확정하지 않는다. 상대별 인계 자료는 HANDOFF의 P0-3 절에 정리했다. 커밋·push·외부 메시지 전송은 하지 않았다.
- 최종 검사: `uv lock --check --offline` 종료0(38개,2ms), `git diff --check` 종료0. 수정/신규22개 경로가 모두 develop/jihye 내부, 로컬 문서 링크87개 대상 존재, 변경 파일에 private DB URL/암호 원문이 없음을 값 출력 없이 검사했다. staging 없음. deploy/.env는 추적되지 않고 Git 제외·권한600이다.

## P0-4 · 확장→업무 테이블 생성

- [x] 연결 SPEC: BE-01·03~05, C05/C06. 전용 검증 DB의 DDL·제약 확인까지 완료; 업무 API 저장 연결은 후속 단계.
- 생성 예정: `migrations/versions/0001_extensions_and_schemas.py`, `0002_app_tables.py`, `app/db/models/employees.py`, `users.py`, `sessions.py`, `inquiries.py`, `tickets.py`, `alerts.py`, `dlq.py`와 모델 등록 파일; `tests/integration/test_migrations.py`.
- 작업: [migrations 안내](../migrations/README.md)의 타입/NULL/기본값/FK/고유키를 적용한다. vector·app/rag 생성 후 employees→users→sessions, inquiries→tickets→alerts, dlq 순으로 만든다. T-2001 별도 시퀀스와 request_key UNIQUE를 둔다. 계정 seed를 DDL 안에 섞지 않는다.
- 확인 예정: `uv run alembic -c migrations/alembic.ini history`, `upgrade head`, `current`를 순서대로 수행한다. `uv run pytest tests/integration/test_migrations.py -q`로 카탈로그를 확인하고 같은 upgrade 재실행이 무변경인지 검사한다. 자동 생성 결과의 확장·스키마·제약은 직접 검토한다.
- 넘길 결과: 원민님에게 티켓/알림/DLQ 구조·중복 제약·nullable inquiry, 다음 단계에 적용 revision과 실제 오류. H02 추가 보안 컬럼은 기본 revision에 미승인으로 넣지 않는다.

### P0-4 실제 기록 · 2026-11-05

- 전제: P0-3의 격리된 `oke-jihye-p0` DB와 마이그레이션 실행 계정을 사용했다. 개인 README·SPEC·계획·HANDOFF 및 deploy/migrations 안내, 공통 API/DB 계약을 대조했다. 유빈님 청크 표본은 P0-5 연결 입력으로만 사용한다.
- 구현: `0001`에서 vector 확장과 app/rag 스키마를 만들고, `0002`에서 업무 테이블 7개(employees, users, sessions, inquiries, tickets, alerts, dlq), FK·고유/검사 제약·조회 인덱스·T-2001 전용 시퀀스를 만들었다. `app/db/models/`에 대응 모델을 등록하고 `deploy/check_db.py`에 마이그레이션 검사 명령을 추가했다. 계정 seed와 RAG 테이블/권한은 후속 범위다.
- 실제 적용: `uv run python deploy/check_db.py --alembic history`는 단일 `0001→0002` 체인, `heads`는 `0002 (head)`였다. 적용 전 `current`는 비어 있었고, `--alembic upgrade`는 종료 0, 적용 후 `current`는 `0002 (head)`였다.
- 실제 검사: `uv run python deploy/check_db.py --migrations` 종료 0, 40개 통과. DB 카탈로그의 확장·스키마·컬럼/NULL/타입/기본값·FK/UNIQUE/CHECK·인덱스, 합성 자료의 중복/거절 및 재적용 무변경을 확인했다. `--all` 종료 0, 전체 155개 통과·기존 Starlette/httpx 폐기 예정 경고 1건. 검사 기록은 실제 전용 DB 결과이며 실서비스 저장 성공이 아니다.
- 범위/다음: rag 스키마는 존재하지만 `rag.documents/chunks`, `vector(3072)` 컬럼과 런타임 role/grant는 P0-5에서 만든다. 유빈님 청크 `chunk_no`는 0부터이고 추적값은 metadata JSONB에 담는 방향으로 대조한다. `complete/partial/rejected`는 청킹 준비 상태라 기본 DDL 컬럼으로 추가하지 않는다. 원민님에는 티켓/알림/DLQ 제약과 실제 저장 API 미연결을 구분해 공유한다. 외부 전송·commit·push는 이 기록에서 주장하지 않는다.

## P0-5 · RAG 테이블·인덱스·접속 권한

- [x] 연결 SPEC: BE-05·06, C06. 전용 DB의 DDL·그룹 역할 권한 확인까지 완료; 실제 서비스 로그인·색인은 미연결.
- 생성 예정: `migrations/versions/0003_rag_tables.py`, `0004_indexes_and_grants.py`, `app/db/models/rag.py`, `tests/integration/test_pgvector.py`, `tests/integration/test_db_permissions.py`.
- 작업: rag.documents/chunks·vector(3072)·all/it·FK·UNIQUE를 적용하고 FK/조회 인덱스를 만든다. 정확 cosine·score=1-distance·top_k3 기준을 유지한다. 마이그레이션/업무/색인/검색 권한을 구분한다. 필요한 DB role은 관리 권한으로 비밀 입력을 사용해 준비하고 암호를 revision에 넣지 않는다.
- 확인 예정: `uv run alembic -c migrations/alembic.ini upgrade head`, `heads`, `current`로 단일0004 head를 확인한다. `uv run pytest tests/integration/test_pgvector.py tests/integration/test_db_permissions.py -q`로3072차원 수락/3071거절·권한 누락 거절·정확 검색 전 all/it 필터·권한별 쓰기/DDL 거절을 확인한다. 가상 벡터 시험은 실제 모델 품질 시험과 분리한다.
- 넘길 결과: 유빈님에게 head·열/차원·모델·권한·인증 주입 방법과 가상 벡터 검사 결과. 유빈님이 실제 문서/임베딩/재색인을 구현한다. HNSW·다른 모델·차원은 추가하지 않는다.

### P0-5 실제 기록 · 2026-11-05

- 시작: P0-4 `0002 (head)` 전용 검증 DB와 깨끗한 작업 트리에서 시작. README·AGENTS·TODO·SPEC·HANDOFF·IMP-PLAN, 공통 API/DB와 migrations/README 기준을 확인했다. 유빈님 청크 표본의 0부터 시작하는 `chunk_no`와 metadata 추적값을 입력으로 대조했다.
- 구현: `0003`에서 `rag.documents/chunks`, `vector(3072)`, all/it CHECK, FK, `(document_id,chunk_no)` UNIQUE 및 0 이상 CHECK를 만들었다. `0004`에서 FK/권한 조회 인덱스와 `oke_app`, `oke_rag_index`, `oke_rag_search`의 비밀번호 없는 NOLOGIN 그룹 역할을 생성하고 schema/table/sequence 및 미래 객체 기본 권한을 구분했다. 마이그레이션 소유자 계정은 런타임에 사용하지 않는다. 문서 권한의 직원별 적용은 검색 SQL에서 별도 수행해야 한다.
- 적용: 전용 Compose DB에서 `--alembic heads`가 `0004 (head)`임을 확인한 뒤 `--alembic upgrade` 종료0, `--alembic current`가 `0004 (head)`임을 확인했다. 처음 `metadata` 예약 속성 경고가 나와 Python 속성만 `metadata_`로 고치고 실제 DB 컬럼명은 `metadata`로 유지했다.
- 검증: `uv run python deploy/check_db.py --all` 종료0, **158 passed, 1 warning**. 기존 P0-4 카탈로그/멱등성 검사를 유지했고 실제 DB에서 RAG 테이블/3072차원·3071차원 거절, 미지 권한 거절, 0번 청크, 가상 벡터의 정확 cosine `score=1-distance`·all/all+it 사전 필터, 역할별 SELECT/INSERT/DDL 거절 및 시퀀스 권한을 확인했다. 검증용 문서는 거래 rollback으로 제거했다. 경고1건은 기존 Starlette/httpx 폐기 예정 경고다.
- 경계: NOLOGIN 역할의 ACL은 실제 DB에서 확인했지만, 서비스별 LOGIN 계정/비밀·n8n Credential·실제 임베딩·data-api 원본·재색인·HTTP 검색은 확인하지 않았다. 운영 접속 자격증명 연결은 오현님 관리의 비밀 설정과 유빈님 실제 Index/Search 연결 때 검증한다. `complete/partial/rejected`는 청킹 준비 상태여서 컬럼으로 추가하지 않았다. HNSW/다른 모델도 미추가다. 상대에게 전송하거나 실제 동의를 받았다고 기록하지 않는다.

## P0-6 · 직원 seed와 첫 관리자

- [x] 연결 SPEC: BE-01·05, C01/C07. Mock 수집・전용 DB 검증 완료, 실제 원본/VM 실행은 미실행.
- 생성 예정: `app/clients/data_api.py`, `app/cli.py`, `app/services/bootstrap.py`, `app/core/security.py`, `tests/test_bootstrap.py`, `tests/integration/test_bootstrap_db.py`.
- 작업: SPEC 6절의 원본6명 대조→직원만 적재→명시한 IT팀 직원의 첫 계정 생성 순으로 만든다. GET /employees를 Mock으로 먼저 확인한다. bootstrap은 BOOTSTRAP_ADMIN_PASSWORD만 읽고 기존 계정 해시/역할을 덮어쓰지 않는다. 명령 이름은 아래와 같이 구현한다.
- 확인 예정: `uv run pytest tests/test_bootstrap.py tests/integration/test_bootstrap_db.py -q`. 정상6명, 누락/추가/부서불일치, 비IT bootstrap 거절, 암호 누락, 재실행 생성0건·기존 해시 유지, 비밀번호 미출력을 확인한다.
- 실제 seed 예정 명령: `uv run python -m app.cli seed-employees` 후 직원6명 확인. 이어 `uv run python -m app.cli bootstrap-admin --employee-name <제공 IT팀 이름> --login-id <선택한 ID>`를 실행하는 인터페이스다. `<…>`는 비밀을 제외한 선택값으로 치환하고 암호 인자는 만들지 않는다.
- 넘길 결과: 오현님에게 최초1회/재실행 조건과 일회성 암호 제거 절차. 나머지5명 발급은 P1-1 관리자 API에서 수행한다. 세션·비밀번호 P0/P1 규정·최후 관리자 보호는 SPEC 현재 기준을 적용하고 추가 운영 제안만 구분한다.

### P0-6 실제 기록 · 2026-11-05

- 재확인 기록: 기존 P0-6 구현을 요청 문서와 다시 대조한 뒤 `uv run python deploy/check_db.py --all`을 재실행했다. 종료0, **180 passed, 1 warning in 10.53s**. 기존 Starlette/httpx 경고1건이며 원본 API·VM 실행 결과는 아니다. 코드 추가 수정 없이 재확인했고, 기록 전 저장소 전체 `git status --short`와 `git diff --name-only`는 빈 결과였다. 이번 기록 수정은 `develop/jihye/Doc/IMP-PLAN.md`에만 한정한다. 다음 구현은 P0-7, P0-6의 실제 원본/VM seed·첫 관리자 적용은 오현님 환경 확인 후 별도로 연결한다.

- 구현: 직원 수집 클라이언트·bootstrap 서비스·CLI·Argon2id 보안 모듈과 테스트를 추가했다. 서버 시작과 공개 API에서 자동 seed/계정 생성은 하지 않는다. 정확한6명/부서를 검증하고 누락·추가·중복·부서 변경·기존 DB 불일치를 거절한다. seed는 직원만 적재한다.
- 원본 경계: 지원 형태는 Mock `{employees:[{name,dept,...}]}`이며 실제 응답 확인이 아니다. 실제 인증을 추정하지 않고 `DATA_API_EMPLOYEES_AUTH_HEADER`에 확인된 헤더 이름을 명시하도록 했다. DATA_API_URL/KEY와 해당 명령 전용 설정이 없으면 실행을 거절한다. 실제 data-api 호출은 미실행이다.
- 관리자: seed 완료·지정 IT직원·빈 계정 집합에서만 첫 admin을 만든다. BOOTSTRAP_ADMIN_PASSWORD/SESSION_SECRET 누락은 DB 작업 전 실패한다. 12자/3종/본인 이름·login_id 포함 금지와 Argon2id를 적용했다. 동일 활성 관리자 재실행은 생성0건·해시/역할 보존, 다른 기존 계정은 복구/승격하지 않고 거절한다. 동일 advisory 거래 잠금으로 seed/bootstrap을 직렬화했으며 동시 실행 자체의 시험은 미실행이다.
- 실제 검사: `uv run python deploy/check_db.py --all` 종료0, **180 passed, 1 warning in 12.36s**. 새22개는 단위/가짜HTTP16개와 실제 PostgreSQL6개다. 원본 불일치·HTTP/형식 오류·필수비밀·오류의 비밀값 비노출·암호 검증·적재/재실행·관리자 경계·해시 보존을 확인했다. 기존 Starlette/httpx 경고1건 유지. 실제 DB 검사는 rollback으로 상시 직원/계정을 만들지 않았다.
- 다음: 실제 employees 응답/인증과 VM DB가 확인된 뒤 seed→6명 대조→지정 IT직원 bootstrap→첫 관리자1명 확인 순으로 적용하고 일회성 암호를 비밀 저장소에서 제거한다. 로그인/세션/첫 변경/나머지 계정 발급은 P1-1, 배포/readiness는 P0-7이다. VM 적용·외부 전송·commit/push는 수행하지 않았다.

## P0-7 · backend 이미지·준비 상태·배포 묶음

- [x] 연결 SPEC: BE-05·06, C07. 전용 로컬 DB/backend 빌드·기동·readiness 확인. frontend/실제 n8n·data-api/VM 전체 연결은 미실행.
- 생성 예정: `deploy/backend.Dockerfile`, `deploy/.dockerignore`; `deploy/compose.yaml`의 backend/frontend/n8n/data-api 연결; `app/api/routes/health.py` 준비 상태 확장; `tests/integration/test_readiness.py`.
- 작업: [deploy 안내](../deploy/README.md)의 컨테이너/로컬 포트·build context·비밀 제외·프로세스/DB 준비 상태를 적용한다. backend는 본인 폴더를 context로 사용한다. frontend Dockerfile·프록시는 수언님 소유이며 아직 없으면 DB/backend까지만 확인한다. n8n/data-api 기존 환경 재사용 여부·실제 모드를 기록한다.
- 확인 예정: `docker compose --env-file deploy/.env -f deploy/compose.yaml build backend`, DB 적용 후 `up -d backend`, `curl --fail http://127.0.0.1:8000/health/ready`, `uv run pytest tests/integration/test_readiness.py -q`. DB 중단/미적용 revision/vector 누락을 준비 완료로 표시하지 않고 오류에 비밀값을 노출하지 않는지 확인한다. 전체 웹/AI 기능 완료 확인은 P1이다.
- 넘길 결과: 오현님에게 검증한 설치/기동/마이그레이션/seed/health 순서·버전·모드·서비스 대상·남은 의존성. 배포나 VM 회귀를 완료했다고 기록하지 않는다.

### P0-7 실제 기록 · 2026-11-05

- 범위: 예제에서 이미지/health 구조만 참고하고 자동 create_all/seed는 사용하지 않았다. 기존 Doc/IMP-PLAN 재확인 기록 변경을 보존했다. frontend 폴더에 빌드 파일이 없어 본 계획의 허용 범위인 DB/backend까지 구현했다. 기존 n8n/data-api 컨테이너는 실행 중이나 네트워크 연결·Credential·워크플로우는 이번에 변경/실호출하지 않았다.
- 파일: `deploy/backend.Dockerfile`, Dockerfile 전용 ignore와 deploy/.dockerignore, uv.lock에서 내보낸 `requirements.lock`, Compose backend, 전용 로컬 계정 준비 도구 `init_backend_env.py`, `app/services/readiness.py`, health 라우터와 tests/integration/test_readiness.py. 마이그레이션 계정을 런타임에 쓰지 않기 위해 `0005_readiness_grant.py`에서 oke_app에 public.alembic_version SELECT만 추가했다. 기존 적용 revision은 덮어쓰지 않았다. 실제 로컬 revision은0005다.
- 준비 확인: readiness는 DB 접속·현재 코드의 단일 head·vector 확장 및 embedding vector(3072)를 검사해200/503을 반환한다. scope=database로 한정하며 n8n/data-api/로그인 기능 완료를 의미하지 않는다. liveness는 DB와 독립이다. 설정/DB 오류의 URL·암호·예외 원문을 응답하지 않는다.
- 빌드: Python3.12 slim 기존 digest를 사용하고 uv.lock의 고정 의존성으로 `docker compose --env-file deploy/.env -f deploy/compose.yaml build backend` 성공. uv export 최초 sandbox 실행은 캐시 쓰기 제한으로 실패한 뒤 허용 재실행으로 성공했다. 빌드 시 pip root 경고는 설치 단계이며 실제 실행은 UID10001이다.
- 런타임: 전용 DB에 LOGIN `oke_backend_login`과 oke_app 연결을 생성했다. 비밀값은 Git 제외·권한600의 deploy/.env.backend에만 저장했다. migration 관리자 URL과 분리했고 실제 컨테이너의 current_user·역할 생성 권한 없음·비밀파일/호스트.venv 미포함을 확인했다. 이 도구는 전용 로컬 DB용이며 VM에는 관리자가 별도 계정/비밀을 준비한다.
- 실제 HTTP: 기본8000 노출 시 Docker 포트 연결 오류로 종료1. 다른 서비스 변경 없이 `BACKEND_PORT=18000`으로 재기동해 backend/postgres healthy를 확인했다. ready200 → 전용 DB 중지 후 ready503·live200 → 같은 volume으로 DB 재기동 후 ready200을 확인했다. 현재 로컬127.0.0.1:18000이고 기본 설정은8000이다. 기존 서비스는 변경하지 않았다.
- 검사: `uv run python deploy/check_db.py --all` 최종 종료0, **188 passed, 1 warning in 7.70s**. 새readiness8개와 기존180개다. 기존 OpenAPI/health 시험이 readiness 미존재를 기대해 최초2개 실패, 그 뒤 DB 환경변수 상속으로1개 실패했다. 새경로/설정없음 조건을 명시해 수정 후 재시험했다. revision/vector 누락·차원 불일치는 가짜DB 응답, 접속/권한·중지/회복은 실제 전용DB/HTTP 결과로 구분한다. Starlette/httpx 기존경고1건 유지.
- 다음: 오현님께0005 포함 적용순서·이미지/환경 이름·runtime 계정 분리·health 범위를 인계한다. 유빈님 DB LOGIN·실원본/임베딩과 다혁님 C03/C04 네트워크는 VM 준비 후 담당자와 연결한다. 수언님 frontend 파일은 소유자 준비 뒤 프록시로 연결한다. 다음 지정 구현은 P1-1이며 실제VM·로그인·AI통합·공식flow.py 완료로 처리하지 않는다. commit/push/외부전송 없음.
- 최종 확인: 이미지 재빌드 성공 후 같은188개를 재실행해 종료0·188 passed/1 warning in 6.45s를 확인했다. 저장소 전체 변경 경로가 develop/jihye 내부이고 private DB URL/암호가 변경 파일에 없음을 값 출력 없이 검사했다. deploy/.env.backend는 Git 제외·권한600이며 이번 검증용 LOGIN은 해당 로컬 DB에만 준비했다. 다른 역할/실행 환경의 자격증명 준비 완료를 뜻하지 않는다.

## P1-1 · 세션·관리자 발급·권한

- [x] 연결 SPEC: BE-01, C01.
- 생성/수정 예정: `app/services/auth.py`, `accounts.py`, `app/repositories/users.py`, `sessions.py`, auth/users 라우터·deps·security; `tests/test_auth_permissions.py`, `tests/integration/test_accounts.py`.
- 작업: 로그인/로그아웃/me/암호 변경과 관리자 생성/비활성화/초기화를 연결한다. 모든 보호 경로에 활성 계정·역할 검사를 적용한다. SPEC 현재 기준의 세션·첫 변경·회수·비밀번호·관리자 보호를 구현한다. HANDOFF에 남은 추가 정책과 DTO 세부만 초안으로 분리한다. 기본401/403·응답 비밀 제거는 바로 구현한다.
- 구현: `app/services/auth.py`, `accounts.py`, users/sessions repositories 및 DB backend를 연결했다. 로그인은 활성 계정만 허용하고 일반화된401을 반환한다. 난수 세션 원문은 HttpOnly·SameSite=Lax·Path=/·8시간 쿠키로만 전달하고 HMAC-SHA256 해시만 `app.sessions`에 저장한다. 요청마다 만료·회수·활성 계정을 확인한다. 로그아웃·비밀번호 변경·관리자 초기화·비활성화는 해당 사용자의 세션을 회수한다. `SESSION_SECRET`/DB 미설정은 안전하게503이다.
- 비밀번호·권한: Argon2id, 12자·문자 3종·본인 이름/login_id 포함 금지를 적용했다. 첫 로그인 사용자는 `me`/암호 변경/로그아웃 외 보호 작업을403으로 막는다. IT팀 부서와 role을 함께 검사하고 role은 계정 발급 시 부서에서 결정한다. 직원 목록·계정 응답에는 해시·비밀번호·세션 토큰을 포함하지 않는다. 본인/최후 활성 IT 관리자 비활성화는409로 거절한다. 계정 동시 변경은 bootstrap과 같은 advisory lock으로 직렬화한다.
- 실제 확인: `uv run python deploy/check_db.py --all` 종료0, **197 passed, 1 warning**. 기존 Starlette/httpx 폐기 예정 경고1건. 새 P1-1 검사에는 쿠키 속성·토큰 응답 미노출·첫 변경 제한·비IT admin 거절 단위 확인과 격리 PostgreSQL HTTP 시험이 포함된다. 실 DB에서 로그인, 관리자 계정목록·발급, 직원403, 임시 암호 변경과 기존 쿠키 무효화, 로그아웃 후 재사용401, 세션 해시 저장을 확인했다. 합성 데이터와 시험 거래를 정리해 테스트 뒤 업무 행이 남지 않도록 했다.
- 미확인/다음: 실제 VM 로그인·SESSION_SECRET 주입·실제 직원 seed 및 첫 관리자 자격으로 화면 시험은 미실행이다. P0-6 bootstrap으로 실제 직원6명과 첫 admin이 VM에 준비된 뒤 로그인/첫 변경 및 나머지5명 발급을 수언님 화면과 대조한다. 수언님에게 쿠키·로그인·계정 발급 응답을 전달하고, 오현님에게 로컬 DB 검증과 VM 미검증 범위를 전달한다. C05 저장 API·문의/티켓/알림 업무 저장은 P1-3 이후 범위다.

## P1-2 · 문의 선저장·support 어댑터·본인 조회

- [ ] 연결 SPEC: BE-02·03, C01/C02.
- 생성 예정: `app/services/inquiries.py`, `app/repositories/inquiries.py`, `app/clients/support.py`; ask/requests 라우터; `tests/test_ask_adapter.py`, `tests/integration/test_request_ownership.py`.
- 작업: 서버 신원→공통 user, 문의 선저장→짧은 거래 종료→support 호출→검증된 응답 저장 순서로 만든다. 동일 키는 소유권부터 검사하고 원문 입력의 변조 재사용/실행중 재시도는 H04 검토 결과로 처리한다. DB 거래를 HTTP 대기 동안 유지하지 않는다.
- 확인 예정: `uv run pytest tests/test_ask_adapter.py tests/integration/test_request_ownership.py -q`. 두 직원의 타인 request_id403·결과 미노출·support 미호출, 본인 목록 분리, 입력400, 공통400 codes,5 route와 reason/timings 보존을 확인한다. timeout/잘못된 JSON은 Mock으로 검증하고 실제 서비스와 구분한다.
- 넘길 결과: 다혁님에게 실제 수신 페이로드·응답 보존/오류 결과, 수언님에게 본인 문의/재시도 사용법. 연결3초·전체30초·재시도0의 초기 예산을 적용하되 실측 없이 시간 목표 통과로 쓰지 않는다.

## P1-3 · 티켓·알림·관리자 처리와 실패 거래

- [ ] 연결 SPEC: BE-03·04, C05.
- 생성 예정: `app/services/tickets.py`, `alerts.py`, `storage_mode.py`, `app/repositories/tickets.py`, `alerts.py`; tickets/alerts 라우터; `tests/integration/test_ticket_idempotency.py`, `tests/test_storage_mode.py`.
- 작업: 내부 X-Api-Key와 세션을 분리하고 요청 직원 확인·문의 연결·T-번호 발급·UNIQUE 충돌 회수를 구현한다. 알림 거래를 분리하고 app/practice 한 대상만 호출한다. DLQ는 공통 반영된 POST /dlq 계약으로 서비스·repository·시험을 연결한다. H07의 알림 duplicate 확장과 DLQ200 명문화 상태는 별도 확인하며, 미확정 확장 없이 가능한 기본 저장은 구현한다.
- 확인 예정: `uv run pytest tests/integration/test_ticket_idempotency.py tests/test_storage_mode.py -q`. 동일 key 동시2회→티켓1건·같은ID·신규201/중복200, 타인 key403, 내부키401, 티켓 commit 뒤 알림 실패에도 티켓 유지, 관리자 수정/직원403/없는 티켓404를 확인한다.
- 넘길 결과: 원민님에게 실제 저장 결과·재시도/중복·장애 경계·실제 관측 대상과 DLQ 저장 결과와 ACK 미해결 세부. 상대로부터 실제 확인이 없으면 연결 완료로 표시하지 않는다.

## P1-4 · 실연결·재시작·측정·인계

- [ ] 연결 SPEC: BE-01~07, C01/C02/C05/C06/C07/C08/C09.
- 생성 예정: `tests/integration/test_persistence.py`, `tests/integration/test_web_flow.py`, `tests/integration/test_backup_restore.py`; 실제 실행 후 `Doc/SUBMISSION-NOTES.md`. 상대 코드/워크플로우·공통 사례 기대값은 수정하지 않는다.
- 확인 예정: `uv run pytest tests/integration/test_persistence.py tests/integration/test_web_flow.py -q`, volume 유지 postgres/backend 재시작 후 revision·문의/티켓·RAG 청크/검색 재확인. frontend→FastAPI→동일support, handoff→같은 저장대상, 유빈님 실제 색인/재색인을 각각 확인한다.
- 백업/복원 확인 예정: `tests/integration/test_backup_restore.py`에서 별도 검증 DB의 백업을 다른 격리 DB에 복원하고 revision·관계·행 수·해시를 대조한다. 유빈님이 복원 후 권한별 검색을 확인한다. named volume 유지 재시작과 별개이며 공유/운영 DB를 덮어쓰지 않는다. 자동 백업 주기·RPO/RTO는 이번 필수 범위에 확정하지 않는다.
- 측정: SPEC 8절대로 품질·지연 원자료를 수집한다. 개발 호출 예산과 최종 검증을 구분한다. 최종 제출용 LLM 시나리오는 **3회 반복(`--repeat 3`)**하고 회차별 실패도 보고한다. 처리시간 측정은 최대5회 표본과 계산 방법을 남긴다. n8n push/test와 팀 VM 실행은 담당 사람이 수행한다.
- 넘길 결과: 각 상대에게 실제 입출력·Mock 여부·실패/재시험 보고서, 오현님에게 검증한 명령/버전/head·재시작/복구·정책 미반영·미실행을 전달한다. 설계/결과 취합은 본인 SUBMISSION-NOTES를 통해 하고 공통 docs는 직접 고치지 않는다.

## 단계별 실제 기록 방식

구현한 단계 아래에 실행일·요구/계약ID·생성파일·작업 디렉터리·명령·종료 상태·기대/실제 차이·Mock/실연결·마스킹한 증거 경로·남은 문제를 기록한다. 아직 실행하지 않은 단계는 체크하지 않는다. 실패가 있으면 같은 조건 재시험 결과도 남긴다. 미검토 제안을 ‘합의 완료’로 적거나 설치/시험 PASS를 미리 채우지 않는다.

## 참고

[주제](../../../docs/TOPIC.md) · [공통 API](../../../docs/API-CONTRACT.md) · [DB](../../../docs/DATA-AND-DB.md) · [협업](../../../docs/COORDINATION.md) · [팀 헌장](../../../docs/TEAM-CHARTER.md) · [전체 아키텍처](../../../docs/ARCHITECTURE.md) · [평가·시나리오 가이드](../../../docs/EVALUATION-GUIDE.md).
