# 지혜님 · 백엔드·DB·실행 환경

화면·워크플로우가 같은 신원·저장 규칙으로 연결되도록 FastAPI와 PostgreSQL 기반을 담당한다. 작업 위치는 저장소의 `develop/jihye/`이며 다른 담당·루트 공통 파일은 읽기만 한다.

## 현재 상태와 다음 작업

| 항목 | 현재 상태 |
| --- | --- |
| P0-1 | FastAPI 골격·설정·liveness·공통 입력 타입 구현. 실제 로컬 HTTP liveness 확인 |
| P0-2 | 웹14 operation(13경로)·내부3 API 모델·라우터·OpenAPI·시험 전용 Mock 구현 |
| P0-2 보완 | 2026-11-05 context 최대2,000자 누락과 개인 문서 기준 정리. 전체100개 통과·경고1건 |
| P0-3 | 전용 PostgreSQL 컨테이너·비밀 설정·접속·Alembic 기반 준비, 실제 DB 시험5개 통과. vector는 가용하지만 아직 활성화하지 않음 |
| 실제 기능 | 로그인·세션/내부키 검증·DB 저장·n8n/data-api 연결 미구현/미검증 |
| 현재 | P0-5 전용 DB 마이그레이션 `0004 (head)` 적용·RAG 테이블/그룹 역할 확인. 다음 단계는 P0-6 직원 seed·첫 관리자 |

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

- `GET /health/live` → `200 {"status":"ok"}`. P0-1 실제 소켓 확인은18000에서 수행했다. DB readiness는 P0-7 예정이며 현재 제공하지 않는다.
- `/docs`·`/openapi.json` 또는 `app.main.create_app().openapi()`로 계약을 볼 수 있다. 실제 업무 미구현은501, 보호 경로의 쿠키/키 누락은401, 임의 쿠키/키를 넣어도501이다. 실행 서버에 Mock 성공 기능은 없다.
- Mock은 `tests/conftest.py`의 dependency override·HTTPX MockTransport에만 있다. 정상5 route·400 codes·계정/저장 예시는 해당 시험 파일에 있다. 실제 서비스 경계는 `app/api/deps.py`다.
- 환경변수 이름은 `app/core/config.py`에서 읽고 `.env`는 자동으로 읽지 않는다. 기본 SERVICE_MODE=app이며 app/practice만 허용하지만 실제 저장 전환은 아직 없다. DB/키 없이 골격 기동 가능하며 실제 기능은 사용 경계에서 설정을 필수 검사해야 한다. 비밀값은 문서·응답·로그에 남기지 않는다.

## 지금 적용할 기준과 미확정 구분

- 질문trim1~500자, ID1~64자, attempt 엄격한 정수≥1, context 최대2,000자. context는 생략/null·빈 문자열 호환을 유지하며 trim/절단하지 않는다.
- 공개 가입 없음·관리자 발급·세션 신원. 쿠키는 oke_session/HttpOnly/SameSite=Lax/Path=/·기본8시간. 첫 변경 제한·회수·본인/최후 관리자 보호는 확정이며 실제 구현은P1-1이다.
- 비밀번호12자·문자3종은 모델 검사, 본인 이름/로그인ID 포함 금지는 실제 서비스에서 연결한다. 이력·잠금·외부OTP는P2다.
- support 연결3초·전체30초·자동 재시도0은 확정 초기 예산이며 실측 성과가 아니다. 응답 추가 필드·reason/timings·공통400 codes를 보존한다.
- PostgreSQL app/rag·vector3072·text-embedding-3-large·정확cosine/top_k3·assignee=IT직원 employees.id는 확정이다. 실제 DB는 P0-3~5 예정.
- H03 목록 DTO·patch 생략/null·Security nullable 세부와 추가 오류코드 등은 초안이다. 알림 ACK duplicate 유지·DLQ200은 사용자 전달 팀장 승인 수신 상태이며 공통 반영 커밋 확인·모델 보완은 별도다. 이번 P0-3에서는 응답 모델을 변경하지 않았다. data-api 문서 조회의 실제 구조·인증은 미확인이다.

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

P0-3 시점에는 빈 revision이었다. P0-4에서 격리 검증 DB에 `0001→0002`를 적용해 현재 `0002 (head)`와 업무 테이블 7개를 확인했다. 전체 155개 통과·기존 경고 1건이며 자세한 실행 결과는 [IMP-PLAN](Doc/IMP-PLAN.md)에 있다. RAG 테이블/grants는 P0-5에서 생성한다.

전용 DB는 healthy 상태로 남겼고 볼륨을 유지했다. 중지가 필요하면 `docker compose --env-file deploy/.env -f deploy/compose.yaml stop postgres`, 재개는 위 up 명령을 사용한다. 일상 중지/재시작에 `down -v`는 사용하지 않는다. 실제 업무 데이터의 재시작 유지·백업/복원은 후속 단계에서 확인한다.

## 팀원 인계와 다음 연결

[HANDOFF](Doc/HANDOFF.md)에 상대별 파일·예시·확인할 내용을 정리했다. P0-2 보완 커밋 fdcd265는 origin/feat/jihye-p0와 일치함을 직접 조회했다. 이번 P0-3은 아직 로컬 변경이며 새 커밋 생성 후 공유 기준을 갱신한다.

수언님은 웹 모델/화면, 다혁님은 C02 요청/응답, 원민님은 C05 저장 ACK를 대조한다. 유빈님은 DB 준비 후 rag 저장·검색을 연결하며 오현님은 공통 반영·VM 배포·최종 취합을 맡는다. 원민님 요청 표본7/7과 유빈님 회신은 사용자가 전달한 결과이고 이번 보완의 재확인·실연결 증거가 아니다. 외부 전송은 하지 않았다.

## 검증 이력과 참고 예제

최신 전체 시험은 전용 DB에서 **158 passed, 경고1건**이다(`uv run python deploy/check_db.py --all`). P0-3의 114개와 P0-4의 155개는 당시 이력이다. 일반 `uv run pytest -q`는 DB 시험 opt-in이 없으면 건너뛰므로 실제 DB 확인에는 위 명령을 사용한다. 기존 Starlette TestClient의 HTTPX 사용 폐기 예정 경고가 남는다. 초기 연결 실패·보안 조치·재시험은 [IMP-PLAN 실제 기록](Doc/IMP-PLAN.md)에 보존한다. 공통14종·최종 LLM3회 반복 시험 수와 구분한다.

[앱 예제](../../docs/references/qnaweb/src-be/app/main.py.example)·[모델](../../docs/references/qnaweb/src-be/app/models.py.example)·[라우터](../../docs/references/qnaweb/src-be/app/routers/qna.py.example)·[Compose](../../docs/references/qnaweb/docker/compose/docker-compose.yml.example)에서는 계층 분리만 참고한다. create_all/자동시드·JWT·InfluxDB·10명 예제 대신 Alembic/명시적bootstrap·세션·app/rag·제공6명 기준을 적용한다. 예제의 존재가 실제 기능 완료를 뜻하지 않는다.
