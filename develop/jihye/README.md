# 지혜님 · 백엔드·DB·실행 환경

화면·워크플로우가 같은 신원·저장 규칙으로 연결되도록 FastAPI와 PostgreSQL 기반을 담당한다. 작업 위치는 저장소의 `develop/jihye/`이며 다른 담당·루트 공통 파일은 읽기만 한다.

## 현재 상태와 다음 작업

| 항목 | 현재 상태 |
| --- | --- |
| P0-1 | FastAPI 골격·설정·liveness·공통 입력 타입 구현. 실제 로컬 HTTP liveness 확인 |
| P0-2 | 웹14 operation(13경로)·내부3 API 모델·라우터·OpenAPI·시험 전용 Mock 구현 |
| P0-2 보완 | 2026-11-05 context 최대2,000자 누락과 개인 문서 기준 정리. 전체100개 통과·경고1건 |
| 실제 기능 | 로그인·세션/내부키 검증·DB 저장·n8n/data-api 연결 미구현/미검증 |
| 다음 | 보완 커밋 기준 팀원 인계·회신 확인, 다음 지정 구현은 P0-3 DB 실행 기반 |

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
- H03 목록 DTO·patch 생략/null·Security nullable 세부와 추가 오류코드 등은 초안이다. 알림 ACK duplicate 확장·DLQ200 명문화는 H07 공통 반영 대기다. data-api 문서 조회의 실제 구조·인증은 미확인이다.

## 팀원 인계와 다음 연결

[HANDOFF 현재 인계 패키지](Doc/HANDOFF.md#현재-인계-패키지--2026-11-05)에 상대별 파일·예시·확인할 내용을 정리했다. 기존 P0-2 커밋은4bbbf49이며 보완 커밋은 생성 후 공유 기준으로 갱신한다.

수언님은 웹 모델/화면, 다혁님은 C02 요청/응답, 원민님은 C05 저장 ACK를 대조한다. 유빈님은 DB 준비 후 rag 저장·검색을 연결하며 오현님은 공통 반영·VM 배포·최종 취합을 맡는다. 원민님 요청 표본7/7과 유빈님 회신은 사용자가 전달한 결과이고 이번 보완의 재확인·실연결 증거가 아니다. 외부 전송은 하지 않았다.

## 검증 이력과 참고 예제

최신 시험은 **100 passed, 경고1건**이다. 기존 P0-1~2의75개에 context 회귀25개를 추가했다. 기존 Starlette TestClient의 HTTPX 사용 폐기 예정 경고가 남는다. 설치 버전·과거30/75개 결과·초기 실패와 재확인·최신 명령은 [IMP-PLAN 실제 기록](Doc/IMP-PLAN.md)에 보존한다. 자체 pytest 수는 공통14종·최종 LLM3회 반복 시험 수와 구분한다.

[앱 예제](../../docs/references/qnaweb/src-be/app/main.py.example)·[모델](../../docs/references/qnaweb/src-be/app/models.py.example)·[라우터](../../docs/references/qnaweb/src-be/app/routers/qna.py.example)·[Compose](../../docs/references/qnaweb/docker/compose/docker-compose.yml.example)에서는 계층 분리만 참고한다. create_all/자동시드·JWT·InfluxDB·10명 예제 대신 Alembic/명시적bootstrap·세션·app/rag·제공6명 기준을 적용한다. 예제의 존재가 실제 기능 완료를 뜻하지 않는다.
