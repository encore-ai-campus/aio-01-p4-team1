# RAG 구현·검증 통합 기록 · P1-1 Index / P1-2 Search STEP 1·2

기준: `feat/yubeen-p0`의 담당 파일과 기존 결과 문서, 2026-11-05 대화에서 사용자가 전달한 로컬 n8n 확인 결과. 이 문서를 작성하며 새 테스트·HTTP 호출·DB 조회는 하지 않았다. 기존 실행 기록과 사용자 보고를 구분하며 키 값과 Credential 내용은 기록하지 않는다.

## 상태 요약

| 범위 | 구현 | 확인된 검증 | 실제 연동 |
| --- | --- | --- | --- |
| P1-1 Index | 합성 원본·임베딩·저장 더블을 쓰는 Python 색인 엔진과 비활성 n8n Mock 래퍼 | Python Mock·DB-API 더블 검증, 격리 n8n CLI의 3노드 Mock 실행 | 실제 원본 API·OpenAI 임베딩·PostgreSQL 저장 미완료 |
| P1-2 STEP 1 | POST Webhook → Code 요청 구조 확인 → Respond 진단 응답 | 로컬 정적 검사; 사용자가 실제 n8n에서 HTTP 200과 3노드 실행을 확인했다고 보고 | 검색·임베딩·DB 연결 없음 |
| P1-2 STEP 2 | 같은 Webhook의 Header Auth 설정, 기존 진단 경로 유지 | 로컬 정적 검사; 사용자가 로컬에서 올바른 키 200, 잘못된 키 403, 키 누락 403을 확인했다고 보고 | C03 검색 결과·실제 권한 검증 없음 |

## A. P1-1 Index

`workflows/oke-index.json`은 비활성 Manual Trigger → 고정 Execute Command의 `rag_verify.py index --source mock` → 안전한 결과 Code의 3노드·2연결이다. `rag_index.py`는 원본 식별자·확인된 권한 → 기존 P0-2 청킹 → 모든 청크의 모델·3072차원·유한 비영벡터 검사 → 문서별 변경 감지·저장 어댑터의 흐름을 준비했다. 완전한 청크만 저장 후보로 보고 partial/rejected를 전체 성공으로 세지 않는다. PostgreSQL 어댑터는 한 전용 연결의 문서 UPSERT·청크 교체·commit/rollback과 바인딩을 구현했으나 실제 DB 연결 생성이나 마이그레이션은 수행하지 않는다.

`INDEX-RESULT.md`의 최종 Mock 기록: Python 전체 **108개 통과**(해당 기록의 실행 결과), 첫 색인 indexed 4 / rejected 1 / failed 0, 같은 입력 재실행 skipped 4 / rejected 1 / failed 0, Mock 저장 문서 4개다. 내용 해시·모델/차원·FK/고유키 대응, 임베딩/저장 실패의 이전 성공본 보존과 재시도, 권한 축소 시 공개 청크 중지, 충돌·미확인 권한 거절, 동시성 및 rollback/commit 불명확 경계를 Mock·DB-API 더블로 확인했다. 이 숫자는 제공 규정의 실제 색인 건수가 아니다.

기존 기록에는 실제 n8n 컨테이너의 Python Mock 명령 성공과 **격리 n8n 2.42.6 CLI**에서 세 노드 실행 성공이 있다. 기존 external Runner를 사용하는 브라우저 수동 실행은 그 기록에서 미확인이다. 사용자가 이후 `oke-index` Mock 실행 성공을 전달했으나, 이 통합 문서에는 별도 실행 ID·화면 결과가 제공되지 않았다. 실제 data-api 원본·권한, OpenAI 임베딩, PostgreSQL/pgvector 저장·잠금·재시작 유지, 관리자 문서 양성 시험과 실제 색인 성공 ID는 미확인이다.

## B. P1-2 Search STEP 1

`workflows/oke-search.json`의 POST `oke-search` Webhook은 JSON을 받는다. Code 노드는 `body`가 객체인지 `body_is_object`로 나타내고 `request_id`, `query`, `type`, `access_levels`, `top_k`만 `received`에 담는다. Respond to Webhook은 HTTP 200의 `step=P1-2 STEP 1`, `mock=true`, `diagnostic_only=true` 진단 JSON을 반환하도록 구성되어 있다. 이는 C03의 `ok/evidence/reason` 검색 응답이 아니다.

`SEARCH-STEP1-RESULT.md`에는 당시 JSON·연결 검사와 예시 입력의 Code 로컬 실행만 기록되어 있다. 이후 사용자는 실제 로컬 n8n에서 HTTP 200과 Webhook → Code → Respond 세 노드의 정상 실행을 확인했다고 전달했다. 이 대화에 실제 HTTP 200 응답 본문 전문이나 실행 ID는 제공되지 않았으므로 **응답 본문의 최종 일치 여부는 미확인**으로 둔다.

## C. P1-2 Search STEP 2

같은 Webhook에 n8n `headerAuth`를 설정했다. Credential의 헤더 이름은 `X-Team-Key`이며 실제 값은 워크플로우 JSON·문서에 넣지 않는다. 인증 성공 시 기존 Code·진단 Respond로 이어지고, 실패는 Webhook 단계에서 후속 처리를 차단한다. `SEARCH-STEP2-RESULT.md`는 구현 당시 정적 확인과 n8n의 예상 403 동작을 기록했으며 실제 요청 결과는 기록 전 상태였다.

이후 **사용자가 직접 수행한 로컬 테스트 결과**로 올바른 키 HTTP 200, 잘못된 키 HTTP 403, 키 누락 HTTP 403 및 세 노드 실행 성공을 전달했다. Code 출력의 `body_is_object=true`, `request_id=req-001`, `query=VPN 연결 오류`, `top_k=3`도 사용자 확인 결과로 기록한다. 원본 캡처·실행 ID·HTTP 200 응답 본문 전문은 이 대화에 제공되지 않아 독립 재현 또는 본문 최종 검증으로 표시하지 않는다. 인증 실패의 상세 JSON은 H-Y01 제안 상태이며 n8n 기본 응답을 C03 확정 형식으로 취급하지 않는다.

## D. 연결·다음 단계와 설계서 근거

Index가 준비한 `content`, `content_hash`, 문서 권한과 모델·차원은 향후 Search의 실제 후보 데이터가 된다. 현재 Index의 MockStore와 Search의 진단 Webhook 사이에는 **실제 검색 연결이 없다**. STEP 3에서는 필드 자료형·빈 query·고정 `top_k=3`과 `[all]`/`[all,it]` 권한 목록을 인증 후 검증하고 잘못된 입력이 후속 검색으로 가지 않음을 확인해야 한다. 본체가 만든 권한을 search가 독립적으로 직원 인증했다고 해석하지 않는다. H-Y01의 상세 입력/인증 오류 형식은 미확정이다.

그 뒤 남은 작업은 실제 질의 임베딩, 지혜님 마이그레이션·접속 권한 확인, `rag.documents.access_level` SQL 후보 선필터, 같은 모델의 pgvector cosine 정확거리·동점 정렬·top3, `score=1-distance`와 C03 정상/빈/503 evidence 응답, 다혁님 본체의 LLM 입력 권한 관측이다. 실제 관리자 문서와 제공 규정 원본, 권한 축소·중지/재개·복구 운영도 확인이 필요하다.

최종 `docs/RAG-ARCHITECTURE.md`에는 이 문서와 `INDEX-RESULT.md`의 Mock 처리·실패/재실행 근거, `SEARCH-STEP1-RESULT.md`·`SEARCH-STEP2-RESULT.md`의 노드·사용자 HTTP 확인, `SEARCH-EVAL.md`의 평가 양식을 연결할 수 있다. 실제 문서 수·길이 분포, 두 청킹 방식의 hit@3, 점수 임계값, 실제 임베딩 토큰·비용, SQL 실행계획·검색 시간, DB 재시작/복구·재색인 시간은 아직 측정 근거가 없으므로 채우지 않는다.

## 원본 증거

- `Doc/INDEX-RESULT.md`: P1-1 Mock JSON·108개 테스트 실행 기록·격리 n8n 실행과 한계.
- `Doc/SEARCH-STEP1-RESULT.md`, `Doc/SEARCH-STEP2-RESULT.md`: 구현 당시 정적 검사·미실행 경계. 이후 로컬 HTTP 결과는 위 사용자 보고로 별도 표시.
- `Doc/SEARCH-EVAL.md`: P0-2 합성 검색 사례와 미측정 평가 양식. 실제 검색 결과가 아님.
- `workflows/oke-index.json`, `workflows/oke-search.json`: 현재 노드와 비활성 설정.

## P1-2 STEP 3 · 입력·권한 형식 진단 · 2026-11-05

기존 비활성 Webhook(`POST oke-search`, `headerAuth`) → Code → Respond의 3노드·2연결을 유지했다. Code는 `request_id` 문자열 1~64자, `query` 비공백 문자열, `type` 비공백 문자열, `access_levels`의 정확한 `["all"]` 또는 `["all","it"]` 배열, `top_k`의 숫자 3을 검사한다. 중복·역순·`it` 단독은 거절한다. request_id 길이는 공통 요청 식별자 경계를 따르며, Search의 query 최대 길이·type enum·top_k 누락 기본값은 H-Y01 제안 상태여서 추가하지 않았다. 현재 다섯 필드를 필수로 검사하는 것은 이 STEP의 테스트 입력 규약이며 C03의 세부 필수/선택 표가 확정됐다는 뜻은 아니다.

형식이 맞으면 STEP 3 `mock=true`, `diagnostic_only=true`, `valid=true`와 기존 5개 `received` 필드를 HTTP 200 진단 응답으로 돌려준다. 틀리면 `valid=false`, `invalid_fields`만 돌려주고 `received=null`인 임시 HTTP 400 진단 응답이다. 이 JSON은 C03 최종 오류 계약이 아니다. Header Auth의 키 누락·불일치 403 경로는 Webhook에 그대로 있다. 오류 상세 형식과 H-Y01의 401 제안은 채택하지 않았다.

`["all","it"]`의 **형식 통과는 IT팀 신원 확인이 아니다**. Header Auth는 호출자를 확인할 뿐 직원을 확인하지 않는다. 그래서 현재 Code는 IT 형식 요청도 `access_authorization=it_unverified`, `it_access_granted=false`, `search_eligible=false`로 표시한다. `["all"]`만 형식상 `search_eligible=true`이나 이 단계에서 어느 요청도 검색하지 않는다(`search_executed=false`). 질문 본문의 관리자 주장은 읽어 권한을 높이지 않는다. 실제 SQL의 `documents.access_level` 선필터·정렬 전 적용은 STEP 4 의존성으로 남긴다.

로컬 Code 격리 Mock 10사례(정상 all, IT 형식, 필수 누락, 공백 query, 잘못된 타입, top_k 오류, 잘못된/중복 권한, 관리자 사칭, 권한 출처 미확인)가 통과했다. 이는 n8n HTTP 실행이 아니다. 기존 STEP 1·2의 사용자 실행 기록은 위 절의 당시 결과이며 **수정된 STEP 3 JSON의 Import·Credential 재연결·HTTP 200/400/403은 아직 미실행**이다. 실제 DB·임베딩·권한 자료·관리자 문서도 호출하지 않았다.

STEP 4 전에는 다혁님과 오현님이 본체의 검증된 부서/권한을 search가 어떤 신뢰 가능한 경로로 받는지 확인해야 한다. 지혜님과 실제 DB 스키마·연결/최소 권한, 원민님과 일반/IT 음성·양성 시험 자료를 확인해야 한다. H-Y01의 Search 필수/선택·길이·오류 응답은 미확정으로 유지한다. 이 단계의 IT 형식 진단을 IT 문서 검색 허용 근거로 사용하지 않는다.

### 이후 사용자 로컬 n8n HTTP 확인 결과

아래 5건은 **사용자가 AIO WSL의 로컬 n8n에서 직접 실행해 전달한 결과**다. 위의 STEP 3 구현 당시 정적·Mock 검증과 구분한다. 실행 ID·실행 날짜·시간 측정값은 제공되지 않았다.

| 테스트 | 입력 조건 | 사용자가 확인한 실제 결과 | 확인 범위 |
| --- | --- | --- | --- |
| TEST 1 | 정상 `["all"]`, `top_k=3` | HTTP 200, Code `valid=true`, Webhook → Code → Respond 3노드 실행 성공 | HTTP 응답 본문 전문은 미확인 |
| TEST 2 | `top_k=5` | HTTP 400, `valid=false`, `invalid_fields=["top_k"]`, `search_executed=false` | HTTP 응답 본문 확인 |
| TEST 3 | `["all","it"]`, `top_k=3` | HTTP 200, `valid=true`, `access_authorization="it_unverified"`, `it_access_granted=false`, `search_eligible=false` | HTTP 응답 본문 확인. IT 신원 확인이나 접근 허용 아님 |
| TEST 4 | 잘못된 인증 키 | HTTP 403, Webhook 인증 단계에서 차단 | n8n 화면에서 Code·Respond 미실행 확인 |
| TEST 5 | 인증 키 누락 | HTTP 403, Webhook 인증 단계에서 차단 | Code·Respond 미실행 여부의 별도 화면 증거 없음 |

현재 완료된 범위는 Webhook 수신, `X-Team-Key` Header Auth, 다섯 필드의 기본 형식 검사, 임시 HTTP 400 진단 처리, IT 권한 미확인 시 관리자 접근 불허다. 기존 기록의 Python 회귀 108개 통과와 Code 격리 Mock 10/10 통과에 위 **사용자 수행 핵심 HTTP 5건**을 추가한다. 이번 문서 반영 중 이 테스트를 재실행하지 않았다.

실제 직원 신원·IT 권한 검증, query 임베딩, PostgreSQL/pgvector 검색, SQL 권한 사전 필터링, C03 evidence·빈 결과·503 장애 응답, 본체 통합과 검색 품질 측정은 미완료다. TEST 2의 HTTP 400은 STEP 3 임시 진단 응답이며 C03 입력 오류의 최종 형식 확정이 아니다. 실제 검색·임베딩·PostgreSQL 조회는 위 5건에서 실행되지 않았다. P1-1 Index의 Mock 결과와 한계는 앞 절의 기록을 유지한다.

## P1-2 STEP 4 · 합성 fixture 검색

`oke-search.json`에 기본 Code 노드를 하나 추가해 Webhook/Header Auth → STEP 3 검증 → 일반 문서 Mock 검색 → Respond의 4노드·3연결로 구성했다. 기존 `cases/chunk-comparison-mock.json`의 확인된 all/it 합성 문서를 재사용한 스냅샷을 Code에 포함했다. 각 항목에 doc, chunk_id/chunk_no, title, section, text, source, access_level을 보존하며 원본 전체를 한 Mock 청크로 취급한다. P0-2의 실제 청킹 결과나 성공 DB 색인이 아니다. fixture를 변경하면 이 스냅샷도 검토해야 한다.

검증, 권한 확인, query 표현 변환, 후보 선필터, 순위/top3, C03 응답 변환, 예외 응답을 함수로 분리했다. Mock query 표현은 공백 단어 집합이며 점수는 어휘 포함 비율이다. 임베딩·cosine·실제 유사도 점수로 해석하지 않는다. 후보의 access_level=all을 먼저 제한하고 점수 내림차순, doc/chunk_no 동점 순으로 최대 3개를 선정한다. 메타데이터는 내부 Code 출력에 보존하고 HTTP evidence에는 doc/section/text/score만 투영한다. 정상·빈 결과는 C03 HTTP200, 장애는 HTTP503/search_unavailable이다. 합성 장애 query `__mock_search_unavailable__`는 이 Mock 전용이다.

STEP 3 불량 입력은 기존 임시 400 진단, IT 권한 출처 미확인 요청은 기존 200/it_unverified 진단과 검색 차단을 유지한다. 클라이언트 필드나 질문의 관리자 주장으로 IT 권한을 부여하지 않는다. Header Auth와 비활성 설정을 유지한다. SQL은 구현·실행하지 않았다. 실제 교체 시에는 공통 모델 text-embedding-3-large/3072차원과 documents 권한 WHERE → 동일 모델 cosine 정확거리 → doc_key/chunk_no → LIMIT 3을 지켜야 하며 DB 계정·접속 설정은 만들지 않았다.

검증: `node tests/search-mock.test.cjs` 13개 통과/0실패. 워크플로우의 실제 Code 문자열을 격리 실행해 정상·최대3·0개·IT 메타데이터 비노출·IT 주장 차단·입력 오류·장애·결정성·관리자 사칭·연결/Auth를 확인했다. 기존 Python unittest 108개 통과/0실패. JSON 파싱·연결 및 git diff --check 통과. 실제 n8n Import/HTTP 및 Credential 설정 회귀는 미실행이다. 실제 API·임베딩·PostgreSQL 조회도 미실행이며 이전 HTTP 결과를 이번 버전의 실행 근거로 사용하지 않는다.

사용자 검증 시 기존 비활성 워크플로우에 수정본을 반영하고 Credential 연결을 확인한 뒤 Test URL에 query=합성(정상), zzzz-not-present(빈 결과), __mock_search_unavailable__(503)을 전송한다. IT 요청은 기존 차단 진단을 확인한다. HTTP 성공 본문은 C03 형식이라 mock 필드가 없으며 워크플로우 이름·노드 notes와 이 기록으로 Mock임을 식별한다. 운영 활성화 전에 이 합성 경로를 실제 어댑터로 교체해야 한다.

STEP 5/실제 통합 전 질문: 지혜님에게 rag 테이블·확장·최소 권한·접속/마이그레이션 준비, 다혁님·오현님에게 검증된 직원 권한 전달의 신뢰 경계 및 H-Y01 오류 계약, 원민님에게 실제 관리자 원문·일반/IT 양성/음성 평가 자료를 확인한다. 실제 벡터/SQL 실행계획·성능·hit@3·비용·본체 LLM 입력은 미검증이다. Mock 구현 완료가 실제 RAG 검색 완료를 뜻하지 않는다.

### STEP 4 이후 사용자 로컬 HTTP 검증

사용자가 AIO WSL 로컬 n8n에서 직접 수행해 전달한 결과다. Codex가 재실행한 HTTP 시험이 아니다. 실행 일시·실행 ID·성능 수치는 제공되지 않았다. 아래 TEST 2~4의 전달된 입력 요약에는 type이 명시되지 않아 값을 추정하지 않는다.

| 시험 | 요청 요약 | 실제 결과 및 확인 범위 | 판정 |
| --- | --- | --- | --- |
| TEST 1 | req-step4-001, query=합성, type=network, all, top_k=3 | HTTP200, ok=true, evidence 3개(mock-plain, mock-structure, mock-unicode), reason=null. score는 Mock 어휘 일치율이며 cosine 아님 | PASS |
| TEST 2 | req-step4-002, query=zzzz-not-present, all, top_k=3 | HTTP200 확인. n8n 노드 출력에서 ok=true, evidence=[], reason=no_evidence 확인. 터미널 HTTP 본문 전문은 미확인 | PASS |
| TEST 3 | req-step4-003, query=__mock_search_unavailable__, all, top_k=3 | HTTP503 확인. n8n 노드에서 ok=false, evidence=[], reason=search_unavailable, mock=true 확인. HTTP 본문도 별도 출력 확인. 실제 DB 장애가 아닌 합성 장애 | PASS |
| TEST 4 | req-step4-004, query=합성, all+it, top_k=3 | HTTP200 STEP 3 진단: valid=true, access_authorization=it_unverified, it_access_granted=false, search_eligible=false, search_executed=false. IT 문서 검색 미실행 | PASS |

TEST 3의 mock=true는 내부 노드 출력 필드다. HTTP 응답은 C03의 ok/evidence/reason 투영이며 내부 출력 전체와 구분한다. TEST 4의 HTTP200은 임시 권한 진단으로 최종 권한 오류 계약의 확정을 뜻하지 않는다.

완료 범위: Header Auth와 STEP 3 입력 검증 유지, 결정적 Mock 어휘 검색, 일반 문서 후보 선필터, 최대3개 제한, C03 정상/빈/장애 응답, 미검증 IT 요청 차단, JavaScript 13개·Python 108개 로컬 테스트 및 위 사용자 HTTP 핵심 4건 확인. 앞 절의 HTTP 미실행 문장은 구현 당시 상태로 보존한다.

미완료 범위: 실제 임베딩 API, PostgreSQL/pgvector 저장·검색, cosine 계산, 검증된 IT 직원의 관리자 문서 검색, 본체 C03 HTTP 통합, 실제 검색 품질 평가, 최종 권한 오류 계약 확정.

### 지혜님에게 전달받은 DB 준비 상태

사용자가 전달한 지혜님 확인 내용: PostgreSQL 접속 확인, pgvector 0.8.6 사용 가능 확인. pgvector 확장 활성화, rag.documents/rag.chunks 생성, 색인·검색 DB 권한은 미완료다. P0-5 완료 후 실제 DB 연동이 가능하며 data-api 응답·인증 방식은 미확정이다. 이는 팀원에게 전달받은 상태이며 Codex가 DB 접속으로 독립 확인한 결과가 아니다.

## P1-2 STEP 5 · 외부 연결 없는 검색 어댑터 준비

추가 파일: tools/rag_search.py, tests/test_search_adapters.py. 기존 n8n 워크플로우와 STEP 4 Mock 코드는 수정하지 않았다. 실제 제공자/DB 연결 생성·SDK·드라이버·키·새 환경변수는 추가하지 않았다.

Index의 load_settings/validate_embedding과 (text,model,dimensions) → {model,embedding} 제공자 규약을 재사용한다. 모델 text-embedding-3-large, 3072차원, 숫자·유한값·비영벡터·모델 일치를 검증한다. 호출자는 Webhook 인증과 STEP 3 입력 검사를 수행해야 하며 이 Python 경계는 직원 권한을 추론하지 않는다. 현재 ['all']만 지원하고 IT 목록은 제공자/DB 호출 전에 실패시킨다. 내부 어댑터의 503은 연결 경계 실패이며 H-Y01의 최종 입력/권한 오류 응답을 확정하지 않는다.

PgvectorSearchAdapter는 호출자가 소유한 전용 DB-API 연결을 받으며 직접 접속하지 않는다. 공통 rag.documents/chunks 컬럼으로 작성한 SQL 초안은 MATERIALIZED 허용 후보에서 documents.access_level과 embedding_model을 WHERE로 먼저 제한한다. <=> 거리 ASC, doc_key/chunk_no ASC, LIMIT 3 및 score=1-distance를 사용한다. 권한·모델·질의 벡터·개수는 execute의 바인딩 매개변수로 전달한다. type은 SQL 필터에 사용하지 않는다. cursor는 정리하지만 연결의 commit/rollback/close, statement timeout과 전체 deadline은 호출자 책임이며 실제 통합 전 구현·검증해야 한다. P0-5 스키마·pgvector 확장·최소 권한과 실행계획 검증 전에는 실제 실행 완료 SQL로 간주하지 않는다.

실행 선택 dispatch의 mode는 서버 소유 설정이다. mock은 명시적으로 선택하고 제공한 Mock 함수만 호출한다. adapter는 adapter_enabled=True와 두 제공자를 모두 명시해야 하며 기본 비활성이다. 모드 누락·미준비·제공자/DB 실패는 503/search_unavailable이고 Mock 자동 대체는 없다. 현재 n8n은 기존 STEP 4 Mock만 사용하며 Python 어댑터와 연결하지 않았다. 향후 n8n 호출 경로와 안전한 Credential·연결 주입 방식은 실제 통합 시 준비한다.

로컬 검증: Python unittest 122개 통과(기존108+신규14), 실패0. 신규 시험은 Fake 제공자·DB만 사용해 모델/3072차원, 잘못된 차원·NaN/Infinity/bool·0벡터·모델 혼입·제공자 장애, SQL 필터/바인딩/LIMIT/동점 정렬, evidence/빈 결과, DB 장애/cursor 정리, IT 차단, top_k, 미설정 모드와 Mock 자동 대체 금지를 확인했다. 기존 n8n Code 로직 JavaScript 13개도 통과했다. 실제 OpenAI API·DB·pgvector·n8n HTTP 실행은 이번에 수행하지 않았다.

지혜님 P0-5 후 확장 활성화·실제 두 테이블/제약·검색 계정 SELECT 권한·vector 차원·접속/트랜잭션·timeout·정확검색 실행계획을 확인해야 한다. 다혁님·오현님과 직원 권한 출처와 서버 호출 신뢰 경계, H-Y01 최종 오류 형식 및 본체 HTTP 연결 예산을 확정한 뒤 연결한다. 실제 IT 검색은 계속 비활성이다. 실제 색인·질의 임베딩 모델 일치, 관리자 양성 사례, 성능·품질·비용은 미검증이다.

### STEP 5 독립 리뷰 PARTIAL 결함 보완

독립 리뷰에서 교체 repository가 반환한 4개 결과·metadata를 공통 경계가 그대로 정상 응답에 넣는 P1, dispatch의 Mock 분기가 공백 query를 제공자에 전달하는 P2, 잘못된 repository 결과·score 경계 회귀 부족 P2가 확인되어 완료 판정을 보류했다.

rag_search.py에 validate_evidence를 추가했다. repository 규약은 list/tuple의 dict 항목이며 최대3개, doc/section/text는 비공백 문자열, score는 bool 제외 유한 int/float만 허용한다. 잘못된 결과는 기존 503/search_unavailable로 처리하고 초과 결과를 잘라 성공 처리하지 않는다. 추가 metadata·DB/debug 필드는 네 공개 필드만 새 dict로 투영해 제거한다. 기본 PgvectorSearchAdapter와 교체 repository 모두 같은 함수로 검증한다. 점수에 새 범위·확률 정책을 추가하지 않았다. 유한 score의 실제 cosine 산출·의미는 SQL/DB 통합 검증 대상이며 -1을 0으로 자르지 않는다.

공통 valid_query를 dispatch 모드 분기 전에 적용해 빈·공백·비문자열을 Mock과 임베딩 제공자 호출 전에 차단한다. 반환은 기존 Python 내부 안전 실패 503이며 최종 입력 오류 HTTP 계약의 확정이 아니다. SQL·워크플로우·Index는 수정하지 않았다.

신규 회귀 13개: 4건 결과 거절, 추가 필드 제거/원본 불변, 필수 필드 누락, 문자열 타입·빈 값, 잘못된 score, 잘못된 컬렉션/항목, 정상1~3개/tuple, 빈 결과, 유한 score 경계, 양 모드의 잘못된 query 제공자 0회, 정상 명시 Mock, repository 예외 비노출, IT 요청의 모든 의존성 호출0회. Python 전체135개(기존108+STEP5 최초14+보완13) 통과/실패0, JavaScript 기존13개 통과/실패0.

기존 테스트와 별도 일회성 재현도 확인했다: repository 4개 반환은503, 1개+metadata는 네 공개 필드만200, Mock 공백 query는503/제공자0회다. 최초 두 결함의 동작은 재현되지 않았다. JSON4노드/3연결·HeaderAuth·비활성, SQL 권한 WHERE 유지, 비밀값 패턴 검사, git diff --check를 확인했다. 실제 n8n HTTP·DB·OpenAI는 실행하지 않았다.

보완 후 STEP5의 외부 연결 없는 연결부 준비 범위는 PASS로 판단한다. 실제 DB/임베딩 검색과 본체 통합은 여전히 미완료이며, 권한 전달·최종 오류 계약·timeout/연결 수명·실제 SQL 실행계획·검색 품질은 앞 절의 확인 사항으로 유지한다. 기존 STEP1~4 실행 결과를 이번 버전의 실제 통합 검증으로 확대하지 않는다.

## P1-3 · 평가 도구 준비

rag_verify.py에 evaluate CLI를 추가하고 rag_evaluate.py로 오프라인 비교 조건·지표·시간 집계를 분리했다. 기존 Index CLI와 검색 어댑터/워크플로우는 유지했다. test_evaluation.py는 실제 원본과 무관한 별도 Fake 정답표·결과만 사용하며 P0-2 Q01~16 기대값을 변경하지 않는다. 기본 CLI 실행에서 방식별48회가 미확정 정답/관리자 원문 미확보로 제외됨을 확인했다. 실제 성능 수치는 생성하지 않았다.

Fake 테스트14개는 문서 적중, 절 실패, top3 미적중, 빈 결과, 일부 반복503, evidence 권한 누출, 반복 시간·누락값, 정답 미확정, 관리자 미제공, 답 없음 오답 관측, 비교 조건 불일치, p95/비정상 측정 경계, 기존16후보 제외, 결과 미실행을 검사한다. 지표 정의·입력 규약·CLI는 SEARCH-EVAL.md의 P1-3 절에 기록했다.

실제 평가 전에는 원문 버전과 문서별 해시·권한, 원문으로 고정한 정확한 정답 절·필수 문구, 관리자 문서, 동일 환경의 실제 두 색인, 질의 임베딩/DB/search 관측, 토큰·통화/단가·비용 근거가 필요하다. 현재 실제 결과 import는 활성화하지 않았으며 Fake 집계만 지원한다. DB/API/n8n·색인 생성/삭제·본체 평가·성능 측정은 실행하지 않았다. P1-3은 도구 준비 단계이며 전체 완료가 아니다.

이번 로컬 검증 결과: Python149개(기존135+신규14) 통과, JavaScript13개 통과, 실패0. git diff --check 통과. evaluate 기본 CLI는 실제 검색 미실행인 preparation 모드를 반환했다.

### P1-3 독립 리뷰 결함 수정·재검증

리뷰 PARTIAL의 E01~E05를 수정했다. frozen 필수 문구 타입 검증으로 글자별 포함률 부풀리기를 막고, 결합 절은 별도 평가 sidecar를 P0-2 metadata·본문/원본 해시·문서·순위·범위와 대조한다. C03 응답은 변경하지 않는다. 중복 JSON 키는 CLI 파싱 단계에서 출력 파일을 열기 전에 거절한다. 반복별 순위/문서/절/점수·시간/토큰/청크/비용·환경/모델/설정과 안전한 해시 참조를 보존하며 본문은 출력하지 않고 비공개/미확인 절은 마스킹한다.

비음수 정수 사용량과 actual/estimated 출처를 검증하고, 비용에는 통화·단가 또는 계산 근거 해시를 요구한다. 혼합 출처·통화는 그룹 통계로 분리한다. E06도 최소 보완하여 입력/보고서 해시 marker로 동일 보고서 재추가를 방지하고 기존 문서는 보존한다. 단일 writer 사용이 전제다. 상세 내부 입력 규약은 SEARCH-EVAL.md 보완 절에 기록했다.

회귀15개 추가 후 Python164개(기존149+신규15), JavaScript13개 통과/실패0. 초기 새 테스트1개는 모델명 text-embedding을 본문 키로 오인한 검사 자체의 실패였으며 evidence의 text 필드 유무를 검사하도록 정정 후 모두 통과했다. 잘못된 문구 타입, 결합 절 양성·유사 절/다른 문서 음성, metadata 불일치, 소수 사용량, 출처 없는 비용, 실제/추정 분리, 반복 추적·마스킹·안전한 참조, 중복 JSON의 출력 불변과 중복 보고서 방지를 검증했다. git diff --check 통과.

P1-3 오프라인 도구의 요청된 결함 보완 범위는 PASS다. 실제 원본/정답표 고정·관리자 원문·두 색인·DB/API 연결·본체 관측·원문 범위 진위·실제 토큰/가격 근거와 성능 측정은 미완료다. 실제 검색 품질 평가 완료를 뜻하지 않으며 commit/push는 수행하지 않는다.
