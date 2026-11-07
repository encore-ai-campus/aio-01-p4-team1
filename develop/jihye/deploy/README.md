# 지혜님 · 서버·DB·배포 작업 지시

[IMP-PLAN](../Doc/IMP-PLAN.md)의 DB/backend 실행 절차를 보완한다. **현재 상태 · 2026-11-06:** 로컬 backend·Compose·readiness는 P0-7에서 구현·검증됐고, 개인 migration head는 `0005`다. 재시작 유지와 별도 DB backup/restore를 확인했다. backup/restore 원본 RAG documents/chunks는 0건이라 실제 저장 벡터 복원은 미검증이다. 루트 [팀 VM 기록](../../../docs/VM-TEAM-TESTING.md)은 VM `0005`와 제한된 FE/BE API·DB 시험을 보고한다. 이는 문서 근거와 사용자가 제공한 VM 표본으로 구분하며 VM 배포·환경값 등록·시험 창은 오현님이 관리한다.

아래 P0 단계별 실행 절은 구현 당시 절차와 이력을 포함한다. `현재`, `예정`, `미실행` 문구가 포함된 날짜별 구간은 작성 당시 상태일 수 있으므로 상단 상태와 루트 VM 기록을 먼저 대조한다. 공유 VM에 적용·재기동·초기화 명령을 실행하지 않는다.

## 후속 CI·CD 산출물 준비 범위

현재는 계획 단계이며 산출물 구현·실행은 미착수다. P1-4 잔여 확인 후 로컬 초기 설정 재현 → CI 준비 → CD 양식·인계 순으로 진행한다. 상세 체크리스트는 [IMP-PLAN](../Doc/IMP-PLAN.md)의 별도 후속 작업 절을 따른다.

| 준비 대상 | 지혜님이 본인 폴더에 준비할 내용 | 적용 담당·완료 경계 |
| --- | --- | --- |
| 로컬 재현·CI | 빈 임시 DB migration·명시적 seed·필요한 계정 준비·핵심 저장/조회와 백엔드 시험 스크립트 및 Actions 예시 | 실제 격리 실행 결과를 남긴 후 오현님이 루트 CI에 반영. 팀 VM 대상으로 실행하지 않음 |
| CD 양식 | 배포 커밋/서비스·설정 이름/용도·백업/migration·이미지 빌드/기동·readiness·실패 대응·결과 기록 및 workflow 예시 | 오현님이 대상/권한/Secrets/승인/백업·복구 정책과 루트 workflow를 적용. 양식 작성은 배포 활성화 완료가 아님 |

CD 예시는 기존 루트 `deploy/README.md`와 팀 VM Compose를 읽기 기준으로 사용한다. 이 폴더의 개인 로컬 Compose를 VM 배포 대상으로 자동 대체하지 않는다. 운영 seed·관리자 생성·데이터 초기화는 포함하지 않고, 이전 이미지로 복귀할 조건과 DB 복원 판단을 구분한다. 마이그레이션 후 구버전 이미지 호환성을 확인하지 않은 일괄 자동 rollback은 계획하지 않는다. 비밀번호·키는 예시에 넣지 않고, `.github/workflows/` 및 VM 수정은 오현님이 수행한다.

## 단계별 전제 및 실행 이력

P0-3 당시에는 postgres Compose·DB 접속·Alembic 기반을 확인하는 범위였다. 이후 P0-7에서 backend Dockerfile·readiness·로컬 Compose까지 구현했다. 현재 확정 주소·모드·인증·시간 예산은 [SPEC 1절](../Doc/SPEC.md#1-적용할-기준--새로-선정하지-않음)을 따른다.

- P0-3: Docker/Compose·pgvector 이미지 확보와 본인 전용 DB 비밀 설정이 전제다. postgres 부분·volume·healthcheck·DB 접속·Alembic 기반만 구현하고 테이블/전체 서비스는 후속으로 둔다.
- P0-7: DB 마이그레이션·확장 준비 뒤 backend 이미지·readiness를 확인한다. frontend가 없으면 타인 파일을 만들지 않고 DB/backend 확인 범위로 기록한다.
- P1-4: 실제 제공자·키트·격리 검증 환경이 준비된 뒤 통합·재시작·백업/복원을 확인한다. 실제 환경/키 전달과 팀 VM 반영은 오현님이 관리한다.
- SERVICE_MODE 설정, n8n Credential/URL, fault/reset/ops 관측 대상은 각각 확인한다. 기본 app/practice 선택만으로 전체 호출 대상이 바뀌었다고 판정하지 않는다.

## P0-3 실제 실행 기반

### P0-7 로컬 실행 기록 · 2026-11-05

전용 로컬 backend/postgres를 빌드·기동했다. backend는 UID10001/read-only 파일시스템·cap_drop ALL로 실행하며 host 기본8000을 loopback에만 공개한다. 실제 검증에서는8000 포트 연결 오류 후 `BACKEND_PORT=18000`을 사용했다. DB 포트는 여전히 외부 공개하지 않는다. 최신 revision은 `0005`이며 기존0004 이후 readiness용 public.alembic_version SELECT 권한만 oke_app에 추가했다. 새revision은 VM 인계에도 포함해야 한다.

로컬 재현 순서(본인 전용 DB용):

```bash
uv run python deploy/check_db.py --alembic upgrade
uv run python deploy/init_backend_env.py
docker compose --env-file deploy/.env -f deploy/compose.yaml build backend
BACKEND_PORT=18000 docker compose --env-file deploy/.env -f deploy/compose.yaml up -d --wait backend
curl --fail http://127.0.0.1:18000/health/live
curl --fail http://127.0.0.1:18000/health/ready
uv run python deploy/check_db.py --all
```

init_backend_env.py는 기존 전용 DB 설정이 일치할 때만 로컬 LOGIN과 oke_app 역할 연결을 만들고 권한600·Git 제외의 `.env.backend`에 runtime DATABASE_URL과 SERVICE_MODE=app을 저장한다. 기존 파일은 덮어쓰지 않으며 파일 없이 같은 LOGIN이 이미 존재하는 경우 실패하고 수동 점검을 요구한다. migration URL/암호는 runtime에 주입하지 않는다. Compose는 `BACKEND_ENV_FILE`로 runtime 파일 위치를 바꿀 수 있으며 파일이 없으면 DB 미설정 readiness503이다. 환경 출력 전체를 공개하지 않는다.

이미지의 의존성은 `uv export --frozen --no-dev --no-hashes --no-emit-project --output-file deploy/requirements.lock`으로 uv.lock에서 내보냈다. Dockerfile 전용 `backend.Dockerfile.dockerignore`가 실제 본인 폴더 build context에 적용되며 app/migrations/고정 requirements 외의 private env·호스트 .venv·문서를 제외한다. deploy/.dockerignore는 참고용이며 단독으로 루트 context를 차단한다고 간주하지 않는다. 패키지를 변경하면 uv.lock과 export를 함께 갱신한다.

`/health/live`는 프로세스 생존200, `/health/ready`는 DB/revision/pgvector 전제200 또는503이다. 응답의 scope=database이며 n8n/data-api/웹 업무의 종단간 준비 상태가 아니다. 실제 전용 DB 중지 중 ready503/live200, 재기동 후ready200을 확인했다. 정상 응답 예시는 `{"status":"ready","reason":"ok","scope":"database","service_mode":"app"}`이다. 이 문단의 P0-7 당시 업무 API 501 설명은 작성 시점의 이력이며, 후속 P1 API 구현·VM의 제한된 API 확인과 구분한다.

P0-7 당시 frontend 빌드 파일이 준비되지 않아 로컬 Compose에 추가하지 않았다. 이후 VM의 FE/BE 배포와 공개 API 확인은 루트 VM 기록에 별도로 보고돼 있다. 현재 팀 VM 구성·네트워크·자격 증명을 이 로컬 실행 절차로 변경하지 않는다. SERVICE_MODE만 바꿔 상대 Credential/관측대상이 자동 전환된다고 가정하지 않는다.

초기 VM 배포 절차는 관리자가 LOGIN/oke_app 연결과 비밀 파일을 준비하고, 적용 커밋의 backend 이미지에서 일회성 마이그레이션 계정으로 필요한 revision을 적용하는 방식이다. 루트 2026-11-06 VM snapshot은 현재 revision `0005`를 보고하므로 이 절차를 현재 VM에 그대로 다시 실행하지 않는다. 이미지에는 uv가 없으므로 컨테이너 내부는 `uv run` 대신 `python -m` 명령을 쓴다. 자동 seed/관리자 생성은 하지 않는다.

P0-4 단계 기록(2026-11-05): 아래 P0-3 기록의 '테이블 없음'은 당시 상태다. 전용 DB에 `0001→0002`를 적용해 당시 `0002 (head)`와 업무 테이블 7개를 확인했다. 이후 P0-5/P0-7에서 로컬 head는 `0005`로 갱신됐다. 당시 명령·결과는 `uv run python deploy/check_db.py --alembic current`, `--migrations`, `--all`, 마이그레이션 검사40개·전체155개 통과·기존 경고1건이다. 단계별 세부는 IMP-PLAN을 참조한다.

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

## 초기 예정 파일과 기준 · 현재 구현 여부는 README/IMP-PLAN 참조

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

## 초기 구현 계획의 로컬 확인 순서 · 실제 단계 결과는 IMP-PLAN 참조

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

### P0-6 직원 seed·첫 관리자 인계

CLI는 구현됐다. 2026-11-05 VM 통합 기록에서 내부 `GET /employees`의 무인증 응답 구조가 CLI가 받는 6명 명단과 일치함은 확인됐지만, 그 결과만으로 CLI seed 실행이나 계정 bootstrap 완료를 뜻하지 않는다. 다른 응답 구조는 추측 변환하지 않는다. `DATA_API_EMPLOYEES_NO_AUTH=true`는 정확한 내부 URL과 키/헤더 미설정 조건에서만 사용한다. 다른 origin은 확인된 인증 설정을 요구한다.

초기 적용 당시의 절차다. 현재 루트 VM 기록은 revision `0005`를 보고한다. VM에서 직원 seed/bootstrap을 수행하기 전 오현님과 대상·현재 직원/계정·권한·시험 창을 확인하고, 승인이 없는 seed/bootstrap은 실행하지 않는다. 격리 로컬 시험에서는 DB URL을 마이그레이션 계정과 구분한 업무 DML 계정으로 주입하고 원문을 출력하지 않는다.

```bash
uv run python -m app.cli seed-employees
uv run python -m app.cli bootstrap-admin --employee-name <제공 IT팀 이름> --login-id <선택한 ID>
```

첫 명령 뒤 이름/부서6명을 확인하고 두 번째 명령을 실행한다. 두 번째는 `BOOTSTRAP_ADMIN_PASSWORD`와 `SESSION_SECRET`을 실행 환경에 주입해야 한다. 암호는 명령 인자로 받지 않으며 성공 출력은 ok/created뿐이다. 같은 대상 재실행은 created=0이며 기존 해시/역할을 보존한다. 다른 계정이 존재하는 환경의 복구 도구로 쓰지 않는다. 완료 뒤 일회성 BOOTSTRAP_ADMIN_PASSWORD를 제거한다. 로그인/첫 변경과 나머지5명 발급은 P1-1에서 연결한다. 테스트용 합성 계정을 VM에 복사하지 않는다.

### P0-5 RAG 실통합 인계 · 과거 적용 절차와 현재 기준

로컬 RAG DDL/권한 검증 당시의 head는 `0004`였고, P0-7에서 readiness grant인 `0005`가 추가됐다. 루트 2026-11-06 VM snapshot은 VM migration `0005`와 기존 RAG 8 documents/33 chunks를 보고한다. 이는 신규 색인·권한별 품질시험이나 백업 복원 검증을 뜻하지 않는다. 아래 절차를 실행하기 전에는 루트 VM 기록과 적용 대상의 현재 revision을 다시 확인한다. 기존 VM에 과거 `0004` 절차를 그대로 재실행하지 않는다.

인계 대상은 본인 폴더의 잠금 의존성, `migrations/versions/0001`~`0005`, `app/db/models/`, 마이그레이션 환경 및 실제 검사 기록이다. 로컬 P0-5 검증은 당시 PostgreSQL16.15/vector0.8.6·전체158개 통과·기존 경고1건이다. 로컬 DB 볼륨이나 private `deploy/.env`를 VM에 복사하지 않는다. 적용할 커밋은 실제 commit/push 후 기록하고 VM checkout과 대조한다.

#### 적용 전 오현님과 확인할 사항

- 사용할 VM DB·현재 revision·기존 데이터/역할 유무, 적용 담당과 시점. 기존 DB이면 백업·복구 경로를 먼저 확인한다. 로컬 Compose 검증 도구는 VM 공용 DB 관리 도구가 아니므로 그대로 실행 대상으로 바꾸지 않는다.
- 마이그레이션 실행 계정의 확장·스키마·역할 생성/GRANT 권한. `0001`은 빈 대상에 확장과 스키마를 생성하므로 이미 객체가 있는 DB에 무조건 적용하거나 `stamp`로 적용했다고 처리하지 않는다.
- 색인·검색 LOGIN 계정 생성 담당, 각 NOLOGIN 역할 연결과 비밀 주입 방법. 기존 동일 이름 역할에 과도한 권한이 있는지도 확인한다. `0004`는 기존 역할을 초기화하거나 암호를 설정하지 않는다.
- VM Python 실행 위치와 DB 접근 경로, Python 검색 서비스의 내부 주소 및 n8n 접근 경로. DB 포트를 외부 공개한다고 가정하지 않는다.
- 실제 원본 문서의 최종 목록·권한과 OpenAI 사용 승인. 유빈님 최신 회신은 8개이며 이전16개와 범위 차이는 오현님 확인 전 임의 확정하지 않는다.

#### DB 적용 순서 · 새 격리 대상에서 승인 담당자가 수행

작업 위치는 체크아웃한 저장소의 `develop/jihye`다. 마이그레이션용 `DATABASE_URL`은 비밀 관리에서 환경에 주입하고 출력하지 않는다. 이 URL은 SQLAlchemy용 `postgresql+psycopg` 드라이버를 사용한다.

```bash
uv sync --dev --locked
uv run alembic -c migrations/alembic.ini history
uv run alembic -c migrations/alembic.ini current
uv run alembic -c migrations/alembic.ini upgrade head
uv run alembic -c migrations/alembic.ini current
```

위 명령은 승인된 새 격리 대상에만 적용한다. 기존 VM에서는 revision과 대상 commit을 먼저 읽기 전용으로 대조한다. 현재 루트 VM 기록은 `0005`를 보고하므로, 공유 VM에 `upgrade head`를 임의 실행하지 않는다. 필요한 변경이 있으면 오현님이 백업·승인·작업 창을 정한 뒤 수행한다. 격리 대상 적용 후에는 실제 revision, vector 확장, app 업무 테이블, rag documents/chunks, `vector(3072)`, 권한·제약을 검사한다. 기존 DB에 시험 데이터를 넣거나 downgrade하지 않는다.

#### 접속과 설정 인계

| 실행 주체 | 접속 대상과 필요한 설정 | 권한 |
| --- | --- | --- |
| Python 색인 | 별도 실행 환경의 `DATABASE_URL`, `OPENAI_API_KEY` | 로그인 계정에 `oke_rag_index` 연결: rag DML·필요 시퀀스 |
| Python 검색 HTTP 서비스 | 별도 실행 환경의 `DATABASE_URL`, `OPENAI_API_KEY`, `SEARCH_TEAM_KEY`, `SEARCH_MODE`, `SEARCH_HOST`, `SEARCH_PORT` | 로그인 계정에 `oke_rag_search` 연결: rag SELECT |
| n8n oke-search | `SEARCH_SERVICE_URL`과 서비스 인증 설정 | Python 검색 HTTP 호출. DB 직접 접속 없음 |

위 변수 이름과 실행 구조는 사용자가 전달한 유빈님 회신 기준이며 실제 VM 설정은 미확인이다. psycopg 직접 접속의 URL 형식은 SQLAlchemy용 URL과 다를 수 있으므로 각 프로그램이 요구하는 형식으로 주입한다. 색인/검색은 각각 다른 계정 값을 같은 `DATABASE_URL` 이름으로 사용할 수 있다. 암호·키·전체 URL을 채팅·보고서에 기재하지 않고 승인된 비밀 전달 경로를 사용한다.

#### 유빈님과 확인할 순서와 남길 결과

1. 실제 색인·검색 로그인 계정으로 접속하고, 색인 DML·시퀀스 허용 및 검색 쓰기/DDL 거절을 확인한다. 로컬 NOLOGIN 역할 ACL 시험과 구분한다.
2. 합성 문서의 저장·3072차원·metadata 보존과 all/all+it 사전 필터 검색을 확인한다. 테스트 데이터 정리 범위를 정하고 기존 문서를 건드리지 않는다.
3. 승인된 원본을 유빈님 프로그램으로 청킹·임베딩·적재한다. 문서 수·누락/거절·실패를 실제 성공 수와 분리한다.
4. Python 검색 서비스→n8n C03→본체 연결 및 권한별 HTTP 시험을 담당자들과 수행한다. C03 경로·직원 권한 전달은 유빈님/다혁님/오현님 확정 결과를 따른다.
5. 적용 커밋, 실행 환경·담당·시각, revision/확장 버전, 역할별 허용/거절, 합성/실제 원본 시험, 실패와 미실행을 개인 IMP-PLAN/HANDOFF에 기록한다. 팀 VM 운영 결과와 공통 설계서 반영은 오현님이 관리한다.

지혜님은 검증한 이미지/의존성 버전·실행 위치·필수 변수 이름·health 경로·schema head·seed/최초 관리자/재실행 조건·SERVICE_MODE·프록시 조건·백업/복원 확인 자료를 전달한다. 오현님은 실제 비밀 등록→DB 준비→마이그레이션→bootstrap 필요 여부 판단→backend/frontend→준비 상태→회귀 순서로 진행한다.

기존 DB 변경 전 백업, 복원 연습은 별도 DB로 계획한다. 재색인은 유빈님 oke-index로 하며 업무 DB 복구와 구별한다. 마이그레이션 실패 시 바로 volume을 삭제하지 않고 head/로그·백업 기준으로 복구 또는 새 수정 revision을 판단한다.

VM 배포 후 공통 시험·LLM 반복·실제 runs 결과는 원민님과 오현님이 기록한다. n8n `push/test`는 사람이 수행한다. 80일차 키트가 준비된 뒤 그 키트 작업 디렉터리에서 `uv run tools/flow.py doctor`를 확인하는 계획이며, 현재 키트 준비나 ready를 확인했다고 쓰지 않는다.

### 개인 DB backup/restore 확인 · 2026-11-06

호스트 PATH에 PostgreSQL 클라이언트가 없으므로 개인 PostgreSQL 컨테이너 내부의 `pg_dump`/`pg_restore` 16.15를 쓰는 [명시 확인 runner](check_backup_restore.py)를 추가했다. `uv run python deploy/check_backup_restore.py --confirm-private-db`만 실행을 허용한다. 원본 `oke_jihye_p0` 및 migration owner/Compose URL을 검사하고, 비어 있는 `oke_jihye_p1_4_restore`가 이미 있으면 중단한다. custom-format 백업을 새 대상에 복원한 뒤 revision·확장 버전·app/rag 테이블별 행 수·문서/청크 해시·vector 차원·embedding 타입을 비교하고, runner가 만든 복원 DB와 임시 archive만 제거한다. 실행 상세·수치는 [IMP-PLAN](../Doc/IMP-PLAN.md)의 2026-11-06 기록을 따른다. 기존 전체 pytest 회귀는 이 runner로 대체되지 않는다.

[전체 아키텍처](../../../docs/ARCHITECTURE.md) · [공통 API](../../../docs/API-CONTRACT.md) · [제출·시연](../../ohyun/SUBMISSION.md).

## 로컬 전용 합성 업무 데이터

`seed_local_mock.sql`은 로컬 통합 화면과 업무 API를 확인할 합성 업무 행을 명시적으로 넣는다. Alembic revision·앱 시작·Compose 기동에서는 자동 실행하지 않는다. 스크립트가 DB명 `oke_jihye_p0`, migration owner `oke_migration`, head `0005`, pgvector 설치를 검사하고, 다른 DB/계정에서는 트랜잭션을 거절한다. 기존 직원의 부서가 팀 고정 6명 명단과 다르면 중단한다.

로컬 개인 Compose가 실행 중이고 migration `0005` 적용이 확인된 경우에만 `develop/jihye`에서 실행한다. `.env` 값이나 비밀번호를 명령에 직접 넣거나 출력하지 않는다.

```bash
docker compose --env-file deploy/.env -f deploy/compose.yaml exec -T postgres sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < deploy/seed_local_mock.sql
```

이 SQL은 팀 고정 직원 6명, 합성 문의 3건, 티켓 2건, 알림 2건, DLQ 1건을 추가한다. `localmock-` 식별자를 사용하고 기존 같은 키 행은 덮어쓰지 않는다. 정확한 fixture가 이미 있으면 재실행해도 중복 생성하지 않으며, 같은 식별자에 다른 내용이 있으면 전체 거래가 취소된다. 출력의 행 수만으로 로그인·워크플로우·실제 API 연결이 확인된 것은 아니다.

계정·세션은 만들지 않고 비밀번호도 포함하지 않는다. 로컬 로그인이 필요하면 기존 `seed-employees`와 `bootstrap-admin`/관리자 계정 발급 흐름을 별도로 사용한다. RAG documents/chunks는 넣지 않는다. 3072차원 0벡터는 화면/API seed로 사용하지 않으며, 검색 시험 데이터는 승인된 로컬 색인 절차나 검색 전용 fixture로 별도 준비해야 한다. 팀 VM, 공유/운영 DB, 실제 data-api와는 분리한다.

### VM data-api no-auth source verification · 2026-11-05

The initial P0-6 note above records the unverified state at implementation time. Later VM integration verified `GET http://data-api:8800/employees` without an auth header returned the exact existing six-person response accepted by `fetch_employees`; no key/header is configured or required by this internal source. The CLI now accepts `DATA_API_EMPLOYEES_NO_AUTH=true` only when `DATA_API_URL` is exactly `http://data-api:8800` and both `DATA_API_KEY` and `DATA_API_EMPLOYEES_AUTH_HEADER` are absent. It sends no authentication header in this mode. Other origins continue to require the existing explicit key and header configuration. The adapter validates the entire roster before the existing `seed_employees` service runs. See the dated VM evidence in [HANDOFF](../Doc/HANDOFF.md).
