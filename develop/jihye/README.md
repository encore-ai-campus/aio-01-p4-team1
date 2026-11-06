# 지혜님 · 백엔드·DB·실행 환경

화면·워크플로우가 같은 신원·저장 규칙으로 연결되도록 FastAPI와 PostgreSQL 기반을 담당한다. 작업 위치는 저장소의 `develop/jihye/`이며 다른 담당·루트 공통 파일은 읽기만 한다.

## 현재 상태와 다음 작업

| 항목 | 현재 상태 |
| --- | --- |
| P0-1 | FastAPI 골격·설정·liveness·공통 입력 타입 구현. 실제 로컬 HTTP liveness 확인 |
| P0-2 | 웹14 operation(13경로)·내부3 API 모델·라우터·OpenAPI·시험 전용 Mock 구현 |
| P0-2 보완 | 2026-11-05 context 최대2,000자 누락과 개인 문서 기준 정리. 전체100개 통과·경고1건 |
| DB·실행 환경 | P0-3~7 로컬 구현. Alembic `0005`까지 적용한 전용 DB와 backend readiness 확인 기록이 있음 |
| 인증·계정 | P1-1 로컬 PostgreSQL HTTP 통합 확인. 11/06 팀 VM 보고에는 직원·관리자 인증 API 점검이 기록됨. 브라우저 화면 검증은 미완료 |
| 문의·support | P1-2 로컬 PostgreSQL+MockTransport 확인. 팀 VM QA에서는 이관 경로와 문의 저장이 확인됐지만 `sources=[]`여서 정상 RAG 답변 검증은 아님 |
| 업무 처리 | P1-3 로컬 C05 저장 구현·검증. 원민님의 별도 로컬 n8n→FastAPI→PostgreSQL 15개 그룹 결과는 전달받은 보고임. VM QA는 티켓 저장·관리자 처리·직원 재조회 경로를 확인했으며 알림/DLQ 전체 시험은 별도 |
| 현재 잔여 | P1-4 로컬 시험 223 passed·2 skipped·warning 1건 기록. DB 재시작·web-flow·별도 DB backup/restore는 확인했지만 원본 RAG 문서·청크가 0건이라 실제 벡터 복원은 미검증. 전체 VM 통합과 공식 공통 평가는 미완료 |

상태 출처: 개인 P1-4 결과는 아래 IMP-PLAN 실행 기록, VM 결과는 [팀 VM 시험 기록](../../docs/VM-TEAM-TESTING.md)의 2026-11-06 보고다. VM 기록은 전달/문서 근거이며 이번 README 정리에서 직접 재실행한 결과가 아니다. 배포 커밋과 개인 작업 브랜치 커밋은 구분한다.

지금 사용할 순서는 **README → IMP-PLAN의 지정 단계 → 연결된 SPEC**이다. 루트 AGENTS의 시작 전 필수 확인은 유지한다. [SPEC 1절](Doc/SPEC.md#1-적용할-기준--새로-선정하지-않음)에 담당 구현에 필요한 현재 기준·출처·대조 커밋을 모았다. 개인 계획이 작업 범위를 정하며 공통 계약 누락/오기는 정리한다. 공통 계약 자체를 바꾸려면 HANDOFF로 요청한다.

## 문서별로 찾을 내용

| 문서 | 확인할 것 |
| --- | --- |
| [AGENTS](AGENTS.md) | 파일 소유권·단계 범위·검증과 전달 기록 규칙 |
| [TODO](Doc/TODO.md) | 백엔드/DB의 목적·필수 작업·후순위 |
| [SPEC](Doc/SPEC.md) | 입력/출력·인증·시간 예산·저장·DB·완료 기준. 확정과 제안 구분 |
| [IMP-PLAN](Doc/IMP-PLAN.md) | 단계별 전제·파일·명령·완료·인계와 실제 실행 이력 |
| [HANDOFF](Doc/HANDOFF.md) | 현재 상대 회신·계약 변경 제안·인계 자료와 과거 이력 |
| [마이그레이션](migrations/README.md) | 업무/rag 테이블·DDL 순서·접속 권한·검증·복구 |
| [배포](deploy/README.md) | Compose·서비스/모드·프록시·준비 상태·VM 인계 |

## 설치·실행·현재 응답

Python3.12 이상과 uv를 사용한다. 작업 디렉터리는 항상 `develop/jihye`다.

```bash
uv sync --dev --locked
uv run pytest -q
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- `GET /health/live` → `200 {"status":"ok"}`. `/health/ready`는 DB·revision·pgvector 전제200/503이며 scope=database다. 로컬 backend 컨테이너는127.0.0.1:18000에서 실제 확인했다. 기동은 [deploy 안내](deploy/README.md)의 P0-7 절을 따른다.
- `/docs`·`/openapi.json` 또는 `app.main.create_app().openapi()`로 계약을 볼 수 있다. 로그인·계정 관리는 DB와 `SESSION_SECRET`이 필요하며 미설정/접속 실패는503이다. 문의 API는 DB에 먼저 저장한 뒤 설정된 C02 URL로 전달한다. 실제 n8n 연결 설정 전에는 안전한503을 반환한다. C05 내부 저장은 `X-Api-Key`로 보호하고 app 모드는 PostgreSQL, practice 모드는 설정된 data-api 한 곳만 사용한다. 실행 서버에 Mock 성공 기능은 없다.
- Mock은 `tests/conftest.py`의 dependency override·HTTPX MockTransport에만 있다. 정상5 route·400 codes·계정/저장 예시는 해당 시험 파일에 있다. 실제 서비스 경계는 `app/api/deps.py`다.
- 환경변수 이름은 `app/core/config.py`에서 읽고 `.env`는 자동으로 읽지 않는다. `SERVICE_MODE=app`은 PostgreSQL, `practice`는 설정된 data-api로 C05 쓰기를 한 곳에만 보낸다. practice adapter는 MockTransport로만 확인했으며 live data-api 응답/인증은 미검증이다. practice 모드 관리자 티켓·알림 읽기/수정은 확인된 data-api 계약이 없어 503으로 닫는다. C05 내부 API는 `INTERNAL_API_KEY` 설정을 필수로 확인한다. 비밀값은 문서·응답·로그에 남기지 않는다.

## 지금 적용할 기준과 미확정 구분

- 질문trim1~500자, ID1~64자, attempt 엄격한 정수≥1, context 최대2,000자. context는 생략/null·빈 문자열 호환을 유지하며 trim/절단하지 않는다.
- 공개 가입 없음·관리자 발급·세션 신원. 쿠키는 oke_session/HttpOnly/SameSite=Lax/Path=/·기본8시간이다. 첫 변경 제한·회수·본인/최후 관리자 보호는 P1-1 로컬 PostgreSQL HTTP 시험에서 확인했다. 팀 VM의 인증 API 점검 기록은 있으나 브라우저 시각·클릭 검증은 미실행이다.
- 비밀번호12자·문자3종·본인 이름/login_id 포함 금지를 P1-1 서비스에서 적용한다. 이력·잠금·외부OTP는P2다.
- support 연결3초·전체30초·자동 재시도0은 확정 초기 예산이며 실측 성과가 아니다. 응답 추가 필드·reason/timings·공통400 codes를 보존한다.
- PostgreSQL app/rag·vector3072·text-embedding-3-large·정확cosine/top_k3·assignee=IT직원 employees.id는 확정이다. 로컬 전용 DB는 migration `0005`까지 적용해 검증했고, VM의 `0005`·RAG 8 documents/33 chunks는 팀 VM 기록의 snapshot이다. VM RAG 재색인·권한별 전체 검색 품질 검증과 백업 복원 후 검색은 별도다.
- H03 목록 DTO·patch 생략/null·Security nullable 세부와 추가 오류코드 등은 초안이다. 알림 duplicate ACK와 DLQ HTTP200은 공통 API 문서에 반영된 기준이며, 지혜님 P1-3 로컬 구현·시험과 VM의 알림/DLQ 실시험은 구분한다. 실제 data-api 문서 조회 구조·인증은 미확인이다.

## P0-3 DB 실행·검증

Linux x86_64에서 Python3.12 uv 환경을 동기화하고 Docker/Compose를 사용할 수 있어야 한다. 첫 명령은 Git 제외·권한600인 deploy/.env를 새로 생성하며 기존 파일이 있으면 덮어쓰지 않는다. 실제 암호/URL은 출력하지 않는다. `.env.example`에는 변수 이름만 있다.

```bash
uv sync --dev --locked
uv run python deploy/init_db_env.py
docker compose --env-file deploy/.env -f deploy/compose.yaml config --quiet
docker compose --env-file deploy/.env -f deploy/compose.yaml up -d --wait postgres
docker compose --env-file deploy/.env -f deploy/compose.yaml ps
uv run alembic -c migrations/alembic.ini history
uv run alembic -c migrations/alembic.ini heads
uv run python deploy/check_db.py
uv run python deploy/check_db.py --all
```

Compose 프로젝트는 `oke-jihye-p0`, DB 서비스는 `postgres`다. 기존 호스트5432/55432는 사용하지 않고 내부 `postgres:5432`와 named volume을 사용한다. 호스트 포트는 공개하지 않는다. 이 환경에서는 Docker 내부 IP에 호스트가 직접 접속하는 경로가 시간 초과였으므로 check_db.py는 같은 네트워크의 임시 db-check 컨테이너에서 시험한다.

시험 컨테이너는 현재 Python3.12 `.venv` site-packages를 읽기 전용으로 참조하고 `/tmp`는 tmpfs를 사용한다. 로컬 검증 도구이며 배포용 backend 이미지는 아니다. check_db.py는 출력의 접속 URL/암호를 가린다. Docker와 uv 캐시 접근 권한이 필요하지만 Docker 소켓 권한 자체는 변경하지 않는다.

P0-3 시점에는 빈 revision이었다. P0-4 단계에서 격리 검증 DB에 `0001→0002`를 적용해 당시 `0002 (head)`와 업무 테이블 7개를 확인했다. 전체 155개 통과·기존 경고 1건은 해당 단계 이력이며, 이후 P0-5/P0-7에서 로컬 head가 `0005`까지 갱신됐다. 자세한 결과는 [IMP-PLAN](Doc/IMP-PLAN.md)에 있다.

전용 DB는 healthy 상태로 남겼고 볼륨을 유지한다. 중지가 필요하면 `docker compose --env-file deploy/.env -f deploy/compose.yaml stop postgres`, 재개는 위 up 명령을 사용한다. 일상 중지/재시작에 `down -v`는 사용하지 않는다. P1-4 재시작 유지와 별도 DB backup/restore를 확인했다. backup/restore는 [IMP-PLAN 실행 기록](Doc/IMP-PLAN.md#p1-4-별도-db-백업복원-실행--2026-11-06)을 따른다. RAG documents/chunks가 0건이라 실제 저장 벡터 복원은 검증되지 않았다.

## 팀원 인계와 다음 연결

[HANDOFF](Doc/HANDOFF.md)에 상대별 확인·인계 상태를 정리한다. 현재 작업 브랜치는 `feat/jihye-p0`이며 main 병합 커밋은 `5bae594`다. VM 배포 커밋은 개인 브랜치와 별도이며 팀 VM 보고서를 기준으로 한다. 본 문서 갱신 중 외부 전송·VM 변경은 하지 않았다.

현재 잔여 연결은 팀 VM 기록·담당자 결과를 근거로 나눠 확인한다. 수언님 화면의 브라우저 시각/클릭 검증, 다혁님 본체의 정상 RAG 답변과 전체 C02/C03/C04 연결, 유빈님 실문서 색인·권한별 검색 및 복원 후 확인, 원민님 alert/DLQ와 공통 사례 시험은 각각의 직접 시험 기록이 필요하다. 오현님이 VM 작업 창·배포·공통 평가를 조정한다. 이 문서 갱신 중 외부 전송은 하지 않았다.

## 검증 이력과 참고 예제

P0-7 단계 결과: **188개 통과·기존 경고1건**. 실제 DB/runtime 로그인과 HTTP ready200→DB중지503/live200→재기동ready200을 확인했다. 이는 로컬 전용 환경 결과이며 VM/AI 통합 결과는 아니다.

P0-6 단계 결과: `uv run python deploy/check_db.py --all`에서 **180개 통과·기존 경고1건**. 직원 seed와 관리자 bootstrap은 격리 시험 DB에서 확인했다. 실제 직원 원본 호출/VM seed 실행 결과와 혼동하지 않는다.

P1-4 기준 마지막 전체 회귀 기록은 `uv run python deploy/check_db.py --all`의 **223 passed, 2 skipped, warning 1건**이다. 별도 backup/restore는 전체 회귀와 분리해 `uv run python deploy/check_backup_restore.py --confirm-private-db`로 수행했다. 이 검증은 공통 14종·VM 전체 시나리오·LLM 3회 반복 시험과 별개다. 일반 `uv run pytest -q`는 DB 시험 opt-in이 없으면 일부 DB 검사를 건너뛸 수 있다.

[앱 예제](../../docs/references/qnaweb/src-be/app/main.py.example)·[모델](../../docs/references/qnaweb/src-be/app/models.py.example)·[라우터](../../docs/references/qnaweb/src-be/app/routers/qna.py.example)·[Compose](../../docs/references/qnaweb/docker/compose/docker-compose.yml.example)에서는 계층 분리만 참고한다. create_all/자동시드·JWT·InfluxDB·10명 예제 대신 Alembic/명시적bootstrap·세션·app/rag·제공6명 기준을 적용한다. 예제의 존재가 실제 기능 완료를 뜻하지 않는다.
