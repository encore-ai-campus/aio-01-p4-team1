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
