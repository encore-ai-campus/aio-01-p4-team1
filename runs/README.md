# runs · 실서버 시험 및 측정 영수증 인덱스

본 디렉터리는 오케퐁(OKE-Pong) 실서버(`https://aio-t1.isitsoft.kr`) 및 통합 검증에서 수집된 실행·측정 JSON 영수증 정본을 보관합니다. 모든 문서는 비밀값과 개인정보를 마스킹/제거한 상태로 기록되었으며, 최초 실패 진단부터 복구·재시험 PASS까지의 전 과정을 투명하게 추적할 수 있습니다.

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

## 2. 팀원별 세부 실험 및 회귀 영수증 보관 위치

- **박지혜 (Backend · DB · RBAC)**: [`develop/jihye/runs/`](../develop/jihye/runs/)
- **신유빈 (RAG · Chunking · Vector Search)**: [`develop/yubeen/runs/`](../develop/yubeen/runs/)
- **임다혁 (Support v18 로컬 회귀 · 점수 분포 · 3회 반복 · 실서버 1/2차)**: [`develop/dahyeok/runs/`](../develop/dahyeok/runs/)
- **이원민 (C04/C05 앱 통합 · Error Trigger · WF-02b/WF-09 라이브 QA)**: [`develop/wonmin/runs/`](../develop/wonmin/runs/) (`runs/INDEX.md` 참조)

> 모든 수치는 [워크플로우 실행 결과서 (`docs/EXECUTION-RESULT.md`)](../docs/EXECUTION-RESULT.md), [RAG 아키텍처 설계서 (`docs/RAG-ARCHITECTURE.md`)](../docs/RAG-ARCHITECTURE.md), [워크플로우 설계서 (`docs/WORKFLOW-DESIGN.md`)](../docs/WORKFLOW-DESIGN.md)와 1:1로 대응합니다.
