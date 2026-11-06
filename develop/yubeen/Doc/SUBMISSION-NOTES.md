# RAG 인계·제출 자료 · 2026-11-05

상태: RAG 코드·실행 도구 구현 완료 / 로컬 Fake·프로토콜 검증 완료 / 실제 DB·VM 통합 미검증.
VM 배포·네트워크·실제 통합 시험은 오현님, 마이그레이션·스키마·계정은 지혜님 담당이다.
이번 구현은 담당 폴더만 변경하며 공통 API·DDL·모델·권한·운영 기본청킹을 변경하지 않는다.

## 실행 환경과 외부 준비물

VM의 프로젝트 `develop/yubeen`에서 실행한다. `.venv/bin/python`에 `requirements-runtime.txt` 설치가 필요하다. OpenAI SDK 없이 urllib와 psycopg를 사용한다.

| 프로세스 | 안전하게 주입할 환경변수 |
| --- | --- |
| 색인 CLI | DATABASE_URL(색인 계정), OPENAI_API_KEY, RAG_DOCS_DIR, RAG_PERMISSIONS_FILE |
| 검색 HTTP | DATABASE_URL(SELECT 계정), OPENAI_API_KEY, SEARCH_TEAM_KEY, SEARCH_HOST/SEARCH_PORT |
| 색인 HTTP(선택) | 색인 CLI 환경 + INDEX_TEAM_KEY, INDEX_HOST/INDEX_PORT |
| 측정 CLI | DATABASE_URL(SELECT 계정, 측정 대상과 같은 DB), SEARCH_TEAM_KEY, SEARCH_TEST_URL(전체 C03 URL) |
| n8n | SEARCH_SERVICE_URL, 선택 INDEX_SERVICE_URL, 각각의 Header Auth Credential |

VM에서 Python은 호스트 내부 실행, DB는 localhost:5432이다. DB명·색인/검색 역할·SSL/인증 방식은 지혜님 전달을 따른다. n8n 컨테이너에서 Python으로 접근할 주소·방화벽은 리드가 설정한다. n8n의 localhost를 VM 호스트 주소로 가정하지 않는다. 실제 키·DSN을 출력하거나 Git에 넣지 않는다.

승인된 권한 manifest는 `approval_status=approved`, documents의 정확한 8개 doc_key마다 access_level=all/it와 원본 바이트 sha256이 필요하다. 권한 미확정 항목을 자동 all로 채우지 않는다. Q08/security-incident 권한 충돌과 Q09/privacy, Q14~16의 정답·관리자 원본은 리드가 확인해야 한다. Q01~Q13 초안은 유지했으며 자동 frozen 승격하지 않았다.

## 기본 색인·검색·검증 순서

다음은 **승인 후 팀장이 실행할 명령**이다. 이 문서 작성 시 실제 서비스에 실행하지 않았다. 출력 파일은 담당 폴더 아래 새 경로로 지정하며 덮어쓰지 않는다. 실행마다 식별 가능한 별도 디렉터리를 사용한다.

```bash
mkdir -p runs/vm-check
.venv/bin/python tools/rag_db.py snapshot --allow-db --output runs/vm-check/before-index.json
.venv/bin/python tools/rag_load.py --docs-dir "$RAG_DOCS_DIR" --permissions "$RAG_PERMISSIONS_FILE" --mode fake
.venv/bin/python tools/rag_load.py --docs-dir "$RAG_DOCS_DIR" --permissions "$RAG_PERMISSIONS_FILE" --mode real --allow-external
.venv/bin/python tools/rag_db.py snapshot --allow-db --output runs/vm-check/after-index.json
.venv/bin/python tools/rag_load.py --docs-dir "$RAG_DOCS_DIR" --permissions "$RAG_PERMISSIONS_FILE" --mode real --allow-external
.venv/bin/python tools/rag_db.py snapshot --allow-db --output runs/vm-check/after-repeat.json
.venv/bin/python tools/rag_db.py compare --before runs/vm-check/after-index.json --after runs/vm-check/after-repeat.json --output runs/vm-check/repeat-comparison.json
```

초회 indexed+skipped=8, failed=rejected=0, 현재 원본은33청크가 기준이다. 재실행 skipped=8, 비교 same_inventory=true와 종료0을 확인한다.DB에 기존 다른 문서가 있으면 대상8개와 구별한다. all→it 변경은 공개 청크를 중지하고 rejected로 멈추는 기존 정책이므로 자동 재개하지 않는다. 한 문서 실패 시 다른 성공 문서는 유지되며 실패 문서만 동일 명령으로 재시도한다. 불명확한 commit은 DB를 재조회하기 전 성공/롤백으로 단정하지 않는다.

스냅샷은 일관된 읽기 전용 REPEATABLE READ에서 vector 확장·vector(3072), 실제 모델/차원·content_hash·청크 연속성을 확인하고 본문/벡터 대신 해시를 기록한다. PK·시각은 비교에서 제외하므로 새 DB에서도 비교할 수 있다. FK·UNIQUE·로그인 역할과 실제 GRANT는 기존 VM 가이드의 카탈로그 점검으로 지혜님과 확인한다. 이 도구가 DDL이나 계정을 만들지는 않는다.

검색 프로세스는 별도 SELECT 계정 환경에서 실행한다.

```bash
.venv/bin/python tools/search_http.py --host "$SEARCH_HOST" --port "${SEARCH_PORT:-8765}"
```

인증 후 `["all"]`/`["all","it"]`만 수락한다. 다른 권한/입력은400, 키 누락·불일치는401, 정상/빈 후보는200, 임베딩·DB 장애는503이다. all+it에 독립 resolver를 요구하지 않는다. SQL의 MATERIALIZED 후보에서 documents.access_level을 먼저 제한한다. 질문·role·is_admin으로 권한을 추가하지 않는다.

## P1-3 실제 측정과 비교

정답표는 검색 전에 승인받은 별도 버전 JSON으로 고정한다. 기존 cases/rag-search.json은 draft 상태를 유지한다. 각 frozen 질문에는 source_verified=true, source_hash, 실제 question, access_levels, expected_doc/expected_section/verified_required_quotes가 필요하다. no_answer는 별도 승인 근거와 source_hash가 필요하며 incorrect_auto_answer는 본체 관측 없이 추정하지 않는다. 초안/관리자 미확정 항목은 평가에서 제외되고 수집기는 frozen 항목이 0이면 서비스 호출 없이 실패한다.

같은 격리 DB에서 section 색인→측정→300 색인→측정→section 복원 순으로 진행한다. 운영 DB에서 청킹 실험을 하지 않는다. CASES_FILE은 승인한 정답표의 경로이며 내용을 자동 수정하지 않는다. ENV_LABEL은 비밀정보 없는 동일한 환경 식별자(영문·숫자·_·-)이다.

```bash
.venv/bin/python tools/rag_measure.py collect --cases "$CASES_FILE" --method section --repeats 3 --environment "$ENV_LABEL" --allow-external --output runs/vm-check/section.json
.venv/bin/python tools/rag_load.py --docs-dir "$RAG_DOCS_DIR" --permissions "$RAG_PERMISSIONS_FILE" --mode real --allow-external --comparison-chunking 300
.venv/bin/python tools/rag_measure.py collect --cases "$CASES_FILE" --method 300 --repeats 3 --environment "$ENV_LABEL" --allow-external --output runs/vm-check/chars.json
.venv/bin/python tools/rag_load.py --docs-dir "$RAG_DOCS_DIR" --permissions "$RAG_PERMISSIONS_FILE" --mode real --allow-external
.venv/bin/python tools/rag_measure.py merge --section runs/vm-check/section.json --chars runs/vm-check/chars.json --output runs/vm-check/results.json
.venv/bin/python tools/rag_measure.py report --cases "$CASES_FILE" --results runs/vm-check/results.json --repeats 3 --output runs/vm-check/evaluation.json
.venv/bin/python tools/rag_verify.py evaluate --cases "$CASES_FILE" --results runs/vm-check/results.json --repeats 3 --output Doc/SEARCH-EVAL.md
```

collector는 실제 DB 원본 해시/권한/청킹과 HTTP 응답을 대조하고, 측정 전후 DB 상태가 바뀌면 결과 저장을 거절한다. section sidecar는 허용된 DB 후보의 content_hash/metadata와 응답을 대조하여 300자 청크의 복수 절을 판정한다. HTTP 대상이 해당 DATABASE_URL을 사용하는 동일 서비스인지 리드가 확인한다. 타임아웃·인증 실패·잘못된 응답은 성공으로 집계하지 않는다. HTTP503은 실패 관측으로 분모에 포함된다. 각 질문의 전체 HTTP 왕복시간을 perf_counter로 측정하며 임베딩/DB 개별시간·토큰·비용은 관측하지 않았으면 null이다.

mode=real은 실제 관측 자료를 입력했다는 분류이며 모델이 실행 증거의 진위를 보증한다는 뜻이 아니다. source_ref는 입력 요청/응답 해시이며 VM 실행 로그와 함께 보관한다. Fake 모드도 그대로 지원한다. 지표는 Hit@3, Recall@3(질문당 관련 문서1개인 현 정답표에서 Hit와 동일), MRR, 절 적중, 필수 근거 포함률, 권한 누출, 빈/장애 수, 시간 N·median·p95·max다. 승인 없이 K나 top_k=3 계약을 바꾸지 않는다.

원시 results/section/chars에는 평가에 필요한 근거 본문·제한 절 metadata가 들어 있으므로 파일은0600으로 생성한다. 공유 보고서는 본문을 제외하고 제한 절을 가린다. runs/는 Git에 넣지 않는다.

## P1-4 실제 복구 검증

위 rag_db snapshot을 재시작 직전에 before-restart.json으로 저장한다. 오현님이 n8n만 재시작한 뒤 같은 DB를 재색인 없이 after-n8n.json으로 캡처하고 compare한다. 이어 지혜님/오현님이 같은 named volume의 PostgreSQL을 재시작한 뒤 after-postgres.json으로 캡처·compare한다. 결과 same_inventory=true와 고정 질문의 일반/IT 검색 결과를 함께 확인한다.

새 DB 복구는 지혜님이 마이그레이션·계정을 준비한 뒤 기존 원본·승인표로 rag_load real을 실행하고 새 DB snapshot과 기존 baseline을 compare한다. PK가 달라도 비교한다. 재생성 임베딩 벡터가 달라졌으면 changed로 보고하며 해시/권한/청크 차이와 검색 품질을 따로 검토한다. 백업 복원은 지혜님이 별도 환경에서 수행한 후 같은 비교 경로를 사용한다. snapshot/compare 자체는 실제 재시작을 관측하지 않으므로 actual_restart_observed=false를 유지하며 리드가 실행 시각·환경/볼륨 식별·재시작 로그를 별도로 연결한다. 복구시간·실제 비용도 실행 기록으로 추가한다.

격리 데이터의 변경·청크 증가/감소·임베딩 실패·DB INSERT 중간 실패·재시도는 로컬 회귀 및 아래 opt-in DB 테스트로 검사한다. 운영 문서를 바꾸거나 팀 DB에서 장애를 주입하지 않는다.

## P1-5 C03·본체 관측 자료

본체는 POST /webhook/oke-search에 X-Team-Key와 다음을 보낸다. 키는 예시에 넣지 않는다.

```json
{"request_id":"integration-001","query":"VPN 연결 오류","type":"network","access_levels":["all"],"top_k":3}
```

정상 예시는 cases/rag-integration-example.json의 **합성 자료**를 따른다. IT 요청은 access_levels를 all+it로, 직원 조회 결과에 맞춰 본체가 생성한다. C03는 evidence를 반환하고 route/sources를 추가하지 않는다. 본체가 evidence의 doc/section/score를 최종 sources로 투영한다.

| C03 상황 | 응답 | 본체에서 확인할 사항 |
| --- | --- | --- |
| 정상 | 200, ok=true/evidence/reason=null | sources는 전달한 허용 evidence의 부분집합, 자동 답변은 근거 필수 |
| 빈 결과 | 200, ok=true/evidence=[]/reason=no_evidence | 담당자 이관·sources=[] |
| 장애 | 503, ok=false/evidence=[]/reason=search_unavailable | 담당자 이관·sources=[] |
| 인증 실패 | 401, ok=false/evidence=[]/reason=unauthorized | LLM에 검색 근거 전달 금지, 호출 설정 확인 |
| 권한/입력 형식 오류 | 400, ok=false/evidence=[]/reason=invalid_request | 검색 실행 금지, 본체 입력 생성 확인 |

본체의 실제 route는 본체 담당이 유지한다. 권한 없는 문서 질문은 권한 없음 또는 담당자 이관이며 RAG가 route를 임의 생성하지 않는다. 최종 응답과 writer/verifier의 **실제 입력 evidence 리스트**를 안전한 관측 파일로 전달받아 검사한다. 전체 프롬프트의 비밀값·개인정보를 수집하지 않는다. llm_evidence를 관측하지 않았으면 필드를 생략하며 검사 결과도 미관측으로 표시한다.

```bash
.venv/bin/python tools/rag_contract.py --record cases/rag-integration-example.json --output runs/vm-check/synthetic-contract.json
.venv/bin/python tools/rag_contract.py --record "$INTEGRATION_RECORD" --permissions "$DOC_ACCESS_MAP" --output runs/vm-check/actual-contract.json
```

INTEGRATION_RECORD의 형식은 예시의 record 객체다. DOC_ACCESS_MAP은 승인한 doc_key→all/it JSON이다. llm_evidence는 C03 evidence에 없는 항목·다른 본문·권한 없는 항목이면 거절한다. sources도 C03에 없는 근거면 거절한다. 검사기는 본체의 프롬프트 조립을 변경하거나 실시간 차단하지 않는다. RAG는 SQL 선필터로 안전한 근거만 반환하고, 그 이후 본체가 추가한 데이터는 본체 담당과 관측·검증한다.

n8n 두 워크플로우는 비활성을 유지한다. 오현님이 import→Credential 연결→테스트 URL/네트워크 확인→일반/IT·빈·오류 시험 후 활성화한다. 검색 HTTP timeout4초 내 성공 여부는 실제 지연을 측정해야 한다. 색인 timeout180초 초과 시 HTTP 응답 실패와 실제 DB 작업 진행 여부를 재조회하며 중복 실행하지 않는다.

## 로컬 시험과 제출 경계

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -q
node --test tests/*.test.cjs
```

독립 DB 자동 시험은 RAG_DISPOSABLE_TEST_DSN이 없으면 skip한다. 이 변수는 localhost/127.0.0.1/::1의 **비어 있는 codex_rag_test_ 접두어 DB**만 허용한다. 기존 rag 스키마가 있으면 거절한다. tests/test_postgres_optin.py의 DDL은 그 격리 DB 전용 계약 fixture이며 팀 마이그레이션이 아니다. 실제 OpenAI 대신 결정적 합성 벡터를 사용해 실제 INSERT·SQL 권한 선필터·재실행·변경·rollback을 시험한다. DB 생성/삭제는 실행자가 관리한다. 팀 DB DSN이나 일반 DATABASE_URL은 이 테스트에 사용하지 않는다.

지혜님 DDL/계정 적용 후 순서는 카탈로그/권한→원본/승인표→Fake 입력 점검→실제 색인→재실행→일반/IT 검색→품질 비교→복구 전후→본체/n8n 통합이다. RAG 설계서에 전달할 출처는 REAL-DOC-INTEGRATION-READINESS(원본), CHUNK-COMPARISON/P1-3-READINESS(구조), INDEX-RESULT(로컬), 실제 evaluation 보고서(품질·시간), rag_db 전후 기록(복구), rag_contract 관측 보고서(본체)다.

정답표·권한 승인은 외부 결정 대기이며 RAG 코드 누락으로 처리하지 않는다. 실제 측정값·비용·VM 성공 증거는 아직 없다. 리드가 실제 환경에서 발견한 SQL/네트워크/응답 차이는 담당 범위에서 후속 수정한다.


## P1-1~5 구현 완료 인계 · 2026-11-05

RAG 담당 코드·평가/복구 도구·워크플로우 검사·통합 제출 준비 구현을 완료했다. 실제 VM 통합 완료와 구별한다. 세부 실행 명령과 계약/합성 샘플은 SUBMISSION-NOTES.md를 따른다.

- Python 전체217건: 216통과, 독립 DB 설정이 없는 기본 실행에서 opt-in1건 skip. JavaScript 테스트 파일3개 통과. JSON/그래프·인증·권한·멱등·rollback·실제 결과 import·실제 보고서 CLI 회귀 포함.
- 별도 독립 로컬 PostgreSQL17/pgvector0.8.7에서 opt-in1건 실제 실행 통과: 합성 문서2개·합성3072벡터로 INSERT, 동일 입력 skip, 변경 문서만 갱신, 임베딩 실패 보존, 실제 DELETE 후 INSERT 실패 rollback·재시도, all/all+it SQL 검색을 확인했다. 팀원 DB/VM에 접속하지 않았다. 실제 Markdown8개/OpenAI 임베딩 적재 성공으로 해석하지 않는다.
- rag_db snapshot CLI도 위 로컬 DB에서 읽기 전용 실행 통과했다. 이후 pg_ctl restart 시도가 컨테이너의 주 PostgreSQL 프로세스를 종료하여 --rm/tmpfs 임시 환경이 제거됐다(exit137). 재시작 후 데이터 유지 시험은 통과하지 않았으며 전후 비교 증거가 없다. 이 임시 컨테이너는 남아 있지 않다. VM의 named volume 유지 검증은 팀장 수행 대상이다.
- flow.py check: oke-index/oke-search 각각 오류0·경고1(수동 트리거에 Webhook 없음 / IF typeVersion2). 정적 검사이며 n8n push/test는 미실행이다. git diff --check 통과.
- 외부 의존성: 지혜님 마이그레이션/최소권한 계정·실제 GRANT, 리드 문서별 권한표·원본 버전 및 정답표 승인, VM 환경/네트워크/Credential·실제 비용 승인, 본체의 실제 writer/verifier 근거 관측이다.
- RAG 범위에서 계획한 남은 코드 구현은 없다. 외부 승인·실제 환경 시험 후 발견되는 차이는 후속 보완 대상이다. 코드 READY, 실제 문서 적재/VM 검증 BLOCKED_EXTERNAL. 커밋·푸시는 하지 않았다.
