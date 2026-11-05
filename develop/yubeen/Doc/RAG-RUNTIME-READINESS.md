# RAG 실행 환경 점검 · 2026-11-05

## 상태

- `PREPARED`: WSL AIO, `feat/yubeen-p0`, 담당 폴더의 Python 3.14.4 전용 `.venv` 준비. 앞선 작업에서 작성한 `Doc/REAL-DOC-INTEGRATION-READINESS.md`를 보존했다.
- `VERIFIED_FAKE`: 기존 HTTP Fake 및 Mock 회귀 시험 통과. 이는 아래 실제 임베딩 응답과 별개의 검증이다.
- 실제 임베딩 API 1건: 사용자 제공 실행 결과 기준 HTTP 200, `text-embedding-3-large`, 3072차원 및 기존 검증 함수 통과. 실제 DB 검색 상태 등급으로 승격하지 않는다.
- `VERIFIED_LOCAL_REAL`: 미달성. 실제 DB 접속/pgvector 검색은 미실행.
- `VERIFIED_VM_REAL`: 미달성. 팀 VM 배포·n8n 실호출은 미실행.

## Python 및 임베딩

기존 폴더는 `python3 -m unittest` 실행 방식이고 패키지 선언이나 전용 가상환경이 없었다. `uv venv develop/yubeen/.venv`로 전용 환경을 만들고 `psycopg[binary]==3.3.8`을 설치해 import와 binary 구현을 확인했다. `.venv/`는 Git ignore 대상이다. 재현용 선언은 `requirements-runtime.txt`다. 시스템 Python은 변경하지 않았고 DB 연결은 시도하지 않았다.

이전 Codex 작업 프로세스에서는 `OPENAI_API_KEY`가 보이지 않아 **BLOCKED_NO_API_KEY**, 호출 0회로 기록했다. 이후 사용자 제공 실행 결과에 따르면 별도 환경에서 키를 확인하고 기존 임베딩 코드로 실제 OpenAI API를 1회 호출했다. 최초 DNS 오류는 네트워크 권한 승인 후 해결됐으며, 최종 응답은 HTTP 200, 모델 `text-embedding-3-large`, 임베딩 3072차원, 유한 숫자·0벡터 아님·기존 RAG 검증 함수 모두 PASS다. Fake/Mock 응답이 아니다. 이번 문서 반영 과정에서는 API를 재호출하지 않았으며 원본 요청·응답 로그나 실행 명령은 제공되지 않아 독립 재검증하지 않았다. 키·전체 벡터·요청 헤더는 기록하지 않는다.

`OpenAIEmbeddingProvider`는 호출 때 환경 키를 읽어 `text-embedding-3-large`/3072/float 형식으로 전송하고 기존 `rag_index.validate_embedding`으로 응답을 검사한다. 실제 임베딩 성공은 DB 연결·색인·pgvector 검색 성공을 뜻하지 않는다.

## HTTP 설정·연결

`search_http.py`: `SEARCH_TEAM_KEY`가 없으면 시작 거절, `SEARCH_MODE=live`만 허용, `SEARCH_HOST` 기본 `127.0.0.1`, `SEARCH_PORT` 기본 `8765`. 요청은 X-Team-Key 인증·입력 검증 뒤 `OPENAI_API_KEY` 임베딩→`DATABASE_URL`의 읽기 전용 psycopg 연결→`rag_search.PgvectorSearchAdapter` 권한 SQL→C03 응답 순이다. DB URL 또는 API 키가 없으면 503/search_unavailable이며 Fake 결과로 전환하지 않는다. `all,it`는 검증된 직원 권한 전달 계약이 없어서 차단한다.

`oke-search.json`은 비활성이고 n8n의 `SEARCH_SERVICE_URL` 전체 내부 URL과 HTTP Header Auth Credential을 참조한다. URL이 실제 서비스에 닿는지, Credential 연결, n8n import/test는 미검증이다. `search.env.example`에는 변수 이름만 있으며 비밀값은 없다.

## DB 준비 후 순서

1. 지혜님에게 0004 DDL, 격리 DB 대상, 색인/검색 최소 권한 계정과 안전한 접속 경로를 받는다. 오현님에게 8개 문서 권한표 및 `security-incident.md`와 Q08 충돌 해결을 받는다.
2. 읽기 전용 계정으로 pgvector 확장, `rag.documents`/`rag.chunks` 컬럼·제약·3072차원·기존 건수와 권한을 확인한다. 실제 DDL과 색인/검색 SQL을 대조한다.
3. 앞서 보고된 실제 임베딩 1건 결과를 별도 근거로 보존하고, 색인 대상과 쓰기 승인을 확인한 뒤 실제 8개 원본을 청킹·임베딩하여 문서 단위 트랜잭션으로 적재한다. 건수·해시·중복 재실행·실패 보존을 확인한다.
4. 일반 직원 `all` 검색과 IT 문서 차단을 확인한다. 검증된 IT 권한 전달 계약을 구현·확인한 뒤에만 IT 양성 검색을 시험한다.
5. 실제 HTTP 검색 200/빈200/503, n8n C03 호출, 다혁님 본체의 응답·이관, 마지막으로 팀 VM 경로를 각각 검증한다.

## 회귀

앞선 실행 환경 점검에서 전용 `.venv`의 전체 Python unittest 171개, JavaScript 16개(기존 Mock 13개와 비활성 실제 HTTP 워크플로우 3개)가 통과했다. 이 문서 갱신에서는 코드를 변경하거나 테스트·API·DB를 재실행하지 않았다. 실제 임베딩 1건 결과는 위 사용자 제공 기록이며 DB 검색·n8n·VM 단계는 미실행이다.
