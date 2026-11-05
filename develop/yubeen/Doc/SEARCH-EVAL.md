# P0-2 검색 평가 준비

상태: 실제 검색·임베딩·DB·본체 연결·품질 평가는 미실행. 아래 계약 예시와 정답표 초안은 실측 자료가 아니다. Q01~Q16은 cases/rag-search.json, 권한 요청 쌍은 requests/search-all.json 및 search-it.json에 있다.

## 정답표와 변경 관리

- 버전 p0-2-draft-v1, draft_not_frozen. Q01~11은 SPEC 시작안을 전사한 초안이며 필수 답 문구는 원문 확인 전이라 verified_required_quotes가 비어 있다. 임의 숫자·절 제목·답변을 보충하지 않았다.
- Q12~13은 답 근거 없음 질문으로 별도 집계한다. 벡터 후보가 반드시 0개라고 가정하지 않는다. 실제 원문 대조는 미검증이다.
- Q14~16은 질문·기대 문서·절을 null로 두고 not_executed로 표시했다. 권한 입력만 all/all+it/all로 준비했다.
- 원문 확보 후 검색 전에 원본 해시·정확한 절·필수 답 문구를 대조해 새 버전으로 고정한다. history에 변경 날짜·이유·검색 전/후와 근거를 추가한다. 검색 결과에 맞춰 기대를 자동 갱신하는 코드는 없다. 실제 원문 검증/정답표 고정은 현재 미완료다.

## C03 합성 계약 예시

cases/rag-search.json의 functional_cases는 품질 질문과 분리된 준비 자료다. 실제 검색 실행 결과가 아니다.

| 사례 | HTTP | 형식/판정 |
| --- | --- | --- |
| F01 정상 | 200 | ok=true, doc/section/text/score 근거 1개, reason=null. mock-public은 합성 문서이며 score=0.5는 임의 형식 예시 |
| F02 후보 없음 | 200 | ok=true, evidence=[], reason=no_evidence |
| F03 검색 장애 | 503 | ok=false, evidence=[], reason=search_unavailable. 본체가 이관 |
| F04 잘못된/누락 권한 | 미확정 | 검색/임베딩 실행 및 권한 확대 금지. 상세 HTTP/오류 코드는 H-Y01 제안 상태, 확정 응답으로 생성하지 않음 |

요청은 request_id/query/type/access_levels/top_k를 사용하고 top_k=3이다. all과 all+it는 본체가 직원 조회로 확인한 값이어야 한다. 요청 JSON은 합성 입력이며 인증 키를 포함하지 않는다. 실제 관리자 문서의 검색 성공을 주장하지 않는다. type 추가 필터·임계값·시간 예산은 별도 제안을 확정하지 않는다.

## 실제 평가 기록 양식

원본/설정 버전과 정답표를 고정한 뒤 동일 질문을 방식별 3회 측정한다. 색인은 격리 DB에서 순차 비교하며 두 방식을 섞지 않는다. 실패도 결과에서 제외하지 않고 기록한다.

| 실행/질문 ID·반복 | 원본/설정 해시·청킹 | 권한·기대 doc/절·답 문구 | 실제 순위별 doc/절/chunk_no/원문범위/score | doc/절/근거 판정 | HTTP·reason·권한 누출 | 임베딩/DB/search/본체 시간 | 실행 근거·Mock 여부·미해결 |
| --- | --- | --- | --- | --- | --- | --- | --- |

| 방식 | 문서/청크 수·거절 수 | 본문/content 길이 최소·중앙·최대 | hit@3·절 hit@3·근거 포함률(분자/분모) | 답 없음 오답·권한 누출 | 시간 N·중앙·p95·최대 | 실제 토큰·비용 출처 | 판정·남은 문제 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| section | 미측정 | 미측정 | 미측정 | 미측정 | 미측정 | 미측정 | 실제 검색 미실행 |
| 300 | 미측정 | 미측정 | 미측정 | 미측정 | 미측정 | 미측정 | 실제 검색 미실행 |

hit@3와 절 hit@3 분모는 답 존재 질문, 근거 포함률은 실제 top3가 필수 답 문구를 뒷받침한 비율이다. Q12~13은 별도 집계한다. 점수는 1-cosine distance이며 확률이 아니다. 시간은 단조 시계로 구별 측정하며 p95는 정렬한 N개 중 올림(0.95×N)번째 값이다. 후보/evidence/LLM 입력/일반 로그 권한 누출 요구는 0건이나 현재 실제 관측하지 않았다. 품질·시간·임계값 목표 통과는 미판정이다.

## 독립 평가 보완 · p0-2-draft-v2

기존 Q01~16 질문·권한·기대·상태는 유지하고, evidence_review에 절/답 근거 미분리 여부와 원문 대조 필요를 기록했다. 두 draft 값이 같아도 검증된 정답이 아니며 separation_verified=false다. verified_required_quotes는 여전히 비어 있다. history에 검색 전 변경 이유를 추가했다.

functional_cases는 기존 F01~04를 보존하고 다음 합성 사례를 추가했다. 모두 실제 검색 미실행이며 아래 테스트는 사례 구조와 기대값의 정합성 검사다. SQL/DB/임베딩 기능 실행 통과를 뜻하지 않는다.

| ID | 기능 사례 | 고정된 합성 기대 |
| --- | --- | --- |
| F05 | 동점 후보 정렬 | distance ASC → doc_key ASC → chunk_no ASC, top_k=3 |
| F06 | 일반 입력 불량 | 검색/임베딩 미실행. 상세 HTTP/응답은 null이며 H-Y01 제안 상태 |
| F07 | DB 오류 | HTTP503, ok=false, evidence=[], reason=search_unavailable |
| F08 | 임베딩 오류 | 같은 HTTP503 형식, 원인별 합성 입력은 분리 |
| F09 | 검색 시간 초과 | 같은 HTTP503 형식, 원인별 합성 입력은 분리 |
| F10 | 질문의 관리자 주장 | 검증된 all을 유지. 질문으로 it 추가 금지, 허용 후보 all만 |

API CLI inventory/compare-chunks는 기본 네트워크 차단이며 종료 코드 2와 api_network_not_authorized를 출력한다. 사용자 승인 후 실제 실행할 때만 --allow-network 옵션을 명시한다. 옵션 자체는 승인을 대신하지 않는다. 주입된 가짜 전송은 허용 옵션 없이 테스트할 수 있으며, 실제 http_transport를 선택하는 경로는 collect_api의 allow_network=True가 필요하다. 이번에는 허용 경로도 가짜 전송으로만 확인했으며 실제 요청은 하지 않았다.

## P1-3 오프라인 평가 도구 준비

CLI(작업 폴더 develop/yubeen):
`python3 tools/rag_verify.py evaluate --cases cases/rag-search.json --repeats 3 --output Doc/SEARCH-EVAL.md`

기본 실행은 외부 호출·색인 없이 준비 상태만 집계한다. 현재 Q01~16은 정답 미확정이라 방식별48개 반복을 제외하며 성능값은 null이다. output은 기존 문서에 추가한다. 로컬 Fake 결과를 시험하려면 `--results <로컬 JSON 경로>`를 추가한다. 현재 Fake 모드만 수용하며 실제 실행 보고서 수용은 후속 검증 대상이다. 원래 cases나 정답을 자동 변경하지 않는다.

Fake 입력 규약은 tests/test_evaluation.py의 setUp에 실행 가능한 예가 있다. bundle은 mode=fake, conditions={section:{...},300:{...}}, doc_access={doc_key:all/it}, records 객체다. 두 conditions는 source_hashes(문서별 해시), access_levels(시험할 권한 배열 목록), model, dimensions, distance, top_k, questions_version, repeats, overlap, environment, settings_version을 모두 동일하게 제공해야 한다. 모델 text-embedding-3-large/3072차원/cosine/top3/overlap0을 검사한다. 키 section/300만 비교 방식이며 실제 색인 교체는 하지 않는다. 청크 수는 결과별 기록값이므로 비교 조건 동일성에는 넣지 않는다.

records 키는 `section:질문ID:반복번호` 또는 `300:질문ID:반복번호`(반복1부터)다. 항목에는 http_status와 C03 response, 선택적으로 embedding_ms/db_ms/search_ms/embedding_tokens/chunk_count/cost와 incorrect_auto_answer(bool)를 준다. 없는 측정은 null로 집계하며 임의0·공식 단가로 비용을 채우지 않는다. cost는 입력 작성자가 같은 통화·가격 기준으로 계산한 값이어야 한다. 호출·시간 측정 기능은 없으며 수집된 관측값만 집계한다.

평가 대상은 질문별 source_verified=true, status=frozen, source_hash와 질문이 있고, 답 존재 질문은 expected_doc/expected_section/verified_required_quotes가 있는 경우다. draft 절·문구를 확정값으로 사용하지 않는다. 관리자 원문 미제공은 admin_source_unavailable, 미확정은 answer_key_unfrozen, 관측 누락은 not_executed로 제외한다. 제공된 원본 해시·권한 목록과도 대조한다.

지표 단위는 질문×반복이다. hit@3=기대 문서를 찾은 답 존재 관측/실행된 답 존재 관측, 절 hit@3=같은 문서·정확한 절 적중/같은 분모, 근거 포함률=기대 문서 top3에서 필수 문구 모두를 찾은 관측/같은 분모다. 이는 자동 문자열 포함 검사이며 사람의 의미 검증을 대체하지 않는다. 실행된503도 분모에 남겨 실패로 센다. no_answer는 hit 분모에서 제외하며 incorrect_auto_answer를 실제 관측한 bool 항목만 오답 지표 분모에 넣는다. 근거 후보가 있다는 이유만으로 자동 답변 오답으로 세지 않는다.

권한 누출은 doc_access가 제공된 evidence 항목 중 허용 권한 밖 문서 항목 수/권한을 관측한 evidence 항목 수다. 이는 evidence 범위 관측이며 후보·LLM 입력·로그의 누출0을 입증하지 않는다. 미관측은 분모에 넣지 않는다. 정상(근거있음)/빈 결과/장애를 별도 집계한다.

시간·사용량 각 필드에 N·중앙값·p95·최대를 기록한다. p95는 정렬 후 ceil(0.95×N)번째 관측값이다. 누락 개수를 별도로 보존하며 N=0의 수치는 null이다. 음수·bool·NaN·Infinity 측정은 거절한다. 원본 결과의 시간은 실패 관측도 버리지 않고 제공된 경우 포함한다. 결과에는 질문ID·반복·HTTP·reason·문서ID와 실행 조건을 남기고 원문 본문은 복사하지 않는다.

현재 실제 검색·청킹 품질·hit@3·시간·토큰·비용 측정은 미실행이다. Fake 수치는 평가 코드의 시험 자료이며 실제 RAG 성능이나 P1-3 전체 완료 근거가 아니다.

### P1-3 독립 리뷰 E01~E06 보완 규약

위 초기 규약 중 다음 항목을 보완한다. 기존 결과 이력은 삭제하지 않는다.

- E01: frozen 답 존재 정답표의 verified_required_quotes는 비어 있지 않은 문자열의 비어 있지 않은 list만 허용한다. 문자열 단독·숫자·객체·null·공백 항목은 오류이며, 미확정 정답표는 계속 제외한다. no_answer에는 필수 답 문구를 요구하지 않는다.
- E02: C03 evidence는 변경하지 않는다. 단일 절의 정확 일치는 유지한다. 결합 절은 record.evidence_observations에 rank(1부터), doc, content_hash와 P0-2 metadata를 따로 제공한다. metadata는 chunking, chunking_version=p0-2-v1, source_hash, source_range=[start,end], included_sections를 사용한다. 같은 순위·문서, 실제 evidence 본문 SHA-256, 비교 조건의 문서 원본 해시, 방식, 정확한 절 목록 결합, 유효한 반열린 범위를 모두 대조한다. 출처가 누락·불일치하거나 중복 sidecar이면 결합 절 적중을 인정하지 않는다. 이는 입력 관측의 내부 일관성 검사이며 원문 진위의 독립 인증은 아니다. 원문 전체 길이와 범위의 실제 내용 대조는 원본 확보 후 별도 검증한다.
- E03: evaluate CLI는 정답표와 결과 JSON의 모든 객체에서 중복 키를 파싱 시 거절한다. duplicate_json_key/종료2이며 기존 출력은 변경하지 않는다. 반복 키는 기존 method:id:repeat 형식이며 중복 질문 ID도 거절한다.
- E04: 반복 관측에 method·rank/doc/section/score, 측정값, 출처, 환경·모델·설정 버전을 보존한다. 본문은 저장하지 않으며 doc_access에서 all로 확인되지 않은 문서의 절 이름도 [restricted_or_unknown]으로 가린다. source_ref는 sha256: 뒤 64자리 소문자16진 해시만 허용한다. 경로·URL·임의 메모는 출력하지 않는다. 실제 파일 위치는 저장소 밖의 접근 통제된 대장에서 해시로 연결한다.
- E05: embedding_tokens/chunk_count는 null 또는 비음수 int만 허용한다(bool 제외). 값이 있으면 measurement_provenance의 같은 필드에 kind=actual/estimated와 source_ref를 요구한다. cost에도 같은 출처 구분과 currency(대문자3자), unit_price(비음수 유한 숫자) 또는 calculation_ref(안전한 해시)를 요구한다. source_ref가 가리키는 자료에 단가의 적용 단위·사용량·계산 근거를 보존해야 한다. 시간·사용량·비용의 누락은 null이며 실제/추정 또는 통화가 다르면 measurement_groups로 분리하고 혼합 전체 통계는 N=0/null로 남긴다. Fake 모드에서 actual로 표시한 관측도 Fake 입력 내부의 분류이며 실제 서비스 측정 완료가 아니다.
- E06: input_sha256은 cases/results/repeats의 정규화 해시, report_sha256은 입력 해시를 포함한 결과 해시다. 동일 보고서 marker가 출력에 있으면 재추가하지 않고 기존 내용을 보존한다. 입력이나 계산 결과가 달라지면 새 절을 추가한다. 실행 시각·외부 실행 ID를 만들지 않는다. 병렬 writer의 원자적 잠금은 구현하지 않아 CLI는 단일 writer로 사용한다.

보완 검증: 기존149개에 회귀15개를 추가해 Python164개 통과, JavaScript13개 통과(실패0). 결합 절은 두 방식에서 확인하고 유사 절·다른 문서·누락/변조 metadata는 적중시키지 않았다. 중복 반복 JSON 거절 시 출력 불변, 동일 결과 재실행 시 한 번만 추가를 임시 파일로 확인했다. 원본 정답표·공통 계약·워크플로우는 변경하지 않았으며 실제 검색·DB·API·n8n은 실행하지 않았다.
