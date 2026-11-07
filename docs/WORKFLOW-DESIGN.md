# Workflow Design — OKE-Pong n8n v18

> Source workflows: `workflows/oke-support.json`, `oke-index.json`, `oke-search.json`, `oke-handoff.json`, `oke-errors.json`. Approved design baseline: main commits `983f25c` (support v18), `9bdb9c6` (controlled error hook and full execution logging), and `0b848e7` (persistent `settings.errorWorkflow = "okeErrorsFlow01"` binding across `okeSupportFlow01`, `okeSearchFlow01`, and `okeHandoffFlow01`).
> Scope: this document describes the checked-in JSON graph, its actual node names, and the boundary payload contracts. A local JSON snapshot can differ from a separately approved deployment; source discrepancies are called out explicitly.

## 1. v18 behavior, runtime settings, and architecture rationale

- **v18 Main Workflow Architecture (`oke-support.json`, 63 nodes):**
  - FAQ enrichment was streamlined from 5 nodes down to 2 nodes (`N10b FAQ HTTP` → `N10b Match FAQ`), reducing total main workflow complexity from 66 to **63 nodes**. FAQ failure preserves policy-only evidence and never replaces policy citations.
  - **N12 Evidence Gate Threshold (`APPROVED_MIN_SCORE=0.40`):** Based on empirical cosine similarity measurements (`text-embedding-3-large`, `top_k=3`) where in-scope questions scored **0.380–0.709** (median 0.571) and out-of-scope top candidates scored up to **0.383**, replacing the initial Mock threshold (`0.80`) with `0.40`. A source below `0.40` cannot authorize automatic answering.
- **Multi-stage Pipeline Safety Design (`Triage ➔ Search(C03) ➔ Writer ➔ Verifier ➔ Handoff(C04)`):**
  - Rather than relying on a single monolithic prompt, each stage isolates its failure mode to guarantee **"never fabricate when uncertain; escalate safely"**:
    1. **Pre-LLM Rule & Triage Gate:** Malformed inputs (`WF-13`: empty, >500 chars, unknown employee) return HTTP 400 and prompt injection attempts (`WF-08`) are blocked deterministically by `N04 Injection rules` with **0 LLM calls**. Ambiguous requests (`WF-02`, `attempt < 3`) return structured clarifying questions (`접속 대상 / 오류 메시지 / 발생 시점`), while `attempt >= 3` (`WF-02b`) escalates immediately to prevent infinite clarification loops.
    2. **Search (`C03`):** Uses only verified employee department ACL (`IT팀` → `["all","it"]`, general → `["all"]`) and passes top-3 evidence through `N12 Evidence gate` (`>= 0.40`).
    3. **Writer (`N13`):** Generates answers strictly from retrieved `evidence.text`. If the evidence does not directly answer the question, Writer sets `answerable=false` and escalates with `reason="low_confidence"`.
    4. **Verifier (`N14`):** Performs a second-pass sentence-level grounding and policy check (`grounded`, `policy_ok`), catching any hallucinated details or border-score (`0.380–0.40`) false positives before output filtering (`N22 Output filter`, PII masking).
- **Backend RBAC Session Boundary & Sub-workflow Separation, Timeouts, and Live VM Recovery:**
  - **Backend Session Authentication & RBAC Boundary (`C01/C02`, [`runs/be-db-integration-20261107.json`](../runs/be-db-integration-20261107.json)):** FastAPI enforces server-side session authentication via `HttpOnly` cookies (storing only hashed session tokens in PostgreSQL `app.sessions`) and strict role-based access control (`401` unauthenticated `/api/auth/me` ➔ `200` employee login with `HttpOnly` cookie ➔ `403` employee access to `/api/admin/tickets` blocked ➔ `200` `/api/ask` and `/api/my-requests` owner-scoped inquiry persistence in `app.inquiries` with `status="completed"` ➔ `200` admin login and `/api/admin/tickets`).
  - **`oke-search.json` (7 nodes / 3 core HTTP-validation steps):** Enforces a **4-second** HTTP timeout (`4000ms`) to the RAG search service. On timeout or downstream error, it returns a safe `search_unavailable` state so `oke-support` gracefully escalates via Handoff (`HTTP 200`) instead of crashing.
  - **`oke-handoff.json` (30 nodes):** Called by `oke-support` with a **5-second** timeout (`5000ms`), bounded ticket retry (max 2 attempts × 1000ms), and independent fail-safe sinks for operator alerts (`alerts`, 600ms) and Dead-Letter Queue (`dlq`, 600ms). During live VM QA ([`runs/live-integration-qa-20261107.json`](../runs/live-integration-qa-20261107.json)), a missing entry webhook node (`H01 Handoff Webhook`, 29 nodes on VM vs. 30 in repo) caused `Cannot read properties of null (reading 'disabled')` (HTTP 500). Republishing the canonical **30-node** `oke-handoff.json` on the live VM restored `H01` and verified **HTTP 200 OK** across all live retests:
    - Direct C04 smoke & WF-09 idempotency ([`runs/live-integration-qa-20261107T113546Z.json`](../runs/live-integration-qa-20261107T113546Z.json)): `T-2033` and `T-2034` (`duplicate: false` on 1st call, `duplicate: true` on 2nd call with 0 duplicate DB rows, 7/7 checks PASS).
    - Main workflow `oke-support` v18 live escalation ([`runs/support-v18-integration-20261107.json`](../runs/support-v18-integration-20261107.json)): **WF-02b** (`attempt=3`, `reason="max_attempts"`) issued ticket **`T-2035`** (2.188s PASS), and **WF-03** (`reason="low_confidence"`, `sources=[]`) issued ticket **`T-2036`** (3.004s PASS).
  - **`oke-errors.json` (14 nodes):** Dedicated `Error Trigger` workflow (`okeErrorsFlow01`) that isolates unexpected runtime exceptions from expected business faults (`WF-04`/`WF-10`). All three runtime workflows (`okeSupportFlow01`, `okeSearchFlow01`, and `okeHandoffFlow01`) permanently bind `settings.errorWorkflow = "okeErrorsFlow01"` (`0b848e7`), whereas `okeErrorsFlow01` itself sets `settings.errorWorkflow = ""` and never rethrows sink failures, guaranteeing non-recursive fail-safe execution.
- Approved logging policy is successful and failed execution data saved as `all`; all three operational workflows (`okeSupportFlow01`, `okeSearchFlow01`, `okeHandoffFlow01`) permanently bind `settings.errorWorkflow = "okeErrorsFlow01"` (`0b848e7`, so the `oke-errors.json` workflow handles the controlled error path across support, search, and handoff).
- **Checked-in snapshot discrepancy:** `oke-index.json` currently declares `saveDataSuccessExecution: "none"`, `saveDataErrorExecution: "none"`, and `saveManualExecutions: false`; this conflicts with the approved all-execution logging requirement. This task is documentation-only, so the JSON remains unchanged. Before claiming configuration parity, reconcile the index workflow setting in the workflow source/deployment.
- Current JSON settings: `okeSupportFlow01` (`oke-support.json`), `okeSearchFlow01` (`oke-search.json`), and `okeHandoffFlow01` (`oke-handoff.json`): `settings.errorWorkflow = "okeErrorsFlow01"` (`0b848e7`), `saveDataSuccessExecution = "all"`, `saveDataErrorExecution = "all"`; `okeErrorsFlow01` (`oke-errors.json`): `settings.errorWorkflow = ""`, `saveDataSuccessExecution = "all"`, `saveDataErrorExecution = "all"` (no `errorWorkflow` of its own, avoiding recursive hook chaining); `oke-index.json`: as discrepancy above.
- Search is delegated through C03; handoff through C04. Mock branches are explicit test paths and must not be described as live persistence.

## 2. Payload contract catalog


Each `main` edge carries n8n item JSON from its source unless a listed Code node constructs or projects a new object. Branch index 0/1 is the n8n output order, not a business status by itself; descriptions below specify the condition. Fields marked required are required at that boundary; optional fields may be absent or null as stated. Internal envelopes can carry additional context fields from earlier steps; external HTTP payloads are the closed contracts shown here.

### S1 · Support webhook request (required `request_id`, `user`, `question`; optional `channel`, `attempt`, `context`)

`request_id`: nonempty string, max 64; `question`: nonempty string; `user`: employee name; `channel`: string; `attempt`: positive integer; `context`: string. `N02 Normalize input` trims strings, normalizes absent values and accumulates `codes`. Employee identity is validated by real employee lookup or explicit mock adapter; client supplied role/department is not trusted.

```json
{"request_id":"r-001","user":"박서연","question":"VPN 접속 오류가 납니다.","channel":"web","attempt":1,"context":"Windows 11"}
```

### S2 · Normalized support envelope (required `request_id`, `user`, `clean_question`, `context`, `codes`, `employee_lookup`; optional `dept`, `blocked`, `integration_mode`, replay/triage/handoff state)

`N02` adds trimmed `clean_question`, safe `context`, `codes`; `N03 Capture employee` maps data-api `{employees:[...]}` or supported `{items:[...]}` into a matched employee and verified `dept`. The mock adapter is test-only. `N04 Injection rules` adds `blocked` and a reason without treating user claims as authority. `N05 Parse replay` adds replay state; a hit may terminate with the prior safe response, a miss enters triage.

```json
{"request_id":"r-001","user":"박서연","clean_question":"VPN 접속 오류가 납니다.","context":"Windows 11","codes":[],"employee_lookup":"ok","dept":"재무팀","blocked":false}
```

### S3 · Triage result (required `type`, `urgency`, `missing`, `needs_action`; optional `ticket_id`, `reason`)

`N06 Parse triage` parses JSON and validates enums/types; `N07 Route triage` applies deterministic incident override and derives a routing `decision`. `type` is a category string; `urgency` is `normal|high`; `missing` is a string array; `needs_action` is boolean. No triage field grants permissions.

```json
{"type":"network","urgency":"normal","missing":[],"needs_action":false,"ticket_id":null}
```

### S4 · C03 search request (required `request_id`, `query`, `type`, `access_levels`, `top_k`)

`N08 Build search input` derives `query` from cleaned question and context, uses only verified employee department for ACL (`IT팀` → `all,it`; otherwise `all`), sets `top_k:3`, and preserves request correlation. `APPROVED_MIN_SCORE=0.40` is the acceptance threshold for evidence scores. The search backend must apply access-level filtering before ranking.

```json
{"request_id":"r-001","query":"VPN 접속 오류 Windows 11","type":"network","access_levels":["all"],"top_k":3}
```

### S5 · C03 response (required `ok`, `evidence`, `reason`; evidence fields required `doc`, `section`, `score`, `snippet`; optional backend metadata)

`N09 Capture C03` stores HTTP status/body; `N09 Normalize search` validates shape and maps failure to a safe unavailable state. `N11 Join retrieval` requires exactly one search and one ticket branch with matching `request_id`. `N12 Evidence gate` keeps only allowed evidence with score >= 0.40; lower scores cannot authorize an automatic answer. `reason` can identify `no_evidence`, `search_unavailable`, `forbidden` or a successful result.

```json
{"ok":true,"evidence":[{"doc":"remote-work-vpn","section":"연결 점검","score":0.62,"snippet":"인증서와 네트워크 상태를 확인합니다."}],"reason":null}
```

### S6 · Own-ticket lookup and FAQ enrichment

The ticket lookup is conditional on a validated triage `ticket_id`; requester is the validated employee name. Lookup output is normalized to `ticket_lookup:{state,data}` where state distinguishes `skipped`, `ok`, `not_found`, `forbidden`, and unavailable. The FAQ path is exactly two nodes: `N10b FAQ HTTP` requests `GET /faq?q=<clean question>`; `N10b Match FAQ` validates and maps at most the configured matching FAQ entries into evidence rows (`doc:"faq"`). FAQ failure preserves policy evidence only. FAQ is supplementary and never fabricates policy citations.

```json
{"ticket_lookup":{"state":"ok","data":{"ticket_id":"T-1001","status":"open"}},"faq_evidence":[{"doc":"faq","section":"FAQ-003","score":1,"snippet":"VPN 오류 해결 순서"}]}
```

### S7 · Handoff request (required `request_id`, `requester`, `title`, `category`, `priority`, `reason`; optional `evidence_summary`, `ticket_id`)

`N20 Prepare handoff` creates this contract only when required by route; request_id is the idempotency key. `priority` is `normal|high`; summary is masked and bounded. `N20 C04 HTTP` sends the request with the configured team key; response capture retains status/body separately. Mock C04 does not persist a ticket.

```json
{"request_id":"r-001","requester":"박서연","title":"VPN 연결 장애","category":"network","priority":"normal","reason":"근거 부족","evidence_summary":"VPN 접속 오류, 개인식별정보 제거"}
```

### S8 · C04 response / final support response

C04 response requires `ok`, `ticket` (`ticket_id`, `priority`, `duplicate` when present), `reason`, `alerted`, `dlq`. `N20 Map handoff` accepts only validated shapes and `N20 After handoff`/`N21 Already handed off` prevent duplicate escalation. `N22 Finalize P0-3` builds the common result; `N22 Output filter` masks PII before `N23 Respond`.

```json
{"ok":true,"ticket":{"ticket_id":"T-2030","priority":"normal","duplicate":false},"reason":null,"alerted":true,"dlq":false}
```

```json
{"request_id":"r-001","route":"auto_answer","answer":"VPN 인증서와 네트워크 상태를 확인하세요.","sources":[{"doc":"remote-work-vpn","section":"연결 점검"}],"ticket":null,"agents":{"triage":true,"writer":true,"verifier":true},"security":{"blocked":false}}
```

### S9 · Index service request/result

`수동 색인 시작` emits a manual trigger item; `실제 색인 서비스 호출` sends the configured index-service HTTP request. The response verifier requires HTTP 200, `ok:true`, 8 documents, `counts.failed=0`, `counts.rejected=0`; it returns only safe aggregate/document identifiers and status.

```json
{"ok":true,"mode":"upsert","counts":{"indexed":8,"failed":0,"rejected":0},"documents":[{"doc_key":"remote-work-vpn","status":"ok","chunk_count":4}]}
```

### S10 · C03 webhook input/result

Required request: `request_id`, `query`, `type`, `access_levels`, `top_k`; request validator rejects invalid shapes before HTTP. `실제 검색 서비스 호출` returns an HTTP envelope; `검색 응답 검증` maps known 400/401/403 errors to safe C03 responses and malformed/5xx results to 503.

```json
{"request_id":"r-001","query":"VPN 접속","type":"network","access_levels":["all"],"top_k":3}
```

```json
{"ok":true,"evidence":[{"doc":"remote-work-vpn","section":"연결 점검","score":0.62,"snippet":"인증서를 확인합니다."}],"reason":null}
```

### S11 · Handoff store envelopes

`H03 Select Store` chooses exactly one app or practice target and returns readiness/config status. Ticket writes accept the mapped S7 request; a successful app ticket ACK is 201/new or 200/duplicate with `{ticket_id,duplicate}`. Retry is bounded by budget and preserves the first confirmed result. Alert payload requires `workflow,node,message,severity`; optional `ticket_id,event_key`. DLQ requires `request_id,workflow,node,reason,safe_payload`; `execution_ref` optional. Sensitive fields are removed before these writes. `H10 Build Result` returns `{ok,ticket,reason,alerted,dlq}`.

```json
{"workflow":"oke-handoff","node":"H06 Keep Ticket","message":"담당자 이관 티켓이 접수되었습니다.","severity":"normal","ticket_id":"T-2030","event_key":"r-001:ticket-created"}
```

```json
{"request_id":"r-001","workflow":"oke-handoff","node":"H08 Check Alert","reason":"alert_store_failed","safe_payload":{"stage":"alert","priority":"normal"},"execution_ref":"exec-42"}
```

### S12 · Controlled error workflow event/store payload

n8n `settings.errorWorkflow` on `okeSupportFlow01` (`oke-support.json`), `okeSearchFlow01` (`oke-search.json`), and `okeHandoffFlow01` (`oke-handoff.json`) is permanently bound to `okeErrorsFlow01` (`0b848e7`). Error Trigger input carries the n8n parent workflow/execution/trigger objects; `E02 Safe Error Context` validates parent identity, allowlisted workflow names and extracts only safe `source_workflow`, `source_node`, `execution_ref`, `error_kind`. Self-trigger or untrusted parent is skipped. Alert and DLQ writes are independent; sink failure is not rethrown and no parent HTTP response is fabricated.

```json
{"workflow":{"name":"oke-support","id":"support-flow"},"execution":{"id":"exec-42","error":{"name":"NodeApiError","message":"redacted"}},"trigger":{"error":{"message":"redacted"}}}
```

```json
{"workflow":"oke-errors","outcome":"success","request_id":null,"execution_ref":"exec-42","source_workflow":"oke-support","source_node":"N13 Writer Agent","error_kind":"node_error","alerted":true,"dlq":true}
```

### S13 · AI model connector input

AI model connections carry LangChain model configuration, not the business JSON envelope. `N06 Triage model`, `N13 Writer model`, `N14 Verifier model` feed only their corresponding Agent node. Credentials are n8n-managed and never part of item data.

```json
{"model":"gpt-4.1-mini","credential":"n8n credential reference"}
```

## 3. Edge-by-edge connection contract

The following inventory is generated from every `connections` entry in the five source JSON files. Every edge names its source and destination exactly, its n8n connection type/output index, the payload schema reference, and the transformation/branch semantics. Schema references resolve to §2; examples are included there.

### oke-support.json

| Source node | Connection | Destination node | Payload schema | Required/optional, transformation and branch |
|---|---|---|---|---|
| `N01 Support webhook` | `main[0]` | `N02 Normalize input` | S1 | Webhook body enters normalization. |
| `N02 Normalize input` | `main[0]` | `N03 Employee mode` | S2 | Input is normalized or employee response is captured; verified employee attributes are added. |
| `N03 Validate employee MOCK` | `main[0]` | `N04 Injection rules` | S2 | Test-only employee fixture; production path uses HTTP adapter. |
| `N04 Injection rules` | `main[0]` | `N05 Replay MOCK` | S2 | Adds blocked/reason; next replay stage can terminate blocked request. |
| `N05 Triage gate` | `main[0]` | `N05 Triage mode` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N05 Triage gate` | `main[1]` | `N22 Finalize P0-3` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N05 Triage mode` | `main[0]` | `N06 Triage MOCK` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N05 Triage mode` | `main[1]` | `N06 Triage Agent` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N06 Triage MOCK` | `main[0]` | `N06 Parse triage` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N06 Triage Agent` | `main[0]` | `N06 Parse triage` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N06 Triage model` | `ai_languageModel[0]` | `N06 Triage Agent` | S13 | Model connector config only; no user payload crosses this edge. |
| `N06 Parse triage` | `main[0]` | `N07 Route triage` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N07 Route triage` | `main[0]` | `N07 Route urgent` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N20 Prepare handoff` | `main[0]` | `N20 Handoff gate` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N20 Handoff gate` | `main[0]` | `N20 Handoff mode` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N20 Handoff gate` | `main[1]` | `N22 Finalize P0-3` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N20 Mock C04` | `main[0]` | `N20 Map handoff` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N20 Map handoff` | `main[0]` | `N20 After handoff` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N22 Finalize P0-3` | `main[0]` | `N22 Output filter` | S8 | Final response envelope is PII-filtered before webhook response. |
| `N08 Build search input` | `main[0]` | `N09 Search mode` | S2/S4 | Creates S4 search_request; branch 0 starts search, sibling branch starts own-ticket lookup. |
| `N08 Build search input` | `main[0]` | `N10 Build ticket lookup` | S2/S4 | Creates S4 search_request; branch 0 starts search, sibling branch starts own-ticket lookup. |
| `N09 Mock C03` | `main[0]` | `N09 Normalize search` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N09 Normalize search` | `main[0]` | `N11 Collect retrieval` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N10 Build ticket lookup` | `main[0]` | `N10 Ticket mode` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N10 Mock ticket` | `main[0]` | `N10 Normalize ticket` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N10 Normalize ticket` | `main[0]` | `N10b FAQ HTTP` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N11 Collect retrieval` | `main[0]` | `N11 Join retrieval` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N11 Join retrieval` | `main[0]` | `N12 Evidence gate` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N12 Evidence gate` | `main[0]` | `N12 Route evidence` | S2/S5 | Evidence gate retains rows with score >= 0.40; branch 0 is answerable evidence, branch 1 is already handed off/insufficient evidence. |
| `N12 Route evidence` | `main[0]` | `N13 Prepare writer` | S2/S5 | Evidence gate retains rows with score >= 0.40; branch 0 is answerable evidence, branch 1 is already handed off/insufficient evidence. |
| `N12 Route evidence` | `main[1]` | `N21 Already handed off` | S2/S5 | Evidence gate retains rows with score >= 0.40; branch 0 is answerable evidence, branch 1 is already handed off/insufficient evidence. |
| `N13 Prepare writer` | `main[0]` | `N13 Writer mode` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N13 Writer mode` | `main[0]` | `N13 Writer MOCK` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N13 Writer mode` | `main[1]` | `N13 Writer Agent` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N13 Writer MOCK` | `main[0]` | `N13 Parse writer` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N13 Writer Agent` | `main[0]` | `N13 Parse writer` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N13 Writer model` | `ai_languageModel[0]` | `N13 Writer Agent` | S13 | Model connector config only; no user payload crosses this edge. |
| `N13 Parse writer` | `main[0]` | `N13 Writer valid` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N13 Writer valid` | `main[0]` | `N14 Prepare verifier` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N13 Writer valid` | `main[1]` | `N21 Already handed off` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N14 Prepare verifier` | `main[0]` | `N14 Verifier mode` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N14 Verifier mode` | `main[0]` | `N14 Verifier MOCK` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N14 Verifier mode` | `main[1]` | `N14 Verifier Agent` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N14 Verifier MOCK` | `main[0]` | `N14 Parse verifier` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N14 Verifier Agent` | `main[0]` | `N14 Parse verifier` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N14 Verifier model` | `ai_languageModel[0]` | `N14 Verifier Agent` | S13 | Model connector config only; no user payload crosses this edge. |
| `N14 Parse verifier` | `main[0]` | `N15 Decide answer` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N15 Decide answer` | `main[0]` | `N15 Route answer` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N15 Route answer` | `main[0]` | `N22 Finalize P0-3` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N15 Route answer` | `main[1]` | `N21 Already handed off` | S2/S5 | Writer/verifier JSON is parsed and validated; branch 0 continues a valid answer, branch 1 escalates or preserves prior handoff. |
| `N22 Output filter` | `main[0]` | `N23 Respond` | S8 | Final response envelope is PII-filtered before webhook response. |
| `N07 Route urgent` | `main[0]` | `N20 Prepare handoff` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N07 Route urgent` | `main[1]` | `N08 Build search input` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N20 After handoff` | `main[0]` | `N08 Build search input` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N20 After handoff` | `main[1]` | `N22 Finalize P0-3` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N21 Already handed off` | `main[0]` | `N22 Finalize P0-3` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N21 Already handed off` | `main[1]` | `N20 Prepare handoff` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N05 Replay MOCK` | `main[0]` | `N05 Parse replay` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N05 Parse replay` | `main[0]` | `N05 Route replay` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N05 Route replay` | `main[0]` | `N22 Finalize P0-3` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N05 Route replay` | `main[1]` | `N05 Triage gate` | S2/S3 | Carry validated context; parse triage JSON and branch by replay/triage/route decision. |
| `N03 Employee mode` | `main[0]` | `N03 Get employees HTTP` | S2 | Input is normalized or employee response is captured; verified employee attributes are added. |
| `N03 Employee mode` | `main[1]` | `N03 Validate employee MOCK` | S2 | Input is normalized or employee response is captured; verified employee attributes are added. |
| `N03 Get employees HTTP` | `main[0]` | `N03 Capture employee` | S2 | Input is normalized or employee response is captured; verified employee attributes are added. |
| `N03 Capture employee` | `main[0]` | `N04 Injection rules` | S2 | Input is normalized or employee response is captured; verified employee attributes are added. |
| `N09 Search mode` | `main[0]` | `N09 C03 HTTP` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N09 Search mode` | `main[1]` | `N09 Mock C03` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N09 C03 HTTP` | `main[0]` | `N09 Capture C03` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N09 Capture C03` | `main[0]` | `N09 Normalize search` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N10 Ticket mode` | `main[0]` | `N10 Own ticket HTTP` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N10 Ticket mode` | `main[1]` | `N10 Mock ticket` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N10 Own ticket HTTP` | `main[0]` | `N10 Capture ticket` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N10 Capture ticket` | `main[0]` | `N10 Normalize ticket` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N20 Handoff mode` | `main[0]` | `N20 C04 HTTP` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N20 Handoff mode` | `main[1]` | `N20 Mock C04` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N20 C04 HTTP` | `main[0]` | `N20 Capture C04` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N20 Capture C04` | `main[0]` | `N20 Map handoff` | S2/S7/S8 | Maps C04 result; branch depends on handoff eligibility/success and existing handoff state. |
| `N10b FAQ HTTP` | `main[0]` | `N10b Match FAQ` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |
| `N10b Match FAQ` | `main[0]` | `N11 Collect retrieval` | S4/S5/S6 | Captures and normalizes search/ticket/FAQ results; adds one typed retrieval branch. FAQ enriches only eligible normal pending requests. |

### oke-index.json

| Source node | Connection | Destination node | Payload schema | Required/optional, transformation and branch |
|---|---|---|---|---|
| `수동 색인 시작` | `main[0]` | `실제 색인 서비스 호출` | S9 | Manual invocation passes to configured index HTTP call and result validation; validator emits safe aggregate status. |
| `실제 색인 서비스 호출` | `main[0]` | `색인 결과 검증` | S9 | Manual invocation passes to configured index HTTP call and result validation; validator emits safe aggregate status. |

### oke-search.json

| Source node | Connection | Destination node | Payload schema | Required/optional, transformation and branch |
|---|---|---|---|---|
| `검색 요청 수신` | `main[0]` | `요청 형식 확인` | S10 | Validates C03 request; branch 0 is valid HTTP search, branch 1 is rejection; capture/validator maps HTTP envelope to safe C03 response. |
| `요청 형식 확인` | `main[0]` | `유효한 C03 요청` | S10 | Validates C03 request; branch 0 is valid HTTP search, branch 1 is rejection; capture/validator maps HTTP envelope to safe C03 response. |
| `실제 검색 서비스 호출` | `main[0]` | `검색 응답 검증` | S10 | Validates C03 request; branch 0 is valid HTTP search, branch 1 is rejection; capture/validator maps HTTP envelope to safe C03 response. |
| `검색 응답 검증` | `main[0]` | `C03 응답 반환` | S10 | Validates C03 request; branch 0 is valid HTTP search, branch 1 is rejection; capture/validator maps HTTP envelope to safe C03 response. |
| `입력 거절` | `main[0]` | `C03 응답 반환` | S10 | Validates C03 request; branch 0 is valid HTTP search, branch 1 is rejection; capture/validator maps HTTP envelope to safe C03 response. |
| `유효한 C03 요청` | `main[0]` | `실제 검색 서비스 호출` | S10 | Validates C03 request; branch 0 is valid HTTP search, branch 1 is rejection; capture/validator maps HTTP envelope to safe C03 response. |
| `유효한 C03 요청` | `main[1]` | `입력 거절` | S10 | Validates C03 request; branch 0 is valid HTTP search, branch 1 is rejection; capture/validator maps HTTP envelope to safe C03 response. |

### oke-handoff.json

| Source node | Connection | Destination node | Payload schema | Required/optional, transformation and branch |
|---|---|---|---|---|
| `H01 Handoff Webhook` | `main[0]` | `H02 Validate and Map` | S7 | Validates and maps required C04 request; invalid branch responds immediately. |
| `H02 Validate and Map` | `main[0]` | `H02a Valid Input` | S7 | Validates and maps required C04 request; invalid branch responds immediately. |
| `H02a Valid Input` | `main[0]` | `H03 Select Store` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H02a Valid Input` | `main[1]` | `H11 Respond` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H03 Select Store` | `main[0]` | `H03a Store Ready` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H03a Store Ready` | `main[0]` | `H03b App Ticket Store` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H03a Store Ready` | `main[1]` | `H11 Respond` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H03b App Ticket Store` | `main[0]` | `H04 Create Ticket App` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H03b App Ticket Store` | `main[1]` | `H04 Create Ticket Practice` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H04 Create Ticket Practice` | `main[0]` | `H05 Retry Gate` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H04 Create Ticket App` | `main[0]` | `H05 Retry Gate` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H05 Retry Gate` | `main[0]` | `H05a Retry Allowed` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H05a Retry Allowed` | `main[0]` | `H05 Wait` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H05a Retry Allowed` | `main[1]` | `H05 Recheck Budget` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H05 Wait` | `main[0]` | `H05 Recheck Budget` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H05b App Retry Store` | `main[0]` | `H04 Retry Ticket App` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H05b App Retry Store` | `main[1]` | `H04 Retry Ticket Practice` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H04 Retry Ticket Practice` | `main[0]` | `H06 Keep Ticket` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H04 Retry Ticket App` | `main[0]` | `H06 Keep Ticket` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H05 Restore First Result` | `main[0]` | `H06 Keep Ticket` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H06 Keep Ticket` | `main[0]` | `H07 Failure Context` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H07 Failure Context` | `main[0]` | `H08a App Alert Store` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H08a App Alert Store` | `main[0]` | `H08 Store Alert App` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H08a App Alert Store` | `main[1]` | `H08 Store Alert Practice` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H08 Store Alert App` | `main[0]` | `H08 Check Alert` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H08 Store Alert Practice` | `main[0]` | `H08 Check Alert` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H08 Check Alert` | `main[0]` | `H09a Needs DLQ` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H09a Needs DLQ` | `main[0]` | `H09b App DLQ Store` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H09a Needs DLQ` | `main[1]` | `H10 Build Result` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H09b App DLQ Store` | `main[0]` | `H09 Store DLQ App` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H09b App DLQ Store` | `main[1]` | `H09 Store DLQ Practice` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H09 Store DLQ App` | `main[0]` | `H09 Check DLQ` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H09 Store DLQ Practice` | `main[0]` | `H09 Check DLQ` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H09 Check DLQ` | `main[0]` | `H10 Build Result` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H10 Build Result` | `main[0]` | `H11 Respond` | S11 | Writes/checks safe alert or DLQ receipt; branch selects exactly one app/practice adapter or skips unnecessary DLQ. |
| `H05 Recheck Budget` | `main[0]` | `H05c Retry Still Allowed` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H05c Retry Still Allowed` | `main[0]` | `H05b App Retry Store` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |
| `H05c Retry Still Allowed` | `main[1]` | `H05 Restore First Result` | S7/S11 | Selects store, writes ticket, retries only within deadline and preserves first confirmed ACK; response carries ticket receipt. |

### oke-errors.json

| Source node | Connection | Destination node | Payload schema | Required/optional, transformation and branch |
|---|---|---|---|---|
| `E01 Error Trigger` | `main[0]` | `E02 Safe Error Context` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E02 Safe Error Context` | `main[0]` | `E02a External Parent` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E02a External Parent` | `main[0]` | `E02 Select Store` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E02a External Parent` | `main[1]` | `E05 Outcome` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E02 Select Store` | `main[0]` | `E02b Store Ready` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E02b Store Ready` | `main[0]` | `E03a App Alert Store` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E02b Store Ready` | `main[1]` | `E05 Outcome` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E03a App Alert Store` | `main[0]` | `E03 Store Alert App` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E03a App Alert Store` | `main[1]` | `E03 Store Alert Practice` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E03 Store Alert App` | `main[0]` | `E03 Check Alert` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E03 Store Alert Practice` | `main[0]` | `E03 Check Alert` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E03 Check Alert` | `main[0]` | `E04a App DLQ Store` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E04a App DLQ Store` | `main[0]` | `E04 Store DLQ App` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E04a App DLQ Store` | `main[1]` | `E04 Store DLQ Practice` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E04 Store DLQ App` | `main[0]` | `E04 Check DLQ` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E04 Store DLQ Practice` | `main[0]` | `E04 Check DLQ` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |
| `E04 Check DLQ` | `main[0]` | `E05 Outcome` | S12 | Extracts safe error context; branch gates parent allowlist/store readiness. Alert and DLQ sinks run independently and outcome is internal only. |

## 4. Exact node-name inventory

Names below are copied verbatim from the `nodes[].name` values in each source JSON. This is the alignment source of truth; names are not the older conceptual N01…N23 plan labels.

### oke-support.json

Node count: **63**

`N01 Support webhook` | `N02 Normalize input` | `N03 Validate employee MOCK` | `N04 Injection rules` | `N05 Triage gate` | `N05 Triage mode` | `N06 Triage MOCK` | `N06 Triage Agent` | `N06 Triage model` | `N06 Parse triage` | `N07 Route triage` | `N08 Build search input` | `N09 Mock C03` | `N09 Normalize search` | `N10 Build ticket lookup` | `N10 Mock ticket` | `N10 Normalize ticket` | `N11 Collect retrieval` | `N11 Join retrieval` | `N12 Evidence gate` | `N20 Prepare handoff` | `N20 Handoff gate` | `N20 Mock C04` | `N20 Map handoff` | `N22 Finalize P0-3` | `N23 Respond` | `N13 Prepare writer` | `N12 Route evidence` | `N13 Writer mode` | `N13 Writer MOCK` | `N13 Writer Agent` | `N13 Writer model` | `N13 Parse writer` | `N13 Writer valid` | `N14 Prepare verifier` | `N14 Verifier mode` | `N14 Verifier MOCK` | `N14 Verifier Agent` | `N14 Verifier model` | `N14 Parse verifier` | `N15 Decide answer` | `N15 Route answer` | `N22 Output filter` | `N07 Route urgent` | `N20 After handoff` | `N21 Already handed off` | `N05 Replay MOCK` | `N05 Parse replay` | `N05 Route replay` | `N03 Employee mode` | `N03 Get employees HTTP` | `N03 Capture employee` | `N09 Search mode` | `N09 C03 HTTP` | `N09 Capture C03` | `N10 Ticket mode` | `N10 Own ticket HTTP` | `N10 Capture ticket` | `N20 Handoff mode` | `N20 C04 HTTP` | `N20 Capture C04` | `N10b FAQ HTTP` | `N10b Match FAQ`

### oke-index.json

Node count: **3**

`수동 색인 시작` | `실제 색인 서비스 호출` | `색인 결과 검증`

### oke-search.json

Node count: **7**

`검색 요청 수신` | `요청 형식 확인` | `유효한 C03 요청` | `C03 응답 반환` | `실제 검색 서비스 호출` | `검색 응답 검증` | `입력 거절`

### oke-handoff.json

Node count: **30**

`H01 Handoff Webhook` | `H02 Validate and Map` | `H02a Valid Input` | `H03 Select Store` | `H03a Store Ready` | `H03b App Ticket Store` | `H04 Create Ticket Practice` | `H04 Create Ticket App` | `H05 Retry Gate` | `H05a Retry Allowed` | `H05 Wait` | `H05 Recheck Budget` | `H05c Retry Still Allowed` | `H05b App Retry Store` | `H04 Retry Ticket Practice` | `H04 Retry Ticket App` | `H05 Restore First Result` | `H06 Keep Ticket` | `H07 Failure Context` | `H08a App Alert Store` | `H08 Store Alert Practice` | `H08 Store Alert App` | `H08 Check Alert` | `H09a Needs DLQ` | `H09b App DLQ Store` | `H09 Store DLQ Practice` | `H09 Store DLQ App` | `H09 Check DLQ` | `H10 Build Result` | `H11 Respond`

### oke-errors.json

Node count: **14**

`E01 Error Trigger` | `E02 Safe Error Context` | `E02a External Parent` | `E02 Select Store` | `E02b Store Ready` | `E03a App Alert Store` | `E03 Store Alert App` | `E03 Store Alert Practice` | `E03 Check Alert` | `E04a App DLQ Store` | `E04 Store DLQ App` | `E04 Store DLQ Practice` | `E04 Check DLQ` | `E05 Outcome`

## 5. Operational interpretation

- `oke-support.json` is the main orchestration: normalize/validate, employee lookup, injection/replay gates, triage, optional early handoff, C03 and own-ticket retrieval, FAQ enrichment, evidence gate, writer/verifier, final response filter.
- `oke-index.json` is a manual trigger → index service request → strict result validation workflow.
- `oke-search.json` validates the C03 contract, invokes the search service, validates the response, and returns either a safe result or rejection.
- `oke-handoff.json` validates C04, selects one store, creates an idempotent ticket with bounded retry, records alert and conditionally DLQ receipts, then responds.
- `oke-errors.json` receives controlled n8n error events, derives safe context, checks the parent and storage readiness, then attempts alert and DLQ persistence without replacing the parent HTTP response.
- Any evidence of VM activation, external service availability, or a live ticket receipt belongs in execution evidence, not inferred from workflow JSON alone.
