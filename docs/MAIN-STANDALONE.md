# W03 독립 제출본 정리 결과 · 2026-11-08

이관 전 기준은 `c153511`이다. main의 배포·CI·코드·데이터·오프라인 평가 자산을 루트 표준 경로로 연결하고 `develop/`, `slides/`, `tools/`, `team-tasks/`를 저장소와 작업 디렉터리에서 제거했다.

## 변경

- CI: 루트 `workflows/*.json`, `cases/*.json` 검사, `backend/ rag/ eval/` 컴파일, `frontend/`의 고정 pnpm 설치·타입 검사·빌드.
- VM·로컬 Compose: `backend/`, `frontend/`, `rag/` build context와 해당 Dockerfile 상대 경로. RAG env·권한 경로도 `rag/`로 이동.
- RAG: `config/rag-settings.json` 포함, 설정 로더의 기준 경로 수정. 규정 8종을 루트 `knowledge/`에서 읽고 안내 README만 제외하며 미승인 추가 파일은 거절.
- 제공 API: `data/`, `knowledge/`, `prompts/` 사용. 스키마 3개를 `data/schemas/`에 포함하고 VM·로컬 마운트를 동일하게 적용.
- 평가: 필요한 RAG 사례·합성 검색 fixture·Mock 워크플로우를 `cases/`·`eval/`에 포함. 테스트·CLI가 루트 `rag/`·`requests/`를 사용.
- 로컬 초기화: 다른 강의 체크아웃 없이 이 저장소 규정 해시를 검증. 루트 안내·현재 아키텍처·실행 문서도 갱신.
- 비공개 RAG 환경 파일과 TypeScript 빌드 캐시를 Git 제외 규칙에 추가.

## 직접 검증 결과

| 검사 | 결과 |
| --- | --- |
| `python3 -m compileall -q backend/ rag/ eval/` 및 deploy·data-api 컴파일 | PASS; pycache는 저장소 밖에 기록 |
| 백엔드 `uv sync --frozen` 후 `pytest -p no:cacheprovider -m "not integration" -q` | 163 passed, DB 통합 67 deselected; 기존 Starlette 경고 1개 |
| `python3 -m unittest discover -s eval -p 'test_evaluation.py'` | 30개 PASS |
| `python3 eval/retrieval_check.py` | 21/21 PASS, 로컬 합성 Mock |
| `rag_verify.py index --scenario initial-and-repeat --json` | 재색인 멱등성·임베딩/저장 실패 시 보존·재시도 PASS |
| 승인 규정의 fake 색인 | 8문서·33청크, 실패/거절 0; 예상 밖 파일 거절 확인 |
| 제공 API HTTP smoke | 직원 6명, 규정 8개·README 제외/404, 프롬프트 p1~p3, 스키마 3개 조회 PASS |
| 로컬 초기화의 규정 해시 검사 | 8개 PASS, 저장소 내부 자료만 사용 |
| VM/로컬 Compose | `config --no-interpolate --no-env-resolution --quiet` PASS; 앱 build context·Dockerfile·데이터/권한 mount의 실제 파일 존재 확인 |
| 프론트엔드 TypeScript·Next.js 프로덕션 빌드 | PASS |
| 루트 context의 backend/frontend/RAG Docker 이미지 빌드 | 3종 PASS, 검증용 `oke-submission-*:verify` 태그 사용 |
| 추가 이관 자산 | 12개 원본 바이트 일치 |
| 삭제 경로 참조 검사 | 실행 코드·배포·CI 설정에 제거한 폴더 의존성 없음 |

실제 VM 배포·재시작·DB 통합·유료 API 호출·실서비스 품질 재평가는 수행하지 않았다. 기존 운영 결과와 과거 개발 경로는 당시 이력이며 이번 검사 결과로 대체하지 않는다. 현재 실행 명령은 [SUBMISSION](../SUBMISSION.md)과 [배포 안내](../deploy/README.md)를 따른다.

다음 VM 재생성 전 비공개 환경 파일을 `backend/deploy/.env.backend`, `rag/.env.openai`, `rag/search.env`, `rag/index.env`에 준비하거나 Compose 환경 변수로 위치를 지정해야 한다. 기존 VM 볼륨·네트워크 이름과 비밀값은 변경하지 않았다.

## 후속 폴더 정리 · 2026-11-08

- 공식 제출 구조에 맞춰 데일리 3장과 안내를 `docs/daily/`로 이동하고 내부 링크·README 트리·헌장·구조 문서를 갱신했다. 일일 기록 본문과 당시 이력은 보존했다.
- `data-api/data/`의 중복 사본 22개를 제거했다. 루트 `data/`·`knowledge/`·`prompts/`와 바이트 일치를 먼저 확인했으며 루트 원본·API·Compose 데이터 경로는 변경하지 않았다.
- 중복 `eval/rag_evaluate.py`를 제거하고 기존 `rag/rag_evaluate.py`를 공통 구현으로 유지했다. RAG 실행 코드와 평가 테스트가 같은 구현을 사용한다.
- 평가·검사 회귀 41개, 합성 검색 Mock 21/21, Mock 색인·재색인 검사를 통과했다. 제공 API의 직원 6명·규정 8종·FAQ 6종·기존 티켓 4건·스키마 3종·프롬프트 3종 조회도 확인했다. 이 단계에서 실제 VM을 재배포하거나 재시작하지 않았다.

추가 구현 폴더의 재배치 검토는 별도 후속 범위로 남겼다.
