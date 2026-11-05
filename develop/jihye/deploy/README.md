# 지혜님 · 서버·DB·배포 작업 지시

[IMP-PLAN P0](../Doc/IMP-PLAN.md)에서 단계별로 작성한다. 이 문서는 배포 작업의 상세 조건이다. **P0-3 실제 실행 절 외의 전체 배포 파일·명령은 후속 구현 예정이다.** 실제 팀 VM 배포와 환경값 등록은 오현님이 담당한다.

## 현재 상태와 단계별 전제

2026-11-05 현재 P0-1~2와 P0-3 postgres Compose·실제 접속·Alembic 실행 기반을 확인했다. 아래 backend Dockerfile·readiness·전체 Compose·VM 절차는 아직 구현/실행하지 않았다. 현재 확정 주소·모드·인증·시간 예산은 [SPEC 1절](../Doc/SPEC.md#1-적용할-기준--새로-선정하지-않음)을 따른다.

- P0-3: Docker/Compose·pgvector 이미지 확보와 본인 전용 DB 비밀 설정이 전제다. postgres 부분·volume·healthcheck·DB 접속·Alembic 기반만 구현하고 테이블/전체 서비스는 후속으로 둔다.
- P0-7: DB 마이그레이션·확장 준비 뒤 backend 이미지·readiness를 확인한다. frontend가 없으면 타인 파일을 만들지 않고 DB/backend 확인 범위로 기록한다.
- P1-4: 실제 제공자·키트·격리 검증 환경이 준비된 뒤 통합·재시작·백업/복원을 확인한다. 실제 환경/키 전달과 팀 VM 반영은 오현님이 관리한다.
- SERVICE_MODE 설정, n8n Credential/URL, fault/reset/ops 관측 대상은 각각 확인한다. 기본 app/practice 선택만으로 전체 호출 대상이 바뀌었다고 판정하지 않는다.

## P0-3 실제 실행 기반

실제 생성 파일은 compose.yaml의 postgres, compose.check.yaml의 검증 전용 db-check, init_db_env.py/check_db.py와 변수 이름만 있는 .env.example이다. 프로젝트 `oke-jihye-p0`는 기존 서비스와 별도 네트워크·named volume을 사용하며 DB 호스트 포트를 공개하지 않는다. 기존 n8n/data-api를 여기에 연결하지 않았다.

```bash
uv run python deploy/init_db_env.py
docker compose --env-file deploy/.env -f deploy/compose.yaml config --quiet
docker compose --env-file deploy/.env -f deploy/compose.yaml up -d --wait postgres
docker compose --env-file deploy/.env -f deploy/compose.yaml ps
uv run python deploy/check_db.py
uv run python deploy/check_db.py --all
```

최종114개 통과·경고1건(실제 DB5개 포함). 확인 이미지는 compose.yaml에 digest 고정한 pgvector/pgvector:pg16, 실제 PostgreSQL16.15·사용 가능한 vector0.8.6이다. vector 활성화·테이블·grants는 아직 없다. 처음 호스트→Docker bridge 접속과 시험 컨테이너의 임시 디렉터리 누락으로 실패했고, 같은 Docker 네트워크와 /tmp tmpfs로 수정 후 재시험했다.

검증 도구는 설치된 Linux x86_64 Python3.12 .venv를 읽기 전용으로 참조한다. backend 배포 이미지는 P0-7에서 별도로 만든다. 로컬 DATABASE_URL은 postgres 호스트를 사용하므로 호스트 셸에서 직접 DB 명령을 실행한다고 접속되는 것은 아니다. 현재 실접속 검증은 check_db.py에서 수행한다. DB는 healthy 상태로 남기고 volume을 유지했다.

private deploy/.env는 권한600·Git 제외다. 처음 상세 traceback에 자동생성 검증용 암호가 노출되어 교체했고 출력 마스킹/짧은 traceback·보안 회귀를 추가했다. 실제 값이나 과거 값은 기록하지 않는다. 이 migration용 접속을 앱/RAG 런타임에 공유하지 않고 P0-5 최소 권한을 별도로 준비한다. DB 준비 상태·실패/재시험 원자료는 IMP-PLAN 실제 기록을 따른다.

## 만들 파일과 기준

| 예정 파일 | 내용·확인 |
| --- | --- |
| deploy/backend.Dockerfile, deploy/.dockerignore | 본인 pyproject/잠금 파일로 backend 이미지, 비root 실행·8000·비밀 파일 제외. context가 본인 폴더일 때 dockerfile은 deploy/backend.Dockerfile |
| deploy/compose.yaml | frontend/backend/postgres/n8n/data-api, named volume·healthcheck·내부 네트워크·모드. backend build context=.., frontend=../../sueon |
| deploy/.env.example | 아래 공통 변수의 **이름만**. 실제 .env는 배포 비밀 관리에서 만들고 Git에 넣지 않음 |
| app/api/routes/health.py, tests/integration/test_readiness.py | liveness와 DB/revision/vector readiness를 구분, 오류에서 접속 문자열 미노출 |

[API C07](../../../docs/API-CONTRACT.md)의 내부 주소는 backend:8000, postgres:5432, n8n:5678, data-api:8800이다. 공개 웹 기본3000, 로컬 backend8000/n8n5678/data-api8800을 사용한다. 로컬용 내부 도구 포트는 loopback 바인딩으로 계획한다. postgres5432는 기본 외부 공개하지 않는다. VM의 n8n 관리 접근/비밀번호·공개 경로는 오현님이 관리한다.

PostgreSQL은 pgvector 포함 이미지·named volume·healthcheck를 사용한다. PostgreSQL/pgvector 이미지 태그·digest는 실제 설치/확장 검증 뒤 고정하며 지금 검증한 버전으로 적지 않는다. n8n은 공통 평가 환경과 호환되는 버전을 적용한다. 기존 n8n/data-api를 재사용하면 Compose 중복 기동을 피하고 같은 네트워크 alias·충돌 포트·실제 URL을 기록한다. 포트를 임의 재선정하지 않고 충돌 변경은 C07로 요청한다.

프론트 Dockerfile·/api 프록시는 수언님 소유다. 지혜님은 해당 파일을 대신 만들지 않는다. 수언님에게 frontend context와 `/api`→`http://backend:8000` 서버 프록시 조건을 전달한다. 브라우저는 localhost 또는 VM 공개 웹 주소로 접근하며 Docker 내부 호스트명·n8n 키를 브라우저에 넣지 않는다. 프론트 파일이 아직 없으면 postgres/backend를 먼저 확인한다.

## 환경변수·모드

공통 변수 이름은 DATABASE_URL, N8N_WEBHOOK_URL, N8N_WEBHOOK_KEY, INTERNAL_API_KEY, DATA_API_URL, DATA_API_KEY, SERVICE_MODE, SESSION_SECRET, BOOTSTRAP_ADMIN_PASSWORD, BACKEND_ORIGIN이다. 실제 값·VM 주소·암호·토큰은 문서/로그/화면/저장소에 넣지 않는다. bootstrap 암호는 최초 생성 명령에만 주고 평상시 서버 필수값으로 만들지 않는다.

| 모드 | 실행 목적 | 기록할 것 |
| --- | --- | --- |
| practice | 원본 data-api 직원/규정·티켓/알림 및 fault/reset/ops 공통 시험 | support/handoff의 실제 대상 data-api, 관측도 같은 대상인지 원민님 확인 |
| app | 계정/문의·새 티켓/알림/DLQ는 PostgreSQL, 직원/규정 원본 조회는 data-api | handoff의 저장 대상 backend /tickets·/alerts·/dlq, 관리자 조회는 같은 PostgreSQL |

SERVICE_MODE 하나가 상대 n8n Credential/URL까지 자동 변경한다고 가정하지 않는다. 시작 전 FastAPI 설정과 n8n의 실제 호출 대상·fault/reset/ops 관측 대상을 대조해 원민님에게 넘긴다. 같은 티켓을 PostgreSQL과 data-api에 이중 생성하지 않는다. PostgreSQL 장애를 data-api로 몰래 우회해 성공으로 표시하지 않는다.

## 구현 후 로컬 확인 순서 · 아직 실행하지 않음

명령의 작업 디렉터리는 저장소 기준 `develop/jihye`다. 실제 비밀 파일은 로컬에서만 `deploy/.env`로 준비하는 계획이다. 명령 출력에 환경값을 펼치는 config 출력은 피한다.

1. `uv sync --dev`로 본인 의존성만 설치하고 잠금 파일을 검증한다. 서버 개발 명령은 `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`로 계획한다. 이미지 내부는 host 0.0.0.0/8000이다.
2. `docker compose --env-file deploy/.env -f deploy/compose.yaml config --quiet`로 경로·문법을 검사한다. 실제 .env·암호·키는 출력/보고서에 복사하지 않는다.
3. `docker compose --env-file deploy/.env -f deploy/compose.yaml up -d postgres` 후 `ps`로 health를 확인한다. `pg_isready`는 접속 준비 검사이며 schema 적용 증거는 아니다.
4. `docker compose --env-file deploy/.env -f deploy/compose.yaml build backend` 후 backend 일회성 컨테이너에서 `uv run alembic -c migrations/alembic.ini upgrade head`를 실행하는 절차를 구현한다. 마이그레이션용 접속과 앱 런타임 권한을 분리한다. [마이그레이션](../migrations/README.md) 확인을 먼저 끝낸다.
5. backend 일회성 명령 `uv run python -m app.cli seed-employees`→`bootstrap-admin --employee-name <제공 IT팀 이름> --login-id <선택한 ID>`를 구현한다. 첫 명령 완료/직원6명 확인 후 다음 명령으로 간다. 비밀번호는 BOOTSTRAP_ADMIN_PASSWORD에서만 읽는다.
6. `docker compose --env-file deploy/.env -f deploy/compose.yaml up -d backend` 후 `/health/live`와 `/health/ready`를 확인한다. ready는 DB 접속·현재 head·vector를 확인하며 n8n 미연결을 숨기지 않는다. 예정 확인 요청은 `curl --fail http://127.0.0.1:8000/health/ready`다.
7. 제공자 준비 뒤 n8n/data-api 연결, 수언님 frontend 프록시를 연결한다. 로그인→첫 변경→질문→내 문의→관리자 티켓/알림 순으로 실제 연결하고 Mock 검증과 따로 기록한다. 브라우저 요청이 /api만 향하는지도 확인한다.
8. 앱 기록과 RAG 테스트 문서/청크를 넣은 뒤 `docker compose --env-file deploy/.env -f deploy/compose.yaml restart postgres backend`로 volume 유지 재시작을 확인한다. 준비 회복 후 revision·행 수·키·검색 결과를 비교한다. `down -v`나 데이터 삭제는 기본 절차가 아니다.

각 명령의 실제 실행 가능 여부와 이미지 버전은 구현 뒤 검증해 이 문서에 반영한다. 없는 파일을 이미 실행 가능한 도구로 소개하지 않는다. 장애로 중단하면 마지막 성공 단계·실패 로그(마스킹)·다음 복구 조치부터 기록한다.

## VM 인계 · 오현님 수행

지혜님은 검증한 이미지/의존성 버전·실행 위치·필수 변수 이름·health 경로·schema head·seed/최초 관리자/재실행 조건·SERVICE_MODE·프록시 조건·백업/복원 확인 자료를 전달한다. 오현님은 실제 비밀 등록→DB 준비→마이그레이션→bootstrap 필요 여부 판단→backend/frontend→준비 상태→회귀 순서로 진행한다.

기존 DB 변경 전 백업, 복원 연습은 별도 DB로 계획한다. 재색인은 유빈님 oke-index로 하며 업무 DB 복구와 구별한다. 마이그레이션 실패 시 바로 volume을 삭제하지 않고 head/로그·백업 기준으로 복구 또는 새 수정 revision을 판단한다.

VM 배포 후 공통 시험·LLM 반복·실제 runs 결과는 원민님과 오현님이 기록한다. n8n `push/test`는 사람이 수행한다. 80일차 키트가 준비된 뒤 그 키트 작업 디렉터리에서 `uv run tools/flow.py doctor`를 확인하는 계획이며, 현재 키트 준비나 ready를 확인했다고 쓰지 않는다.

[전체 아키텍처](../../../docs/ARCHITECTURE.md) · [공통 API](../../../docs/API-CONTRACT.md) · [제출·시연](../../ohyun/SUBMISSION.md).
