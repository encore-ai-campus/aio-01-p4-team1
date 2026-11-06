# 팀 VM RAG 통합 실행 가이드 · 준비본

상태: **PREPARED**. 이 가이드를 작성하면서 VM, PostgreSQL, OpenAI, n8n에 접속하지 않았다. 오현님이 전달한 VM 구성은 계획·확정 정보이며 이 체크아웃에서 독립 실행 검증한 결과가 아니다. 비밀값과 실제 접속 주소는 저장소에 적지 않는다.

## 사전 조건과 차단 게이트

- 지혜님이 팀 VM의 Alembic `0004` 적용 증거와 실제 DDL, `oke_rag_index`(색인 DML)·`oke_rag_search`(SELECT) 로그인 경로, pgvector 확장, 데이터 보존/백업 상태를 전달한다. 현재 체크아웃의 `develop/jihye/migrations/`에는 README만 있으므로 SQL 호환성은 미확인이다.
- 오현님이 실제 Markdown 8개 파일의 버전·SHA256과 **문서별** `all`/`it` 권한표를 승인한다. 코스 킷 로컬 사전 조사 결과는 `REAL-DOC-INTEGRATION-READINESS.md`에 있다. VM의 `/data/docs/`는 data-api 컨테이너 내부 경로일 수 있다. Python 프로세스가 읽을 수 있는 실제 경로와 원본 해시를 VM에서 확인해야 한다. `security-incident.md=it` 지정과 기존 Q08 `all` 기대 충돌, `privacy.md` 권한 미확정을 해결하기 전에는 **8개 실제 문서 적재를 중단**한다.
- 지혜님·오현님이 쓰기 대상이 격리 DB인지 확인하고 실제 문서 적재 범위·기존 색인 교체 여부를 승인한다. 아래 합성 시험도 격리된 대상에서만 수행한다.
- VM Python과 PostgreSQL이 동일 네트워크 네임스페이스일 때만 `localhost:5432`를 DB 주소로 사용한다. Python이 Docker 컨테이너 안이면 `localhost`는 그 컨테이너 자신이므로 지혜님에게 실제 서비스명·네트워크를 확인한다.
- 실제 키는 VM의 비밀 주입 경로로 전달받는다. `DATABASE_URL`, `OPENAI_API_KEY`, `SEARCH_TEAM_KEY`의 값을 명령 출력·로그·문서·Git에 남기지 않는다. 색인용과 검색용 `DATABASE_URL`은 별도 프로세스 환경에서 각각 해당 최소 권한 계정으로 설정한다.

## 1–3. VM 접속과 Python 환경

VM 접속 별칭·계정은 오현님이 제공해야 한다. 제공받은 **별칭**으로 `ssh <승인된_VM_접속_별칭>`을 실행한다. 이 명령의 꺾쇠 부분은 아직 값이 없으므로 그대로 실행하지 않는다. 체크아웃을 VM에서 담당 경로로 배치한 뒤 다음을 실행한다.

```bash
cd /opt/oke-rag
uv venv .venv
UV_CACHE_DIR=/tmp/oke-rag-uv-cache uv pip install --python .venv/bin/python -r requirements-runtime.txt
.venv/bin/python -c 'import psycopg; print(psycopg.__version__)'
```

`/opt/oke-rag`은 기존 `oke-index` Mock 래퍼가 가정하는 코드 배치 경로이며, 실제 VM 배치 여부는 오현님 확인이 필요하다. 경로가 다르면 승인된 배치 경로에서 `develop/yubeen`의 내용을 실행한다. 시스템 Python을 변경하지 않는다. `requirements-runtime.txt`는 `psycopg[binary]==3.3.8`을 고정한다. OpenAI 임베딩은 기존 `rag_search.OpenAIEmbeddingProvider`의 표준 라이브러리 HTTP 호출을 사용한다.

비밀 주입 후 값 자체를 출력하지 않고 존재 여부만 확인한다.

```bash
.venv/bin/python -c 'import os; print({k: bool(os.getenv(k)) for k in ("DATABASE_URL", "OPENAI_API_KEY", "SEARCH_TEAM_KEY")})'
```

`DATABASE_URL`은 VM 안에서 색인 프로세스에는 `oke_rag_index`, 검색 프로세스에는 `oke_rag_search` 계정으로 안전하게 주입한다. URL의 host가 `localhost`인지 실제 네트워크 구성을 확인한다. n8n용 `SEARCH_SERVICE_URL`은 `/webhook/oke-search`를 포함한 **n8n에서 접근 가능한** Python 서비스 URL이어야 한다. n8n이 다른 컨테이너이면 `127.0.0.1:8765`를 n8n 접근 주소로 가정하지 않는다. 포트 노출·방화벽·Credential은 오현님/지혜님과 확인한다.

## 4–5. revision·스키마 읽기 전용 확인

지혜님이 제공한 `0004` 적용 명령·로그와 실제 migration head를 먼저 확인한다. VM의 마이그레이션 프로젝트 위치가 확인된 경우에만 지혜님 표준 Alembic 환경에서 `current`를 실행한다. 현재 이 체크아웃에는 실행 가능한 Alembic 프로젝트가 없다. 아래 명령은 **검색 전용 또는 읽기 전용 계정**의 DB URL이 안전하게 주입된 격리 대상에서만 실행한다. 결과에 DB URL을 출력하지 않는다.

```bash
.venv/bin/python - <<'PY'
import os, psycopg
with psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=3,
                     options='-c default_transaction_read_only=on') as db:
    with db.cursor() as cur:
        cur.execute("SELECT extname FROM pg_extension WHERE extname='vector'")
        print('vector_extension', bool(cur.fetchone()))
        cur.execute("SELECT table_schema,table_name,column_name,data_type,udt_name FROM information_schema.columns WHERE table_schema='rag' AND table_name IN ('documents','chunks') ORDER BY table_name,ordinal_position")
        for row in cur.fetchall(): print(row)
        cur.execute("SELECT count(*) FROM rag.documents")
        print('documents_count', cur.fetchone()[0])
        cur.execute("SELECT count(*) FROM rag.chunks")
        print('chunks_count', cur.fetchone()[0])
PY
```

지혜님 실제 DDL에서 `rag.documents`의 id/doc_key/title/access_level/source_url/source_hash/updated_at, `rag.chunks`의 document_id/chunk_no/section/content/content_hash/embedding/embedding_model/metadata, FK·UNIQUE·vector(3072)·JSONB·역할 GRANT를 확인한다. 기존 `PostgresStore`는 autocommit=false 전용 연결과 advisory lock을 요구하고 UPSERT→기존 청크 DELETE→새 청크 INSERT를 한 거래에서 수행한다. `PgvectorSearchAdapter`는 권한·모델 선필터 뒤 cosine `<=>`와 top3 바인딩 쿼리를 사용한다. **실제 DDL/권한/SQL 실행계획 대조 전에는 호환 완료로 판정하지 않는다.**

## 6. 격리 합성 문서 시험

지혜님이 허용한 별도 격리 DB·색인 계정에서만 합성 문서 1건을 생성·재실행하고 검색 계정으로 `all` 조회·`it` 누출 방지·쓰기 거절을 확인한다. 현재 제공된 `rag_verify.py index --source mock`은 DB에 접속하지 않는 합성 저장 더블이다. **실제 합성 INSERT/검색의 VM 검증은 미완료다.** `rag_load.py`는 승인된 정확한 8개 Markdown만 입력받으므로, 합성 1건 격리 시험에는 별도 승인된 시험 절차가 필요하다. 공통 migration은 수정하지 않는다.

DB 없이 현재 실행 가능한 사전 검사는 다음과 같다.

```bash
.venv/bin/python tools/rag_verify.py index --source mock --scenario initial-and-repeat --json
.venv/bin/python -m unittest discover -s tests -q
node tests/search-mock.test.cjs
node tests/search-live-workflow.test.cjs
```

위 결과는 **Fake/Mock**이며 실제 DB 성공으로 보고하지 않는다.

## 7–9. 권한 확정·실제 8개 문서 적재

오현님의 8개 권한표와 VM 원본 경로·해시가 확정될 때까지 중단한다. `tools/rag_load.py`는 정확히 8개 Markdown, 명시적 `all`/`it`, SHA256 일치를 먼저 확인한 뒤 기존 `rag_index.index_snapshot`·`OpenAIEmbeddingProvider`·`PostgresStore`를 연결한다. 권한표 JSON은 저장소에 넣지 않고 오현님 승인본을 VM의 비밀 관리 경로에 둔다. 형식은 `{"approval_status":"approved","documents":{"문서키":{"access_level":"all 또는 it","sha256":"64자 hex"}, ...}}`이며 8개 키 모두 필수다. 프로그램은 승인 주장 자체의 진위를 확인할 수 없으므로 오현님이 승인 출처와 원본 해시를 별도 대조해야 한다.

DB 연결 없이 합성 원본으로 사전 검사:

```bash
.venv/bin/python tools/rag_load.py --docs-dir "$RAG_DOCS_DIR" --permissions "$RAG_PERMISSIONS_FILE" --mode fake
```

실제 적재는 지혜님의 DDL/계정·격리 시험, 오현님의 문서별 권한과 쓰기 범위 승인이 끝난 후 VM에서만 실행한다:

```bash
.venv/bin/python tools/rag_load.py --docs-dir "$RAG_DOCS_DIR" --permissions "$RAG_PERMISSIONS_FILE" --mode real --allow-external
```

명령은 문서별 `indexed`/`skipped`/`rejected`/`failed`와 청크 수만 출력하며, 한 문서가 실패하면 종료 코드 1이다. 이미 성공한 다른 문서는 유지된다. DB 트랜잭션 원자성과 실제 재실행은 VM에서 별도 확인해야 한다. `rag_verify.py index --source api`는 여전히 실제 적재 경로가 아니다. 실제 적재 후 doc_key별 원본/청크 건수·해시·권한·중복과 동일 입력 재실행의 skipped 결과를 기록한다. 코스 킷 기준 기본 절 청킹의 예상 33개는 VM 실적재 건수가 아니다.

## 10–12. 검색 서비스와 n8n

검색 계정 `DATABASE_URL`, `OPENAI_API_KEY`, `SEARCH_TEAM_KEY`가 안전하게 설정되고 실제 DB 조회를 확인한 뒤 Python 프로세스가 n8n에서 접근 가능한 주소로 바인딩되도록 `SEARCH_HOST`를 정한다. 로컬 전용 점검의 기존 실행 명령은 다음과 같다.

```bash
.venv/bin/python tools/search_http.py --host 127.0.0.1 --port 8765
```

이 명령은 VM에서 n8n의 접근성을 보장하지 않는다. 실제 배포 바인딩 주소와 방화벽/컨테이너 네트워크는 오현님이 확인한다. 서비스는 `POST /webhook/oke-search`에 X-Team-Key와 `{request_id,query,type,access_levels:["all"],top_k:3}`를 받고 정상/빈 결과 200, 장애 503을 반환한다. `X-Team-Key`는 서비스 인증이며 직원 IT 권한 증명이 아니다. 승인 C03 계약에 따라 X-Team-Key 인증 후 all/all+it를 신뢰한다. 다른 권한 목록은 400, 키 누락·불일치는 401이며 resolver 부재로 403 처리하지 않는다. 직원 조회 책임은 본체에 있다.

n8n의 비활성 `workflows/oke-search.json`은 `SEARCH_SERVICE_URL`과 Header Auth Credential(X-Team-Key)을 참조한다. URL·Credential을 n8n에서 설정하고 담당자가 import/test하여 일반 검색, 빈 결과, 503, 인증 실패와 일반/IT 문서 분리을 확인한다. n8n 워크플로우를 이 가이드만으로 활성화하거나 VM에 push하지 않는다.

## 실패 점검과 완료 판정

- DB 접속 실패: 실제 네트워크 네임스페이스·host/port, 계정 권한, extension, 접속 제한을 지혜님과 확인한다. 접속 문자열은 출력하지 않는다.
- 임베딩 실패: 키 주입 여부, VM outbound 네트워크/DNS, 모델·3072차원, timeout을 확인한다. 키·요청 헤더·벡터는 로그에 남기지 않는다.
- 색인 실패: 실제 DDL 차이, 원본 해시·권한 충돌, 청크 부분 거절, 트랜잭션 rollback/commit 불명확 상태를 분리한다. 불명확한 commit은 재조회 전 성공으로 처리하지 않는다.
- 검색 503: 임베딩과 DB 장애를 내부에서 분리 관측하되 외부 C03에는 `search_unavailable`만 반환한다. 일반 직원에 IT 문서가 노출되면 즉시 검색을 중단하고 담당자와 확인한다.
- n8n 호출 실패: URL의 실제 도달성, Credential 연결, HTTP 상태·응답 외형, 4초 시간 예산을 검증한다.

완료 판정은 0004/DDL/역할 실제 확인, 승인된 권한표, 격리 합성 INSERT·검색, 실제 8개 문서 적재/중복 없는 재실행, 일반/IT 권한 경계(IT 양성은 인증된 본체의 all+it 사용), Python HTTP 200/빈200/503, n8n C03 실제 호출 증거가 모두 있어야 한다. 현재는 **CLI·HTTP 서비스·워크플로우의 로컬 Fake 검증까지 완료**했으며 `VERIFIED_LOCAL_REAL` 또는 `VERIFIED_VM_REAL`이 아니다.

## n8n 색인 HTTP 연결 (로컬 준비, VM 미검증)

색인 전용 프로세스에는 `RAG_DOCS_DIR`, `RAG_PERMISSIONS_FILE`, 쓰기 계정 `DATABASE_URL`, `OPENAI_API_KEY`, `INDEX_TEAM_KEY`를 안전하게 주입한다. `INDEX_HOST`/`INDEX_PORT` 기본값은 `127.0.0.1:8766`이다. VM에서 n8n이 해당 주소에 도달할 수 있는 네트워크 바인딩을 오현님이 확인한다.

```bash
.venv/bin/python tools/index_http.py --host "$INDEX_HOST" --port "$INDEX_PORT"
```

`oke-index.json`은 비활성 수동 트리거 → `POST $env.INDEX_SERVICE_URL` → 결과 검증의 3노드다. URL은 `/internal/oke-index` 전체 주소이며, HTTP Header Auth Credential 이름은 `X-Team-Key`, 값은 `INDEX_TEAM_KEY`와 일치하도록 n8n UI에서 설정한다. 본문은 전송하지 않으며 서버가 고정한 원본 경로·권한표만 사용한다. 이 엔드포인트는 쓰기를 트리거하므로 오현님이 접근 가능한 서비스만 노출하고 인증·네트워크를 검증한다. 기존 Mock 워크플로우는 `tests/fixtures/oke-index-mock.json`에 보존했다. `oke-search.json`에도 별도의 `SEARCH_SERVICE_URL`과 검색용 Header Auth Credential이 필요하다. 두 워크플로우 모두 사람이 n8n에 import 후 Credential 연결·test하고 실제 결과를 기록하기 전까지 활성화/실연동 완료로 표시하지 않는다.


## 최종 실행 순서 · 승인 후 VM에서만 수행

현재 판정 BLOCKED. 아래는 실행할 명령이며 이번 점검에서 DB·OpenAI·VM 명령을 실행하지 않았다. 1~4단계가 실패하면 적재하지 않는다. 별도 터미널의 색인/검색 프로세스에는 해당 전용 계정 환경을 각각 주입한다. 패키지 설치는 위 uv 절차 또는 `python3 -m venv .venv` 후 `.venv/bin/python -m pip install -r requirements-runtime.txt`를 사용한다.

| 단계 | 명령·작업 | 성공 / 실패 기준 |
| --- | --- | --- |
| 1 VM·경로 | 제공받은 SSH 별칭 접속 후 `cd /home/yubeen/Aio-4pj-1team/develop/yubeen` 및 `git branch --show-current` | 실제 VM 배치 경로와 feat/yubeen-p0 확인. 경로가 다르면 리드가 알려준 경로 사용 |
| 2 Python | `.venv/bin/python --version` 및 `.venv/bin/python -c 'import psycopg; print(psycopg.__version__)'` | import 성공. 미설치 시 위 설치 절차 |
| 3 DB | 위 읽기 전용 카탈로그 명령과 아래 SQL 실행 | localhost:5432, vector 확장·3072형·제약·계정 확인. DDL 차이/접속 실패면 중단 |
| 4 문서 | `.venv/bin/python tools/rag_load.py --docs-dir "$RAG_DOCS_DIR" --permissions "$RAG_PERMISSIONS_FILE" --mode fake` | 승인표/8개 해시 일치, indexed=8·failed/rejected=0·33청크(현재 버전). fake는 DB 쓰기·OpenAI 없음 |
| 5 적재 | 색인 계정 환경에서 `.venv/bin/python tools/rag_load.py --docs-dir "$RAG_DOCS_DIR" --permissions "$RAG_PERMISSIONS_FILE" --mode real --allow-external` | 종료0, indexed+skipped=8, failed/rejected=0. 실패 시 문서별 reason 확인, 부분 성공 보존 |
| 6 건수·재실행 | 아래 집계 SQL 후 5단계 동일 입력 재실행 | 대상 8개·33청크, 중복0, 재실행 skipped=8. 기존 다른 문서는 전체 건수에서 구별 |
| 7 일반 검색 | 검색 계정 환경에서 search_http 실행 후 아래 HTTP 점검 | 200, evidence의 모든 doc이 승인표 all에 속함. it 노출 시 중단 |
| 8 IT 검색 | 같은 질문에 all+it로 아래 HTTP 점검 | 200, 해당 IT 문서의 답이 있는 질문에서 it 근거 포함. 후보 top3 특성상 임의 질문으로 양성 판정 금지 |
| 9 n8n | UI에서 SEARCH_SERVICE_URL·Header Auth Credential 확인 후 oke-search import/test, 아래 HTTP 대상 URL을 n8n 테스트 URL로 변경 | 일반/IT 요청, 빈200/no_evidence, 장애503/search_unavailable, 키401·권한400 확인. 담당자가 실제 실행 증거 기록 |

3·6단계 SQL은 위 psycopg 읽기 전용 연결의 cur.execute로 각각 실행한다. 접속 실패의 원시 예외에는 DSN이 포함될 수 있으므로 캡처·보고서에 복사하지 않는다.

```sql
SELECT format_type(a.atttypid,a.atttypmod)
FROM pg_attribute a
WHERE a.attrelid='rag.chunks'::regclass AND a.attname='embedding';
SELECT conrelid::regclass, pg_get_constraintdef(oid)
FROM pg_constraint WHERE conrelid IN ('rag.documents'::regclass,'rag.chunks'::regclass);
SELECT d.doc_key,d.access_level,count(c.document_id),min(vector_dims(c.embedding)),max(vector_dims(c.embedding))
FROM rag.documents d LEFT JOIN rag.chunks c ON c.document_id=d.id
GROUP BY d.doc_key,d.access_level ORDER BY d.doc_key;
SELECT document_id,chunk_no,count(*) FROM rag.chunks GROUP BY document_id,chunk_no HAVING count(*)>1;
```

7·8단계 HTTP 점검은 승인 후 유료 임베딩을 발생시킨다. 본문을 출력하지 않고 doc 식별자만 비교한다. 질문은 본문을 출력하지 않는 getpass로 입력한다. n8n 테스트 URL은 UI가 제공한 전체 URL을 SEARCH_TEST_URL에 주입하며 테스트 리스너를 먼저 시작한다.

```bash
.venv/bin/python - <<'PYHTTP'
import os,json,getpass
from urllib.request import Request,urlopen
from urllib.error import HTTPError
url=os.environ.get('SEARCH_TEST_URL','http://127.0.0.1:8765/webhook/oke-search')
query=getpass.getpass('승인된 IT 문서 양성 질문: ')
for levels in (['all'],['all','it']):
    body=dict(request_id='vm-rag-check',query=query,type='security',access_levels=levels,top_k=3)
    req=Request(url,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Team-Key':os.environ['SEARCH_TEAM_KEY']})
    try:
        with urlopen(req,timeout=15) as response:
            result=json.load(response)
            print(response.status,levels,result.get('ok'),result.get('reason'),[r['doc'] for r in result.get('evidence',[])])
    except HTTPError as error:
        print('http_status',error.code)
    except Exception:
        print('search_check_failed')
PYHTTP
```

n8n의 HTTP timeout은 4초이고 Python 검색은 임베딩3초+DB 연결3초+SQL3초를 각기 허용한다. 전체4초 이내 성공은 보장되지 않아 VM에서 지연을 측정해야 한다. 시간 예산 변경은 본체/리드와 조율한다. 빈 결과는 실제 후보가 없는 격리 데이터에서, 장애는 승인된 시험 환경에서 확인하며 운영 데이터를 비우지 않는다.
