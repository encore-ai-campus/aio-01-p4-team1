# runs · 실서버 시험 및 측정 영수증 인덱스

본 디렉터리는 오케퐁(OKE-Pong) 실서버(`https://aio-t1.isitsoft.kr`) 및 통합 검증에서 수집된 실행·측정 JSON 영수증 정본을 보관합니다. 모든 문서는 비밀값과 개인정보를 마스킹/제거한 상태로 기록되었으며, 최초 실패 진단부터 복구·재시험 PASS까지의 전 과정을 투명하게 추적할 수 있습니다.

## 2026-11-09 유빈님 RAG 격리 실험 취합

`feat/yubeen-p0@70c215a`에서 전달받은 개인 실험 근거다. [RAG 정본](../docs/RAG-ARCHITECTURE.md)과 [취합·재계산 기록](rag-handoff-review-20261109.json)에서 작성자 원본 경로·해시와 main의 보관 위치를 대응한다. 아래 JSON 10개는 원본 바이트를 보존했으며, 원본 내부의 옛 경로는 당시 이력이다. 운영 VM 시험·전체 직원 권한 경로·공식 전체 시험과 합산하지 않는다.

| 근거 | 결과·범위 |
| --- | --- |
| [로컬 청킹 계산](chunk-comparison-local-20261109.json) | 동일 원본 8종, 절 33·300자 14청크. 원문 보존·길이 분포 |
| [승인 정답표](rag-ab-answer-key-frozen-20261109.json)·[승인 권한표](rag-ab-permissions-approved-20261109.json) | 격리 품질 평가의 양성 11문항. 기존 cases 정본 변경 없음. 원본별 해시·권한은 main과 8/8 일치 |
| [첫 실패](rag-ab-actual-20261109.json)·[인증 확인](rag-api-auth-probe-20261109.json)·[재실행 전 조건](rag-ab-preflight-rerun-20261109.json) | 401 실패·두 DB 0/0과 별도 인증 1회, 초회 색인 전 빈 DB 조건을 보존 |
| [격리 A/B 실행](rag-ab-actual-rerun-20261109.json)·[단일 청크 근거 감사](rag-ab-evidence-audit-20261109.json) | 양성 11개×3회×2방식=SQL 66회. 문서 Hit@3는 동률, 필수 근거는 절 33/33·300자 30/33. 임베딩 58회·6,402토큰 |
| [벡터 대용 권한 검사](rag-ab-security-proxy-20261109.json) | 기존 IT 문서 벡터를 질의 대용으로 사용, 새 API 0회. 실제 질문·세션 경로와 구분 |
| [실제 Q08·답 없음 후보 검색](rag-final-q08-noanswer-20261109.json) | 추가 임베딩 3회·80토큰, SQL 8회. 일반 IT 문서 노출 0건. Q12/Q13은 승인 전 후보, 답변 생성 미실행 |
| [취합 검토](rag-handoff-review-20261109.json)·[비밀 검사](secret-scan-rag-publication-20261109.json) | main 청킹 코드·원문으로 근거 해시·순위 재대조, 원본·사용량 해시 검증. 새 서비스 호출·배포 없음 |

## 2026-11-09 Mac 정상 요청과 운영 VM pull 영향

앞선 83회와 별도로 사용자가 Mac에서 보낸 정상 요청 2건을 보관한다. 최신 판단과 남은 작업은 [검토 문서](../docs/DAY82-TEST-REVIEW.md)의 마지막 절을 따른다.

| 근거 | 결과와 범위 |
| --- | --- |
| [Mac 정상 요청 1](local-webhook-check-20261109-120352.json) | 12:03 KST, 1회 PASS·4.602초·규정 출처·티켓 없음. 직접 웹훅이며 FE/API/DB 연결 시험은 아님 |
| [Mac 정상 요청 2](local-webhook-check-20261109-120455.json) | 12:04 KST, 1회 PASS·5.273초·규정 출처·티켓 없음. 원본과 수집 도구 해시 확인 |
| [운영 VM pull 영향 확인](vm-pull-safety-20261109.json) | 11:52 KST 읽기 조회를 필요한 필드로 내보냄. 기존 data-api bind 파일 22개와 서버 파일이 main의 옛 경로에 없어 직접 pull을 피함. 실제 pull·배포·재시작 없이 컨테이너 9개 동일·확인한 GET 200 |
| [추가 반영 비밀 검사](secret-scan-local-publication-20261109.json) | 기존 검토 예외를 적용한 작업 트리 텍스트 범위. Git 과거 이력·바이너리 전체 검사는 아님 |

## 2026-11-09 후속 시험 · 83회 검토

읽기 쉬운 [후속 검토 문서](../docs/DAY82-TEST-REVIEW.md)와 [검토 집계](day82-reviewed-results-20261109.json)가 현재 판단 기준이다. **새 실제 요청 83회**이며 공식 공통·팀 전체 통과가 아니다. 원본의 최초 판정·pending과 검토 후 판단을 구분한다.

| 원본 | 실행 범위·결과 |
| --- | --- |
| [공통 반복](common-repeat-20261109.json) | 정상 LLM 9유형·새 3회·30요청. 실제 출력 대조 후 해당 범위 기대와 일치. WF-07 내보내기 판정 문제는 검토 집계에서 원시 실행 재조회와 함께 정정 |
| [팀 반복](team-repeat-20261109.json) | 정상 10유형·3회·33요청. 7유형 3회 일치, TM-04 실패·TM-13 2/3·TM-12 정답 근거 조건 미충족 |
| [app 요청 한정 티켓 장애](app-scoped-ticket-repeat-20261109.json) | 실패·동일 ID 복구 3회와 장애 중 정상 문의 1회, 총 7요청. 정본 practice와 다른 app 대응 시험 |
| [기존 티켓 지연](ticket-lookup-slow-20261109.json) | 8초 지연에서 3회 안전 이관·8초 이내 및 해제 후 정상 조회, 총 4요청 |
| [Error 자동 발화·복구](error-auto-recovery-20261109.json) | 실제 실패 부모 2건 → 자동 Error → 알림·DLQ 저장 → 같은 ID 수동 정상 재요청, 총 4요청. 오류 위치 unknown 1건 보존 |
| [VPN 벤치](webhook-bench-20261109.json) | 5회 정상 답변. p50 4.184초·p95/최대 4.241초. 직접 웹훅·새 ID·예열/자동 재시도 없음 |
| [종료 상태·원시 출력 재조회](post-test-state-20261109.json) | app·장애 해제·health 200·활성 4종 비교 일치. TM-13 출처 탈락과 WF-07 실제 마스킹을 원래 실행에서 읽기 확인 |
| [원본 노드 격리 검사](isolated-node-fault-check-20261109.json) | 오프라인 합성 입력만 사용. live WF-10/TM-14 성공으로 집계하지 않음. 90→91일 거절 승격 결함 재현 |
| [검사 도구 오프라인 검사](test-harness-offline-checks-20261109.json) | 판정·민감정보 탐지·예외 시 장애 정리의 가짜 통신 검사. 실제 서비스 검사 건수와 구분 |
| [결과 반영 비밀 검사](secret-scan-remaining-20261109.json) | 기존 검토 예외의 작업 트리 텍스트 검사. Git 과거 이력·바이너리 전체 검사는 아님 |

개인정보 검사기의 점수 숫자 오탐으로 중단한 [원래 기록](team-interrupted-20261109.json)과 [실제 문자열 재조회](team-detector-review-20261109.json)를 보존했다. 기록된 요청을 재전송하지 않고 재개했다. 원본 파일 내부의 이전 수집 파일명은 검토 집계의 source_artifacts에서 현재 보관 파일명으로 대응한다. 외부 파일을 실행 의존성으로 요구하지 않는다.

## 2026-11-09 최초 단회 확인

| 근거 | 결과와 범위 |
| --- | --- |
| [공통 사례 · 장애 설정 제외](common-no-fault-20261109.json) | 10:08~10:09 KST, 공통 14유형 중 11유형·13입력·14회 HTTP 요청. WF-13 세 입력과 WF-09 두 번 전송 포함. 자동 검사 및 답변·실행 기록 검토에서 이번 범위의 기대와 일치. 티켓·알림 각 +5, DLQ 증감 없음. 공식 CLI 원본 전체 실행·FE 종단 시험·3회 반복과 구분 |
| [인증 단건 확인](webhook-auth-check-20261109.json) | 09:50 KST, 인증된 빈 질문 1건이 HTTP 400·question_required로 거절됨. 실행 352, Agent·이관 실행 없음. 모든 인증 거절 조건을 시험한 결과는 아님 |
| [main·VM 대조 기록](vm-main-comparison-20261109.json) | 07:12 KST에 수행한 읽기 대조의 감사 메모를 옮긴 요약. 활성 4종의 비교한 구현 필드는 일치. VM Git·RAG/data-api 경로와 일부 설정 차이는 남음. 원시 터미널 출력·파일별 대조 해시는 포함하지 않음 |
| [이번 결과 취합의 비밀 검사](secret-scan-results-publication-20261109.json) | 기존 검토 예외를 적용한 작업 트리 텍스트에서 탐지 0건. 관측 파일의 내보내기·출처 해시·새 링크도 확인. Git 과거 이력·바이너리 이미지 검사는 아님 |

최초 단회 시점에는 공통 장애 WF-04·WF-10·WF-11, 팀 전체, LLM 3회 반복·벤치, 새 Error 자동 발화·복구가 미실행이었다. 후속 수행 범위는 위 최신 검토에 구분했다. WF-10·TM-14 실서비스 주입과 전체 통과는 여전히 확인하지 못했다. 외부 알림 수신·관리자 화면 검사는 별도다. 시험용 보조 파일은 환경별 의존성이 있어 제출용 재현 도구로 포함하지 않았다. JSON은 관측 기록이며 보조 파일을 실행 의존성으로 요구하지 않는다.

## 1. 핵심 실서버 영수증 목록 (2026-11-06 ~ 2026-11-07)

| 영수증 파일 | 담당 / 영역 | 검증 대상 및 핵심 실측 결과 |
| :--- | :--- | :--- |
| [`be-db-integration-20261107.json`](./be-db-integration-20261107.json) | 박지혜 (백엔드 · DB / RBAC) | **실서버 FastAPI 세션 인증·RBAC 보안 경계 및 PostgreSQL 트랜잭션 검증 (`PASS_REQUIRED_CHECKS`).**<br>- 비로그인 `GET /api/auth/me` **401** ➔ 직원 로그인 **200** (`HttpOnly` 세션 쿠키 발급 확인) ➔ 직원 세션의 관리자 API(`GET /api/admin/tickets`) 접근 **403 차단(RBAC 실증)**<br>- 직원 문의(`POST /api/ask` **200**, `route="자동 답변"`, source 1건) ➔ 내 문의 목록(`GET /api/my-requests` **200**, 고유 `request_id` 1건 일치) ➔ 관리자 로그인 **200** 및 티켓 목록 **200** ➔ 양쪽 세션 로그아웃 **200**<br>- 웹 터미널 TLS 검증 세션에서 `oke-postgres-1` 읽기 전용 트랜잭션(`BEGIN READ ONLY / SELECT / COMMIT`)으로 `app.inquiries`에 `status="completed"` 1건 저장 확인 |
| [`rag-search-eval-20261107.json`](./rag-search-eval-20261107.json) | 신유빈 (RAG · 검색) | **사내 규정 8문서 33청크(`all` 7문서/30청크, `it` 1문서/3청크), `text-embedding-3-large` 3072차원 DB 검증 및 WF-05 권한 격리 실측 (`PASS`).**<br>- 동일 보안사고 질의 시 `access_levels=["all"]`에서 IT 전용 규정(`security-incident`) 누출 **0건**(`wf05_leaked_it_count: 0`)<br>- `access_levels=["all","it"]`에서 `security-incident` **2건** 정상 반환(HTTP 200)<br>- 인증 누락(403) 및 잘못된 `top_k`(400 `invalid_request`) 방어 확인 |
| [`support-v18-integration-20261107.json`](./support-v18-integration-20261107.json) | 임다혁 (메인 워크플로우 v18 · 복구 후 2차 재시험) | **VM `oke-handoff` 30노드 복구 직후 `oke-support` v18 (63노드, N12 기준값 0.40) 실서버 재시험 (`PASS`).**<br>- **WF-01 (정상 자동답변)**: `password-policy` 근거 2건(score `0.6687`/`0.6679`) 자동 답변 반환; 첫 호출 8.754s 이후 연속 3회 재측정 **6.9s · 4.8s · 3.8s** (전원 8초 이내)<br>- **WF-02 (1차 보완 질문)**: `접속 대상 / 오류 메시지 / 발생 시점` 되묻기 **1.812s PASS**<br>- **WF-02b (보완 한도 도달 이관)**: 담당자 이관(`reason="max_attempts"`) 및 신규 티켓 **`T-2035`** 발급 성공 (**2.188s PASS**)<br>- **WF-03 (무근거 질의 이관)**: 담당자 이관(`reason="low_confidence"`, `sources=[]`) 및 신규 티켓 **`T-2036`** 발급 성공 (**3.004s PASS**) |
| [`support-v18-integration-20261107-before-fix.json`](./support-v18-integration-20261107-before-fix.json) | 임다혁 (메인 워크플로우 v18 · 1차 복구 전 기록) | **`oke-handoff` H01 복구 전 1차 실서버 호출 기록 (하위 장애 격리 증빙).**<br>- WF-01 자동 답변(재측정 4회 `7.0s · 4.3s · 6.2s · 4.0s`) 및 WF-02 보완 질문(`2.01s`) 통과<br>- 하위 C04(`oke-handoff`)가 HTTP 500인 상황에서도 메인 워크플로우가 중단되지 않고 HTTP 200 + `route="담당자 이관"` + `reason="handoff_unavailable"`로 안전 격리 종료됨을 입증 |
| [`live-integration-qa-20261107T113546Z.json`](./live-integration-qa-20261107T113546Z.json) | 이원민 (QA · 안정성 / WF-09 복구 후 재시험) | **`oke-handoff` 30노드 정본 재게시 후 실서버 WF-09 멱등성 및 DB 정합성 재시험 (`PASS_WF09`, 7/7 통과).**<br>- 사전 점검(`preflight`): `active=true`, `node_count_30=true`, `h01_webhook_present=true`, `h01_connected_to_h02=true` 확인<br>- 1차 호출: HTTP 200 OK, `ticket_id: "T-2034"`, `priority: "high"`, `duplicate: false`, `alerted: true`, `dlq: false` (2.257s)<br>- 2차 동일 `request_id` 재전송: HTTP 200 OK, 동일 `ticket_id: "T-2034"`, `duplicate: true`, `alerted: true`, `dlq: false` (0.594s)<br>- PostgreSQL 실측 증감: 1차 후 `tickets +1 (33➔34)`, `alerts +1 (36➔37)`, `dlq +0 (8➔8)` / 2차 재전송 후 **`tickets +0`, `alerts +0`, `dlq +0`** (중복 티켓·중복 알림 0건 완벽 보장) |
| [`live-integration-qa-20261107.json`](./live-integration-qa-20261107.json) | 이원민 (QA · 안정성 / 1차 장애 원인 규명) | **실서버 `oke-handoff` HTTP 500 장애 원인 규명 영수증 (실패 ➔ 원인 진단 근거).**<br>- 공용 VM `/webhook/oke-handoff` 호출 시 `Cannot read properties of null (reading 'disabled')` (HTTP 500) 및 DB 변화 0건(`32/35/8`) 관측<br>- 읽기 전용 진단으로 VM 게시본(`okeHandoffFlow01`)에 입구 웹훅 노드(`H01 Handoff Webhook`)가 유실되어 **29노드**로 등록된 상태임을 규명(`main` 정본은 **30노드**) ➔ 총괄 집무실 정본 재게시(`T-2033`, `T-2034`, `T-2035`, `T-2036` 연속 통과)로 해결 |
| [`vm-search-observed-20261106.json`](./vm-search-observed-20261106.json) | 이원민 (QA · 검색 연동 진단) | **실서버 `oke-search`(`okeSearchFlow01`) 및 `rag-search` 컨테이너 연동 관측 영수증.**<br>- PostgreSQL 8문서 33청크, `text-embedding-3-large` 3072차원 일치 확인<br>- 직접 검색 호출(HTTP 200, evidence 3건, 1.404s) 및 운영 백엔드 컨테이너(`oke-backend-1`) 경유 n8n 웹훅 호출(HTTP 200, `ok: true`, evidence 3건, 2.227s) 정상 동작 확인 |

---

## 2026-11-08 후속 확인

- [통합 후속 확인 요약](integration-followup-20261108.json): 변경 범위, 유지된 컨테이너, 시험별 한계와 새 API 재시험의 계정 인계 조건.
- [DB 연결 확인](db-link-followup-20261108.json): 기존 실요청 `T-2030`의 문의·티켓·알림 연결과 소유권·키·응답 일치. 읽기 전용 조회이며 API 요청 재실행은 아님.
- [변경 전 응답 시간](workflow-latency-before-20261108.json): 12.425초·4.612초·3.633초. 첫 측정 8초 초과 기록 보존.
- [변경 후 응답 시간](workflow-latency-after-20261108.json): 실행기 유휴 종료 해제 후 7.224초·3.864초·3.887초. 숨은 예열 없이 20초 유휴 구간 포함.
- [n8n 노드별 시간](workflow-node-timings-20261108.json): 위 6개 실제 실행의 노드별 시간. 입력·답변·Credential 제외.

재실행 명령은 [실서버 검사 안내](../eval/LIVE-CHECKS.md)를 따른다. 위 지연 시험은 직접 n8n 웹훅 경로이며 FE/API 전체 지연이나 전체 스택 재시작 직후의 성능을 입증하지 않는다.

## 2. 기록 범위

이 폴더에는 위 표의 제출 영수증을 포함한다. 과거 결과서의 개인 개발 경로는 당시 실행 이력이며 현재 실행에 필요하지 않다. 제출본의 재현 명령과 검증 범위는 [SUBMISSION](../SUBMISSION.md)을 따른다.

> 모든 수치는 [워크플로우 실행 결과서 (`docs/EXECUTION-RESULT.md`)](../docs/EXECUTION-RESULT.md), [RAG 아키텍처 설계서 (`docs/RAG-ARCHITECTURE.md`)](../docs/RAG-ARCHITECTURE.md), [워크플로우 설계서 (`docs/WORKFLOW-DESIGN.md`)](../docs/WORKFLOW-DESIGN.md)와 1:1로 대응합니다.

## 실제 화면과 제출 비밀 검사

- [실제 서비스 화면 캡처](ui-captures-20261108.json): 기존 문의·티켓을 열어 캡처한 웹 화면 8장. 새 문의·티켓 수정·장애 주입 없음.
- [실제 n8n 화면 캡처](n8n-ui-captures-20261108.json): 기존 실행 ID 256·271·276의 흐름·최종 응답 6장. 정상 답변·인젝션 차단·긴급 이관을 기존 보고서와 대조했고 실행·편집·게시 없이 조회했다.
- [제출 비밀 검사](secret-scan-20261108.json): 공식 tscan·오탐/고정 가상 데이터 검토 후 0건, Git 추적 텍스트의 실제 비공개 값 일치 0건. 예외와 범위는 [비밀 검사 안내](../eval/SECRET-SCAN.md).
- [n8n 캡처 추가 후 비밀 검사](secret-scan-after-n8n-20261108.json): n8n 로그인 정보까지 실제 비공개 값 비교에 포함해 재검사.
