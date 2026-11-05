# P0-1 원본 확인 실행 기록

- 단계/SPEC: P0-1 / RAG-01·02, 2026-11-04, 실행 ID p0-1-local-01.
- 환경: Python 3.14, 표준 라이브러리. 원본은 cases/source-inventory-mock.json의 합성 자료이며 실제 규정의 대체물이 아니다.
- 구현: tools/rag_prepare.py, cases/source-inventory-mock.json, tests/test_rag_prepare.py, Doc/SOURCE-MANIFEST.md, 이 문서.
- 작업 디렉터리: develop/yubeen. 외부 API·DB·임베딩·n8n 실행 없음.
- 명령: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`
- 결과: 정상·빈 문서·중복·권한 누락, LF 해시 동일성·코드 펜스 경계, 권한 충돌·본문 누락, 제한 정보 비노출의 4개 테스트 통과(종료 0).
- 최초 실행은 저장소 루트에서 수행해 tests 경로 ImportError(종료 1). 담당 폴더에서 같은 명령을 다시 수행해 위 결과를 확인했다.
- 명령: `python3 tools/rag_prepare.py inventory --source mock --input cases/source-inventory-mock.json --output Doc/SOURCE-MANIFEST.md`
- 결과: 종료 0, 목록 6건 중 후속 준비 가능 2건·거절 4건. 중복 키 두 항목 모두 거절. 미확인 권한 문서도 해시·길이는 조사했다. HTTP 결과는 해당 없음.
- 증거: SOURCE-MANIFEST.md 및 재현 가능한 테스트/Mock. 본문은 대장에 출력하지 않으며 it·미확인 문서 제목과 절 이름도 숨긴다.
- API 모드는 승인 없는 호출을 막고 안내 오류로 종료한다. 추후 승인 후 DATA_API_URL/DATA_API_KEY 기반 실제 응답 어댑터가 필요하다. 현재 Mock 구조는 참고 예제 기준이며 실제 API 구조 확인 완료가 아니다.
- 미실행: 실제 규정 8종·관리자 문서 확보, 실제 권한 근거 확인, 색인·검색·flow.py 검사. 워크플로우는 이번 단계 생성 대상이 아니다.
- 다음: P0-2에 로컬 대장/해시 규칙 전달 가능. 지혜님에게 실제 원본 응답과 권한 메타데이터 제공 여부 확인 필요(C06). 원민님·오현님에게 실제 8종 및 관리자 문서·권한 출처 미확인 전달 필요(H-Y02). 외부 전송·상대 동의 없음.

## P0-1 결함 보완 · 2026-11-04 · p0-1-local-02

기존 기록은 첫 구현 당시의 결과다. 위의 'API 모드 안내 종료'는 아래 구현으로 대체되었다. 실제 연동 미검증 상태는 유지한다.

### 기준 대조와 범위

GitHub main의 IMP-PLAN P0-1, SPEC RAG-01·02, HANDOFF H-Y02, API-CONTRACT, DATA-AND-DB를 읽고 로컬과 대조했다. 공통 DATA-AND-DB 4절에는 메타데이터 부재 시 일반 규정 8종 all 매핑이 확정되어 있다. H-Y02의 별도 버전 관리 매핑표는 제안 상태다. 일반 규정의 정확한 8개 doc_key는 공통 EVALUATION-GUIDE 1절을 사용한다. 관리자 문서는 실제 식별자가 확정되지 않아 제목/키워드로 추정하지 않는다. 메타데이터 충돌·알 수 없는 값은 매핑으로 덮지 않고 거절한다.

IMP-PLAN 확정 요구사항, 공통 파일, 다른 팀원 파일은 수정하지 않았다. 브랜치는 feat/yubeen-p0. P0-2 이후 구현, commit/push/merge, 실제 API/DB/LLM/n8n 호출 없음. 기준 대조를 위한 GitHub 읽기만 수행했다.

### 수정 파일과 동작

- tools/rag_prepare.py: 펜스 상태를 추적한 절 분석으로 변경. 실제 제목이 없으면 본문, 실제 절 앞 유효 내용만 서문. 빈 절 제목/순서를 길이 0으로 보존한다. 청크를 생성하지 않으므로 빈 절의 색인 가능 여부를 이 단계에서 확정하지 않는다. LF와 전체 본문 SHA-256 유지.
- 같은 도구: 환경변수 DATA_API_URL/DATA_API_KEY 기반 GET 수집과 주입 가능한 전송 계층 구현. 문서 키는 URL 경로 단위 인코딩, 타임아웃 10초, 재시도 없음, 리다이렉트 금지. 목록 실패는 실행 실패로, 문서별 HTTP/JSON/본문 오류는 해당 문서 거절로 기록한다. 원본 오류 본문/예외 문자열은 출력하지 않는다.
- 같은 도구: 문서별 조회 시각, 권한 출처·필드·값, 원본 경로와 해시 기록. Mock 파일의 원시 바이트 SHA-256을 대장에 기록한다. API 모드는 수집 스냅샷의 정렬 JSON 해시를 사용한다. 제한/미확인 제목·절 이름은 마스킹하며 본문은 어떤 문서도 출력하지 않는다. 설정된 API 키가 메타데이터에 반사되어도 대장에서 제거한다.
- tests/test_rag_prepare.py: 기존 4개 유지, 회귀·가짜 HTTP·CLI·표준 전송 계층 Mock 검사 22개 추가.
- Doc/SOURCE-MANIFEST.md: 같은 합성 입력으로 재생성. 조사 6항목, 준비 가능 2항목, 거절 4항목. 실제 색인 성공 수가 아니다.
- Doc/INDEX-RESULT.md: 결함, 구현 범위, 검증 및 미확인 사항 추가.

### 실제 검증

작업 디렉터리 develop/yubeen, Python 3.14, 표준 라이브러리. 입력은 cases/source-inventory-mock.json과 테스트 내 합성 HTTP 응답이다.

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`: 26개 통과, 종료 0. 최초 26개 실행에서 HTTPError 시험 객체의 ResourceWarning이 보여 시험 객체 close 처리를 추가했다. 아래 최종 재실행 결과를 기준으로 한다.
- 회귀 목록: 펜스 안 제목만 있는 문서, 제목 없는 문서, 빈 절 연속, 서문+정상 절, 공백 서문 제외, 펜스 길이/종류, LF/CR 정규화, 권한 충돌·누락 및 8종 매핑, 권한 출처 필드, 고정 시각의 대장 결정성, HTTP 성공/500/401/403, 타임아웃, JSON 오류, 목록/본문 형식·누락 필드, 설정 오류, URL 인코딩, 제한 정보·API 키 비노출, CLI 가짜 전송, urllib 오류 마스킹, 네트워크 없는 표준 전송과 리다이렉트 금지.
- `python3 tools/rag_prepare.py inventory --source mock --input cases/source-inventory-mock.json --output Doc/SOURCE-MANIFEST.md`: 종료 0.
- `git diff --check`: 종료 0. 최종 경로 검사로 수정/미추적 파일이 develop/yubeen 내부임을 확인한다.

### 완료 기준 판정

| 기준 | 판정 | 근거/남은 사항 |
| --- | --- | --- |
| 정상·빈 문서·중복·권한 누락 Mock 검사 | 충족 | 기존 4개 포함 회귀 통과 |
| 식별자·원본 경로·조회시각·LF 해시·절/길이 | Mock에서 충족 | 대장, 빈 절 포함; 실제 원본 미확인 |
| 권한 값·근거 또는 거절 사유 | Mock에서 충족 | 필드 출처 분리, 충돌 거절, 공통 매핑과 제안 구분 |
| 제한 본문·비밀값 비노출 | Mock에서 충족 | 보고서·오류/가짜 HTTP 검사; 실제 환경 미관측 |
| API 옵션·환경변수·구조 검증·오류 처리 | 구현 및 Mock 검증 충족 | 실제 네트워크 미사용 |
| 실제 응답 구조·8종 원본·관리자 문서 대조 | 미충족/미검증 | 실제 호출 금지, 관리자 키/제공 여부 미확인 |
| 누락/거절을 성공 건수에서 제외 | 충족 | Mock 2/4 분리, 실제 확보 성공으로 기록하지 않음 |

따라서 P0-1 코드 보완·Mock 검증은 완료했으나 실제 원본 확인을 포함한 P0-1 전체 완료는 선언하지 않는다. 어댑터는 참고 예제의 docs/name/title/text와 시험용 access_level을 명시적으로 지원하며 실제 응답 구조가 다르면 거절한다. X-Api-Key 헤더는 실제 data-api 계약으로 실측 확인되지 않은 어댑터 가정이다. 실제 승인 후 응답 구조/인증 방식 확인이 필요하다.

다음 연결: 지혜님(C06)은 실제 API 응답·인증 및 DB 매핑 입력의 적합성을, 원민님/오현님은 실제 8종과 관리자 문서의 식별자·권한 출처·누락을 확인해야 한다. H-Y02의 별도 매핑표는 승인/반영 완료로 처리하지 않았다. 결과는 이 문서와 SOURCE-MANIFEST이며 외부 전달·상대 확인은 수행하지 않았다.

## P0-1 최종 보안 점검 · 2026-11-04 · p0-1-local-03

이 절이 최신 상태이며 앞선 실행 이력은 보존한다. 담당 범위는 develop/yubeen의 P0-1이며 입력은 합성 Mock/가짜 HTTP, 출력은 안전한 원본 대장이다. 실제 서비스 호출은 하지 않는다.

- 발견: collect_api(environ=...)에서 주입한 키와 render의 os.environ 키가 다르면 제목 등에서 키가 노출될 수 있었다. 원본 응답 자체를 스냅샷 해시 입력으로 직렬화하는 것도 보완했다.
- 수정: 원본 본문으로 LF 해시·절 길이와 권한을 먼저 계산한다. 그 후 출력 허용 필드만 선택해 수집에 실제 사용한 키와 전역 키를 제거하고, 제한 문서 제목/절을 가린 안전한 대장 투영만 API 반환 스냅샷에 보관한다. 원문은 반환 스냅샷·출력·해시 입력용 JSON에 넣지 않는다. Mock 출력에도 직렬화 전에 같은 보호를 적용한다. 완성된 보고서의 문자열 치환에 의존하지 않는다.
- 스냅샷 해시 의미 변경: 원시 Mock 바이트/원본 API JSON 대신 안전한 대장 투영의 정렬 JSON SHA-256이다. 문서 source_hash는 원본 전체 본문의 LF 정규화 SHA-256 그대로다. 대장 투영 해시에는 조회시각이 포함되므로 시각이 바뀌면 달라진다. 고정 시각으로 결정성을 검증했다.
- 코드: tools/rag_prepare.py. 기존 26개 테스트를 유지하고 tests/test_rag_prepare.py에 보안 회귀 7개 추가. 주입/전역 키 불일치, 기본 환경 경로, 제목·권한 메타데이터·오류 반사, 제한 정보, Mock 직렬화 전 보호, 본문 해시 보존을 가짜 전송으로 확인한다.
- 실제 검증 명령(작업 디렉터리 develop/yubeen): `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`. 결과 33/33 통과, 종료 0.
- Mock 대장 재생성: `python3 tools/rag_prepare.py inventory --source mock --input cases/source-inventory-mock.json --output Doc/SOURCE-MANIFEST.md`. 조사 6항목/준비 가능 2항목/거절 4항목. 실제 확보·색인 성공 건수가 아니다.
- 최종 검사: git diff --check, git status, git diff 및 새 파일 내용 검토. 허용 경로 내 P0-1 파일만 반영 대상이다. IMP-PLAN은 이전 작업의 상태 안내 수정만 있고 확정 요구사항은 변경하지 않았다.

| P0-1 기준 | 최종 판정 |
| --- | --- |
| 정상·빈 문서·중복·권한 누락/충돌 | Mock 충족 |
| 식별자·조회 경로/시각·해시·절/빈 절/길이 | Mock 충족 |
| 권한 출처·필드·거절 근거 및 확정 매핑/제안 구분 | Mock 충족 |
| 누락/거절을 준비 가능 건수에서 제외 | Mock 충족 |
| API 환경변수·수집·오류 처리 | 구현 및 가짜 전송 검증 충족 |
| 수집 키 불일치·반사 및 제한 정보 비노출 | Mock 충족, 실제 환경 미관측 |
| 실제 응답 구조·인증·규정 8종·관리자 문서 | 미검증, 전체 완료 선언 불가 |

실제 API/DB/LLM/n8n 실행, P0-2 구현 없음. 규정 8종의 실제 본문/권한과 관리자 문서 식별자/제공 여부는 미확인이다. 지혜님에게 응답/인증 확인, 원민님·오현님에게 원본/권한 출처 확인이 필요하다. 외부 팀원에게 전송하거나 상대 동의를 기록하지 않았다. commit/push 결과는 실제 Git 명령 결과로 별도 보고한다.


## P1-1 Mock 색인 검증 실행 · 2026-11-04

실제 색인 미실행. 아래는 합성 임베딩·저장 더블의 결과다.

```json
{
  "mode": "mock",
  "scenario": "initial-and-repeat",
  "ok": true,
  "first": {
    "indexed": 4,
    "skipped": 0,
    "rejected": 1,
    "failed": 0
  },
  "second": {
    "indexed": 0,
    "skipped": 4,
    "rejected": 1,
    "failed": 0
  },
  "checks": {
    "repeat_unchanged": true,
    "content_hash_matches": true,
    "second_run_skips_all_stored": true,
    "fk_and_unique_valid": true,
    "embedding_failure_preserves_previous": true,
    "storage_failure_preserves_previous": true,
    "retry_succeeds": true
  },
  "stored_documents": 4,
  "actual_api_embedding_db_n8n": "not_executed"
}
```

## P1-1 구현 및 검증 범위 · 2026-11-04 · p1-1-local-01

### 선행 확인과 파일

환경은 AIO / feat/yubeen-p0 / 기준 커밋 38f3bfea7f7876e8204363ba01f75db9baf3af3b다. 시작 작업 트리는 깨끗했다. 루트·개인 AGENTS와 개인 README/SPEC/IMP-PLAN/HANDOFF/P0-2-RESULT, 공통 API·DB·RAG 및 협업 기준을 확인했다. 편집은 develop/yubeen 안에 한정하고 P0-1/P0-2 코드·테스트·정답표·기대값을 변경하지 않았다.

- workflows/oke-index.json: active=false의 수동 Mock 검증 워크플로우. 고정 Execute Command로 공통 Python 엔진의 합성 시나리오를 호출하고 안전한 건수/판정만 반환한다. 색인 로직·청킹을 JS로 복제하지 않는다. 현재 실제 문서 색인을 수행하는 운영 워크플로우는 아니다.
- config/rag-settings.json: text-embedding-3-large/3072차원, section/p0-2-v1/overlap0, cosine/top_k3, 임계값 null, 실제 실행 비활성 설정. 8000바이트 검토 기준은 P0-2와 같으며 토큰 모델 한도 실측값이 아니다.
- tools/rag_index.py: 공통 색인 엔진과 테스트 전용 MockStore, 외부 연결을 생성하지 않는 PostgreSQL DB-API DML 어댑터. DB DDL/마이그레이션/새 서버를 만들지 않는다.
- tools/rag_verify.py: Mock 검증 CLI. source=api는 real_index_execution_not_enabled/종료2로 거절한다. 실제 API·OpenAI·DB 드라이버/연결 생성 코드와 자격증명을 포함하지 않는다. --output은 기존 문서 뒤에 기록을 추가하며 기존 이력을 지우지 않는다.
- tests/test_indexing.py: P1-1 정상·실패·권한·트랜잭션·워크플로우 Mock 검사. 원래 테스트 63개는 보존한다.
- Doc/HANDOFF.md: 실제 연결에서 확인할 사항을 기록한다.

### 동작과 저장 경계

1. P0-1 inventory로 원본 식별자·권한·본문/제목을 검증한다. 마스킹된 prepared_rows 대장은 저장 입력으로 거절한다.
2. P0-2 chunk_document를 그대로 호출해 같은 content/content_hash/source_hash/metadata를 사용한다. complete만 저장 후보로 취급한다. partial/rejected는 문서 전체 성공이 아니며 기존 일반 성공본을 유지한다.
3. 변경 감지는 doc_key·title·access_level·source_url·source_hash, 청크 순서/해시/건수, 저장 모델/차원과 metadata.index_settings_hash를 비교한다. 설정 지문은 모델·차원·청킹·버전·overlap·길이 검토 기준이다. 같은 입력은 임베딩/교체 없이 skipped다.
4. 모든 청크의 응답 모델·길이3072·숫자·유한성·비영벡터를 검증한 후에만 replace를 호출한다. 실패를 부분 저장 성공으로 보고하지 않는다. 결과에는 원문·제목·벡터·키 대신 SHA-256 document_ref와 고정 상태/사유만 남긴다.
5. PostgreSQL 어댑터는 전용 autocommit=false 연결 하나의 cursor에서 문서 UPSERT RETURNING id → 기존 청크 DELETE → 새 청크 INSERT → commit 순서로 처리한다. 오류는 rollback한다. 문서 ID 유지, SQL 값 바인딩, rag.documents/rag.chunks 기존 컬럼만 사용한다. 설정 지문은 기존 metadata JSONB에 보존하며 새 컬럼은 요구하지 않는다. read에서는 vector_dims(embedding)로 저장 차원을 확인한다.
6. 권한 축소 all→it는 일반 실패 때 이전 공개본 보존과 충돌하므로 공통 DATA-AND-DB/RAG의 공개 청크 잔존 금지 기준을 우선한다. 청킹 전에 기존 공개 청크를 제거하는 suspend를 호출하고 permission_reduction_requires_review로 거절한다. 임의로 공개 상태를 유지하거나 자동 재개하지 않는다. 이 DML 경로는 Mock만 검증했다. 실제 검색 중지·권한·접속 장애·동시 변경 운영 확인은 남아 있다. 삭제 동기화/예약 갱신/복구 운영은 구현하지 않았다.

### 실제 실행한 확인

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`: 최종 89개(기존63+신규26) 통과. 초기 87개 통과 후, 검토 중 권한 축소와 긴 절이 동시에 발생할 때에도 공개 청크 중지가 우선해야 하는 순서 경계를 보완하고 주입 설정 검증을 추가했다. 두 회귀를 더해 89개 통과했다.
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/rag_verify.py index --scenario initial-and-repeat --output Doc/INDEX-RESULT.md`: 종료0. 위 JSON은 이 명령의 합성 결과다. 첫 실행 indexed4/rejected1, 두 번째 skipped4/rejected1. 이전 성공본 해시 유지, FK/고유키 대응, content/hash 일치, 임베딩 중간 실패 보존, 삭제 뒤 저장 실패 롤백, 재시도 성공을 Mock에서 확인했다.
- 실제 PostgreSQL 서버 대신 DB-API cursor/connection 더블로 한 연결의 commit/rollback 호출·SQL 바인딩·PK/컬럼 매핑을 검사했다. 실제 트랜잭션/FK/고유키/pgvector 검증 성공으로 취급하지 않는다.
- 워크플로우 JSON 구문·노드 참조·고정 명령·비활성/실행데이터 비저장 설정은 로컬에서 검사한다. 80일차 flow.py 키트는 확인한 저장소에 없다. 66~79일차 도구는 있으나 80일차 check 통과로 대체하지 않았다. 공식 flow.py check는 미실행이다.

### 미검증과 지혜님 확인 사항

- 현재 지혜님 migrations에는 README만 있어 실제 revision·확장·테이블·grant를 검증할 수 없다. 3072차원 vector, doc_key와 document_id/chunk_no 고유키, FK, metadata JSONB, updated_at, vector_dims 사용 가능 여부를 실제 마이그레이션에서 확인해야 한다.
- 실제 API 응답·X-Api-Key 인증·규정8종/관리자 원문·권한, 실제 임베딩 응답 어댑터/토큰 한도, DB 연결은 미검증이다. embedder 호출 규격은 (content,model,dimensions) → {model,embedding}; 실제 OpenAI 응답 매핑은 연결 시 필요하다.
- 전용 연결의 트랜잭션 소유권, INSERT/UPDATE/DELETE/SELECT와 시퀀스 권한, 실패 롤백·연결 단절 시 상태 확인, 공개 청크 중지 및 단일 색인 실행 운영을 지혜님과 실제 확인해야 한다. 새 DB 함수/DDL은 추가하지 않았다.
- n8n 실행 환경에 Python 및 /opt/oke-rag 경로로 담당 폴더 배치가 필요하다. Execute Command 노드가 해당 n8n 버전/보안 설정에서 허용되는지, 실행데이터 보관 설정과 읽기 전용 코드 배치, 80일차 키트 check, 사람의 등록·시험을 확인해야 한다. 공통 Compose를 수정하지 않았다. 기본 Mock 실행은 임시 테스트 저장 더블이며 PostgreSQL의 영속 저장을 대체하지 않는다.
- 실제 색인 경로를 n8n/원본 API/임베딩 Credential/PostgreSQL에 연결하는 작업은 남아 있다. 현재 CLI와 workflow는 이를 활성화하지 않으며 이번에는 실제 서비스 호출·n8n 등록·실행을 하지 않았다. P1-1 실제 색인 완료를 선언하지 않는다.

Mock 범위의 변경 감지·원자 교체 준비·실패 보존·차원/모델 검증은 완료했다. 실제 원본/권한/DB/워크플로우 연결과 통합 검증은 미완료다. commit/push/merge/P1-2 구현은 수행하지 않았다.


## P1-1 Mock 색인 검증 실행 · 2026-11-04

실제 색인 미실행. 아래는 합성 임베딩·저장 더블의 결과다.

```json
{
  "mode": "mock",
  "scenario": "initial-and-repeat",
  "ok": true,
  "first": {
    "indexed": 4,
    "skipped": 0,
    "rejected": 1,
    "failed": 0
  },
  "second": {
    "indexed": 0,
    "skipped": 4,
    "rejected": 1,
    "failed": 0
  },
  "checks": {
    "expected_first_counts": true,
    "expected_second_counts": true,
    "stored_documents_present": true,
    "fault_scenarios_executed": true,
    "repeat_unchanged": true,
    "content_hash_matches": true,
    "second_run_skips_all_stored": true,
    "fk_and_unique_valid": true,
    "embedding_failure_preserves_previous": true,
    "storage_failure_preserves_previous": true,
    "retry_succeeds": true
  },
  "stored_documents": 4,
  "actual_api_embedding_db_n8n": "not_executed"
}
```

## P1-1 독립 검증 결함 보완 · 2026-11-04 · p1-1-local-02

이 절이 최신 보완 상태다. 앞의 89개 테스트 기록과 최초 권한 중지 설명은 당시 실행 이력으로 보존하며, 권한 중지/재개·동시성·검증 성공 판정·연결 실패 처리는 아래 내용으로 정정한다. 실제 서비스 검증 완료로 바꾸지 않는다.

### 결함별 수정

- A / P0 권한 축소 누락: confirmed_restricted_permission은 목록에서 유일한 doc_key의 명시 권한과, name이 일치하는 본문 응답의 명시 권한만 확인한다. 충돌·미확인·중복 또는 다른 문서 본문의 it를 근거로 권한을 바꾸지 않는다. 확인된 it이면 본문/제목 검증 실패보다 기존 공개본 중지를 먼저 처리한다. 중지 처리 오류는 failed이며 정상 rejected/indexed로 숨기지 않는다.
- B / P0 동시 변경: read 당시 version_token(기존 문서 열·updated_at·청크 상태)을 임베딩 준비 후 replace에 전달한다. Mock은 RLock 안에서 비교·교체한다. PostgresStore는 같은 문서 키의 pg_advisory_xact_lock(hashtextextended(...))과 SELECT FOR UPDATE를 저장 트랜잭션 안에서 획득한 후 버전을 비교한다. 불일치는 stale_document_version으로 쓰기 전 거절한다. 신규 행은 INSERT ON CONFLICT DO NOTHING을 사용해 외부 INSERT 충돌에도 덮어쓰지 않는다. 기존 행은 잠긴 PK를 UPDATE하므로 ID를 유지한다. DDL/새 컬럼/새 DB 함수는 만들지 않았다.
- C / P1 검증 성공 오판: 기본 합성 시나리오 최초 indexed4/rejected1/failed0과 재실행 skipped4/rejected1/failed0, 저장4문서, 필수 장애 시나리오 수행 여부를 명시적으로 검사한다. 장애 검사 기본값은 false이며, 빈 저장 집합의 all([])는 성공이 아니다. 임베딩 전체 실패 시 ok=false, CLI 종료1이다.
- D / P1 Mock/DB 불일치: 양쪽 suspend는 문서 ID/행을 보존하고 권한을 it로 축소하며 청크를 제거한다. 기존 행에 청크가 없으면 index_suspended_requires_review로 자동 재색인을 막는다. 재개 승인 조건·작업 주체·구체 절차는 공통에 정의되지 않아 미결정이며 재개 기능은 구현하지 않았다. 이전 기록의 'Mock 문서 삭제' 의미와 자동 재개 가능성은 이 수정으로 제거했다.
- E / P1 rollback/연결 실패: 소유권을 넘겨받은 전용 autocommit=false 연결의 _transaction으로 처리를 통일했다. SQL 실패 후 rollback 성공은 고정 storage_*_failed, rollback 실패는 storage_rollback_failed, commit 예외는 storage_commit_unknown이다. 후자의 두 경우 연결을 close하고 usable=false로 만들어 재사용을 차단한다. close 자체 실패도 원문을 출력하지 않는다. SQLSTATE08/닫힌 연결도 폐기한다. commit ACK가 불명확할 때 rollback 성공·이전 성공본 보존을 주장하지 않는다.

### 회귀 테스트 및 실제 실행

수정 파일: tools/rag_index.py, tools/rag_verify.py, tests/test_indexing.py, 이 문서, Doc/HANDOFF.md. 기존 P0-1/P0-2 소스·테스트·정답표·공통 파일은 수정하지 않았다. 원래 P1-1의 기존 테스트 26개도 유지했다. 그중 두 권한 중지 테스트의 잘못된 '문서 삭제' 기대는 '같은 행의 it/빈 청크 유지'로 정정했고, SQL 테스트의 고정 쿼리 수·실패 주입 위치·read 행 모양은 잠금 및 updated_at 추가에 맞췄다. 실패 보존·바인딩·PK/commit/rollback 검증 목적은 유지했다.

- 전체 회귀: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`와 최종 재실행에서 총108개 통과(기존89 + 신규19), 종료0. 중간 89/105개 실행도 통과했다.
- 신규19개: 빈/공백 본문·잘못된 제목의 권한 축소, 출처 미확인·충돌 권한 불변, 중지 실패 failed, ID/중지 상태 재실행 보존, 임베딩 중 권한 변경, 버전 변경, 두 스레드 경합, 임베딩 전체 실패 및 종료1, 빈 fixture 성공 금지, rollback 실패·연결폐기, commit 불명확·close 실패, 정상 rollback 고정 오류, SQLSTATE08 폐기, 트랜잭션 내 잠금/CAS 순서, 신규 INSERT 충돌, DB 중지 SQL의 행 보존, 기존 PK 잠금 UPDATE/바인딩, read commit 불명확, 엔진의 commit 불명확 상태 보고.
- 정상 CLI: `PYTHONDONTWRITEBYTECODE=1 python3 tools/rag_verify.py index --scenario initial-and-repeat --json` → ok=true/종료0, 최초4색인·1거절, 재실행4건너뜀·1거절. --output 명령으로 위 JSON을 기존 이력 뒤에 추가했다.
- 실패 CLI: 별도 Python subprocess에서 mock_embed 전체 예외를 주입 → ok=false, failed4, 종료1. 실제 API 호출 없이 확인했으며 합성 원본 예외 문자열이 stdout/stderr에 없었다.
- 동시성은 Mock 두 스레드와 DB-API 더블의 SQL 실행 순서로만 확인했다. 실제 PostgreSQL 잠금 대기·격리 수준·deadlock·연결 복구는 미검증이다.

### 남은 미검증·위험과 완료 판정

P1-1 Mock의 지적된 다섯 결함은 회귀 범위에서 보완했다. 실제 PostgreSQL·원본 API·OpenAI·n8n은 호출하지 않았다. 실제 색인 완료/실제 트랜잭션 PASS를 선언하지 않는다. n8n 파일은 여전히 비활성 Mock 래퍼이며 공식 80일차 flow.py check는 미실행이다.

모든 색인 쓰기 경로가 같은 문서 잠금 규약을 따라야 한다. 어댑터를 우회해 청크를 직접 수정하는 외부 작업, 원본 API 자체의 오래된 권한/버전 순서, 실제 격리 수준의 보장은 지혜님과 확인해야 한다. 신규 데이터 무결성은 기존 고유키/FK에 의존하며 실제 DDL·권한은 미검증이다.

공개 청크 중지 자체가 DB 장애로 실패하거나 결과가 불명확하면 결과는 failed/고정 실패 코드다. 이때 공개 청크가 제거됐다고 주장할 수 없다. 실제 서비스에서 검색 중단/운영 확인을 강제하는 수습 절차는 아직 없으므로 실제 배포 전 합의·검증이 필요하다. 원본 권한 출처를 확인할 수 없는 입력으로 기존 권한을 임의 변경하지 않는다.

연결 소유권은 전용 연결을 어댑터에 이전한다는 전제다. 풀/공유 연결을 직접 넘기면 안 된다. 풀을 쓸 경우 소유자 측의 물리 연결 폐기·대여 해제 규약이 추가로 필요하다. 실패 연결의 상태 재확인/재접속·중지 문서 재개 정책은 미결정이며 자동 재개는 하지 않는다.

P1-2는 계약/Mock 설계 준비만 조건부 가능하다. 실제 검색 연계는 위 DB 동시성·권한 중지·재개 정책과 실제 원본·권한·색인 확인 이후에 검증해야 한다. 이번에 P1-2 구현·외부 전달·commit/push/merge는 수행하지 않았다.

## 개인 n8n 실행 환경 보완 및 Mock 실행 · 2026-11-04

이번 기록은 앞선 Python Mock 검증과 별도로 수행한 개인 n8n 실행 환경 확인이다. 실제 원본 API·OpenAI·PostgreSQL 색인 검증은 여전히 미실행이다. 기존 Python 엔진·설정·워크플로우 원본 JSON은 수정하지 않았다.

### 적용 범위와 백업

- 환경: AIO, feat/yubeen-p0, 개인 Compose `/home/yubeen/day65-n8n/compose.yml`, n8n `day65-n8n-n8n-1`/2.42.6.
- 추가 백업: `/home/yubeen/n8n-backup/p1-1-runtime-20261104-181408/`. 비공개 디렉터리에 Compose·환경 파일·n8n 전체 데이터·변경 전 대상 워크플로우를 보관했다. 비밀 파일과 실제 값은 프로젝트에 복사하지 않았다.
- n8n만 정상 중지한 상태에서 데이터 전체를 복사했다. SQLite `integrity_check=ok`, 압축 백업 재추출 후 DB 내용 비교, 암호화 config 해시를 확인했다. 실제 복구용 볼륨 전환 시험은 수행하지 않았다.
- 기존 `day65-n8n_n8n-data` 볼륨을 유지했다. 다른 실습 컨테이너 4개의 ID와 서비스 설정은 바뀌지 않았다.

### 환경 및 저장된 워크플로우 수정

- 개인 폴더의 `Dockerfile.oke-rag`는 기존 n8n 2.42.6 베이스 다이제스트를 유지한다. 별도 Alpine 3.24 빌드 단계에서 Python 3.14.10을 준비하고 `/opt/oke-python`에 배치한다. n8n의 고정 시스템 라이브러리를 변경하지 않는다.
- 최초 시스템 패키지 직접 설치 빌드는 고정 libexpat 의존성 충돌로 실패했다. 이 이미지는 적용하지 않았으며, 독립 런타임 방식의 후속 빌드와 검증이 성공한 뒤 적용했다.
- `.dockerignore`로 환경 파일 등을 빌드 컨텍스트에서 제외했다. 개인 Compose의 n8n 서비스에만 이미지/빌드 설정, `NODES_EXCLUDE=["n8n-nodes-base.localFileTrigger"]`, 담당 폴더의 `/opt/oke-rag:ro` 마운트를 추가했다. 기존 external Runner 구성과 데이터 볼륨은 유지했다.
- 실제 노드 캐시 `/home/node/.cache/n8n/public/types/nodes.json`에서 Manual Trigger·Execute Command·Code 등록을 확인했다. Local File Trigger는 제외되어 있다. `/healthz`는 HTTP 200이다. 인증이 필요한 `/types/nodes.json`의 익명 요청은 401이므로, 해당 요청을 노드 확인 성공으로 계산하지 않았다.
- 저장된 `oke-index` 1건은 노드/명령은 원본과 같지만 connections가 비어 있었다. 기존 ID·노드 ID·설정을 유지하고 공식 `n8n import:workflow`로 원본의 연결 2개를 복원했다. 명령 종료 0, 1건 Import를 확인했으며 비활성 상태를 유지했다. DB 직접 UPDATE는 하지 않았다.
- 최종 비교: 워크플로우 38개 유지, 다른 37개는 행 전체가 동일하다. 대상은 connections·meta·versionId가 바뀌었고 기존 노드는 동일하다. 사용자 1명의 행은 CLI 처리 후 updatedAt만 변경됐으며 다른 계정·인증 값은 동일하다. Credential 4건·소유권·프로젝트·암호화 config는 동일하다. SQLite 무결성도 정상이다.

### 실제 실행 결과와 한계

| 검증 | 실제 결과 |
| --- | --- |
| 호스트 전체 unittest | 108개 통과, 종료 0 |
| 실제 n8n 컨테이너의 읽기 전용 마운트에서 전체 unittest | 108개 실행 중 임시 파일을 tests 아래에 쓰는 3개가 읽기 전용 오류. 원본·테스트·마운트 권한은 바꾸지 않음 |
| 동일 컨테이너 /tmp 복사본에서 전체 unittest | 108개 통과, 종료 0. 임시 복사본은 자동 정리 |
| 실제 n8n 컨테이너에서 `python3 /opt/oke-rag/tools/rag_verify.py index --source mock --scenario initial-and-repeat --json` | 종료 0, mode=mock, ok=true. 최초 indexed=4/rejected=1/failed=0, 재실행 skipped=4/rejected=1/failed=0. 모든 checks=true |
| 네트워크 none인 임시 컨테이너에서 같은 Mock 명령 | 종료 0, ok=true |
| 격리 n8n 2.42.6의 공식 Import 및 execute CLI | 종료 0. 수동 시작 → Python Mock → 안전한 검증 결과의 세 노드 모두 실행, 최종 ok=true |

격리 워크플로우 시험은 임시 데이터와 internal JavaScript Runner를 사용했다. 기존 n8n의 external Runner를 사용하는 브라우저 수동 실행 및 실제 화면 렌더링은 직접 검증하지 않았다. 이 결과를 해당 경로의 실행 성공으로 확장하지 않는다. 검증 CLI의 고정 필드 `actual_api_embedding_db_n8n=not_executed`는 검증기 자체의 외부 연동 상태이며, 이번에 별도로 수행한 n8n Mock 실행은 위 표로 구분한다.

저장된 연결까지 복원했으므로 기존 n8n 화면을 새로고침해 다시 열면 되며, 별도 재Import는 필요하지 않다. 오래된 편집 화면을 그대로 저장해 연결 복원 내용을 덮어쓰지 않는다. 실제 화면에서 세 노드·연결선 2개·수동 실행 결과를 사람이 확인하는 절차는 남아 있다.

개인 환경의 변경·복구 절차는 `/home/yubeen/day65-n8n/P1-1-RECOVERY.md`에 기록했다. 설정 복구는 백업 Compose로 같은 볼륨을 사용하는 n8n만 재생성하는 방식이며, 데이터 삭제·volume prune·사용자 초기화는 하지 않는다. 실제 원본/권한, OpenAI 임베딩, PostgreSQL 저장/동시성/복구 및 실제 색인 완료는 미검증이다. P1-2 구현·commit·push·merge·팀원 메시지 전송은 하지 않았다.
