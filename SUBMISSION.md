# 독립 제출본 · 실행과 검증

`main`의 루트 폴더에 실행에 필요한 코드·데이터·설정·평가 자료를 포함한다. 다른 브랜치, 개인 개발 폴더, 외부 강의 체크아웃을 파일 소스로 사용하지 않는다. 발표 자료와 개발 작업판은 제출 실행 경로에 포함하지 않는다.

## 실행

- 격리 로컬 Compose: [deploy/LOCAL-MAC.md](deploy/LOCAL-MAC.md).
- VM Compose와 환경 파일: [deploy/README.md](deploy/README.md).
- 백엔드: [backend/README.md](backend/README.md).
- 프론트엔드: [frontend/README.md](frontend/README.md).
- RAG 색인·검색: [rag/README.md](rag/README.md).

모든 애플리케이션 build context와 데이터 bind mount는 이 저장소 안의 루트 표준 폴더를 사용한다. VM의 기존 영속 볼륨·네트워크 식별자와 비공개 인증 설정은 배포 환경에서 제공한다. Docker 이미지·패키지 설치와 실제 LLM·임베딩 API는 실행 환경의 의존성이다.

## 저장소에서 재현하는 검사

저장소 루트에서 실행한다.

```sh
python3 -m compileall -q backend/ rag/ eval/
python3 -m unittest discover -s eval -p 'test_evaluation.py'
python3 eval/retrieval_check.py
python3 rag/rag_verify.py index --scenario initial-and-repeat --json
```

백엔드는 `backend/`에서 `uv sync --frozen` 후 `uv run pytest -p no:cacheprovider -m "not integration" -q`로 확인한다. DB 통합 검사는 전용 DB와 별도 실행 설정이 필요하다. 프론트엔드는 `frontend/`에서 `npx --yes pnpm@9.15.4 install --frozen-lockfile`, `npx --yes pnpm@9.15.4 typecheck`, `npx --yes pnpm@9.15.4 build`로 확인한다. 프론트엔드 `test` 스크립트에는 현재 테스트 파일이 없다.

`eval/`의 검색 Mock 검사는 합성 fixture·Mock workflow를 사용하며 실제 n8n·검색·티켓 API를 호출하지 않는다. 이를 실제 서비스 품질·공식 공통 시험 통과로 집계하지 않는다. 실제 실행 근거는 [runs/](runs/README.md), 판정과 한계는 [docs/EXECUTION-RESULT.md](docs/EXECUTION-RESULT.md)를 따른다.

과거 문서의 개발 경로는 당시 기록이다. 현재 코드·설정·검증은 이 문서와 각 루트 README만으로 확인한다. 키·비밀번호·세션·DB 덤프·가상환경·빌드 캐시는 제출하지 않는다.

## 실제 팀 VM 재검사

별도 강의 체크아웃 없이 현재 저장소의 `eval/live_check.py`, `eval/webhook_latency.py`, `eval/execution_profile.py`를 사용한다. 비공개 설정, 실행 명령, 쓰기 범위와 판정은 [실서버 검사 안내](eval/LIVE-CHECKS.md)를 따른다. API 검사만으로 DB 연결 성공을 기록하지 않으며, 팀 전용 검사 결과를 공식 공통 14종 전체 통과로 집계하지 않는다.
