# backend · FastAPI·DB

`app/`, `migrations/`, `tests/`, 의존성·잠금 파일과 `deploy/`에 실행·검증 자산을 포함한다.

이 폴더에서 `uv sync --frozen` 후 `uv run pytest -p no:cacheprovider -m "not integration" -q`로 단위·계약 검사를 실행한다. 서버는 `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`으로 시작한다. 실제 서비스에는 DB·내부 인증 등 비공개 환경 설정이 필요하다.

통합 배포는 [루트 배포 안내](../deploy/README.md), 백엔드 전용 초기화·백업·전용 DB 검사는 [deploy/README.md](deploy/README.md), 마이그레이션은 [migrations/README.md](migrations/README.md)를 따른다. 공통 VM Compose의 build context는 이 `backend/`다. DB 통합 검사는 격리된 검증 DB에서만 명시적으로 실행한다.
