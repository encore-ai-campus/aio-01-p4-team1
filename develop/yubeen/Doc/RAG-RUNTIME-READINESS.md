# RAG 실행 환경 점검 · 2026-11-05

## 상태

- `PREPARED`: WSL AIO, `feat/yubeen-p0`, 담당 폴더의 Python 3.14.4 전용 `.venv` 준비. 앞선 작업에서 작성한 `Doc/REAL-DOC-INTEGRATION-READINESS.md`를 보존했다.
- `VERIFIED_FAKE`: 기존 HTTP Fake 및 Mock 회귀 시험만 통과. 실제 DB·OpenAI 성공으로 해석하지 않는다.
- `VERIFIED_LOCAL_REAL`: 미달성. 실제 DB 접속/pgvector 검색은 미실행.
- `VERIFIED_VM_REAL`: 미달성. 팀 VM 배포·n8n 실호출은 미실행.

## Python 및 임베딩

기존 폴더는 `python3 -m unittest` 실행 방식이고 패키지 선언이나 전용 가상환경이 없었다. `uv venv develop/yubeen/.venv`로 전용 환경을 만들고 `psycopg[binary]==3.3.8`을 설치해 import와 binary 구현을 확인했다. `.venv/`는 Git ignore 대상이다. 재현용 선언은 `requirements-runtime.txt`다. 시스템 Python은 변경하지 않았고 DB 연결은 시도하지 않았다.

현재 프로세스의 `OPENAI_API_KEY`는 미설정이다. 실제 임베딩 호출은 **BLOCKED_NO_API_KEY**, 호출 횟수 0회다. `OpenAIEmbeddingProvider`는 호출 때 환경 키를 읽어 `text-embedding-3-large`/3072/float 형식으로 전송하고 기존 `rag_index.validate_embedding`으로 응답을 검사한다. 코스 킷 일반 문서 청크는 실제 호출 입력 후보로만 준비할 수 있으며 권한 매핑이 최종 확정되기 전에는 전송하지 않는다. Fake 제공자 시험은 실제 API 성공 근거가 아니다.

## HTTP 설정·연결

`search_http.py`: `SEARCH_TEAM_KEY`가 없으면 시작 거절, `SEARCH_MODE=live`만 허용, `SEARCH_HOST` 기본 `127.0.0.1`, `SEARCH_PORT` 기본 `8765`. 요청은 X-Team-Key 인증·입력 검증 뒤 `OPENAI_API_KEY` 임베딩→`DATABASE_URL`의 읽기 전용 psycopg 연결→`rag_search.PgvectorSearchAdapter` 권한 SQL→C03 응답 순이다. DB URL 또는 API 키가 없으면 503/search_unavailable이며 Fake 결과로 전환하지 않는다. `all,it`는 검증된 직원 권한 전달 계약이 없어서 차단한다.

`oke-search.json`은 비활성이고 n8n의 `SEARCH_SERVICE_URL` 전체 내부 URL과 HTTP Header Auth Credential을 참조한다. URL이 실제 서비스에 닿는지, Credential 연결, n8n import/test는 미검증이다. `search.env.example`에는 변수 이름만 있으며 비밀값은 없다.

## DB 준비 후 순서

1. 지혜님에게 0004 DDL, 격리 DB 대상, 색인/검색 최소 권한 계정과 안전한 접속 경로를 받는다. 오현님에게 8개 문서 권한표 및 `security-incident.md`와 Q08 충돌 해결을 받는다.
2. 읽기 전용 계정으로 pgvector 확장, `rag.documents`/`rag.chunks` 컬럼·제약·3072차원·기존 건수와 권한을 확인한다. 실제 DDL과 색인/검색 SQL을 대조한다.
3. 승인된 키로 일반 문서의 짧은 청크 임베딩 1건을 호출해 모델·3072차원·유효값을 확인한다. 키·벡터는 기록하지 않는다.
4. 색인 대상과 쓰기 승인을 확인한 뒤 실제 8개 원본을 청킹·임베딩하고 문서 단위 트랜잭션으로 적재한다. 건수·해시·중복 재실행·실패 보존을 확인한다.
5. 일반 직원 `all` 검색과 IT 문서 차단을 확인한다. 검증된 IT 권한 전달 계약을 구현·확인한 뒤에만 IT 양성 검색을 시험한다.
6. 실제 HTTP 검색 200/빈200/503, n8n C03 호출, 다혁님 본체의 응답·이관, 마지막으로 팀 VM 경로를 각각 검증한다.

## 회귀

전용 `.venv`의 전체 Python unittest 171개 통과, JavaScript 16개(기존 Mock 13개와 비활성 실제 HTTP 워크플로우 3개) 통과. `git diff --check` 통과. 기존 기능 변경 없이 점검했고 실제 API·DB·VM 단계는 모두 미실행이다.
