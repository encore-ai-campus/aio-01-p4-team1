# runs · 실서버 시험 및 측정 영수증 인덱스

본 디렉터리는 오케퐁(OKE-Pong) 실서버(`https://aio-t1.isitsoft.kr`) 및 통합 검증에서 수집된 실행·측정 JSON 영수증 정본을 보관합니다. 모든 문서는 비밀값과 개인정보를 마스킹/제거한 상태로 기록되었으며, 최초 실패 진단부터 복구·재시험까지의 이력을 투명하게 추적할 수 있습니다.

## 1. 핵심 실서버 영수증 목록 (2026-11-06 ~ 2026-11-07)

| 영수증 파일 | 담당 / 영역 | 검증 대상 및 핵심 실측 결과 |
| :--- | :--- | :--- |
| [`rag-search-eval-20261107.json`](./rag-search-eval-20261107.json) | 신유빈 (RAG · 검색) | **사내 규정 8문서 33청크(`all` 7문서/30청크, `it` 1문서/3청크), `text-embedding-3-large` 3072차원 DB 검증 및 WF-05 권한 격리 실측.**<br>- 동일 보안사고 질의 시 `access_levels=["all"]`에서 IT 전용 규정(`security-incident`) 누출 **0건**(`wf05_leaked_it_count: 0`)<br>- `access_levels=["all","it"]`에서 `security-incident` 2건 정상 반환(HTTP 200)<br>- 인증 누락(403) 및 잘못된 `top_k`(400 `invalid_request`) 방어 확인 |
| [`support-v18-integration-20261107.json`](./support-v18-integration-20261107.json) | 임다혁 (메인 워크플로우 v18) | **`oke-support` v18 (63노드, N12 기준값 0.40) 실서버 직접 호출 검증.**<br>- **WF-01**: 자동 답변 정상 반환 (`password-policy` 근거 2건, score `0.6687`/`0.6679`), 1차 콜드 스타트 11.9s 이후 4회 연속 재측정 **7.0s · 4.3s · 6.2s · 4.0s** (전원 8초 이내)<br>- **WF-02**: 모호한 질문 1차 보완 질문(`접속 대상 / 오류 메시지 / 발생 시점`) 2.01s PASS<br>- **WF-02b / WF-03**: 담당자 이관 경로 정상 분기 및 당시 하위 C04 장애 시 워크플로우 중단 없이 `handoff_unavailable` 안전 응답(HTTP 200) 격리 확인 |
| [`live-integration-qa-20261107.json`](./live-integration-qa-20261107.json) | 이원민 (QA · 안정성 / Handoff) | **실서버 `oke-handoff` HTTP 500 장애 원인 진단 영수증 (실패 ➔ 원인 규명 ➔ 복구 연결 근거).**<br>- 현상: 공용 VM `/webhook/oke-handoff` 호출 시 `Cannot read properties of null (reading 'disabled')` (HTTP 500) 및 DB 변화 0건(`tickets: 32`, `alerts: 35`, `dlq: 8` 유지)<br>- 읽기 전용 진단 결과: VM 게시본(`okeHandoffFlow01`)에 입구 웹훅 노드(`H01 Handoff Webhook`)가 유실되어 **29노드**로 등록된 상태임을 규명 (`main` 정본은 **30노드**)<br>- **후속 복구 및 재검증 완료**: 총괄 집무실에서 H01 웹훅 노드를 포함한 **30노드 정본 재게시(Publish)** 완료 후 실서버 재호출 시 1차 `ticket_id: "T-2033"`, `duplicate: false`, `alerted: true` (HTTP 200 OK) 및 2차 동일 `request_id` 재전송 시 `ticket_id: "T-2033"`, `duplicate: true` (HTTP 200 OK)로 **WF-09 멱등성 100% 정상화 확인** |
| [`vm-search-observed-20261106.json`](./vm-search-observed-20261106.json) | 이원민 (QA · 검색 연동 진단) | **실서버 `oke-search`(`okeSearchFlow01`) 및 `rag-search` 컨테이너 연동 관측 영수증.**<br>- PostgreSQL 8문서 33청크, `text-embedding-3-large` 3072차원 일치 확인<br>- 직접 검색 호출(HTTP 200, evidence 3건, 1.404s) 및 운영 백엔드 컨테이너(`oke-backend-1`) 경유 n8n 웹훅 호출(HTTP 200, `ok: true`, evidence 3건, 2.227s) 정상 동작 확인 |

---

## 2. 팀원별 세부 실험 및 회귀 영수증 보관 위치

- **신유빈 (RAG)**: [`develop/yubeen/runs/`](../develop/yubeen/runs/)
- **임다혁 (Support v18 로컬 회귀 · 점수 분포 · 3회 반복)**: [`develop/dahyeok/runs/`](../develop/dahyeok/runs/)
- **이원민 (C04/C05 앱 통합 · Error Trigger · WF-02b/WF-09 라이브 QA)**: [`develop/wonmin/runs/`](../develop/wonmin/runs/) (`runs/INDEX.md` 참조)

> 모든 수치는 [워크플로우 실행 결과서 (`docs/EXECUTION-RESULT.md`)](../docs/EXECUTION-RESULT.md), [RAG 아키텍처 설계서 (`docs/RAG-ARCHITECTURE.md`)](../docs/RAG-ARCHITECTURE.md), [워크플로우 설계서 (`docs/WORKFLOW-DESIGN.md`)](../docs/WORKFLOW-DESIGN.md)와 1:1로 대응합니다.
