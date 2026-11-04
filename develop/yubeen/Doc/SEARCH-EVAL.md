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
