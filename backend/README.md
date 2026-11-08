# backend · API·DB 제출 코드

`main-backup` 기준 커밋 `b8448d0`의 `develop/jihye/`에서 `app/`, `migrations/`, `tests/`, `pyproject.toml`, `uv.lock`을 복사했다. 제출본 테스트가 사용하는 `deploy.check_db`와 마이그레이션 안내의 상대 링크를 충족하도록 추적된 `deploy/` 실행·검증 자료도 추가 복사했다(환경 파일 제외). 개발 원본과 VM 배포 경로는 `develop/jihye/`에 유지한다.

이 폴더에서 `uv sync --frozen` 후 `uv run pytest -m "not integration"`으로 단위·계약 검사를 실행하고, `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`으로 서버를 시작한다. 실제 서비스에는 DB·내부 인증 등 환경 설정이 필요하다. DB 통합 검사는 전용 검증 DB와 명시적 실행 설정을 사용한다.

배포·초기화·백업 절차는 [개발 원본 배포 안내](../develop/jihye/deploy/README.md), 마이그레이션은 [migrations/README.md](migrations/README.md)를 따른다. 제출본에도 [배포·검증 자료](deploy/README.md)를 함께 둔다. VM Compose와 Dockerfile은 기존 원본 경로를 계속 사용한다.

가상환경·캐시·환경 파일·실제 DB 덤프는 취합하지 않았다. 기능 수정은 개발 원본에서 진행한 뒤 제출본에 반영한다.

W03 제출 경로 검사: 기존 개발 가상환경의 Python으로 `pytest -p no:cacheprovider -m "not integration" -q`를 실행해 163개 통과, DB 통합 검사 67개 제외를 확인했다. 실제 VM 배포·DB 통합 검사는 이번 이관에서 실행하지 않았다.
