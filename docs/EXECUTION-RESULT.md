# 워크플로우 실행 결과 · DAY 80–82 · 2026-11-05 ~ 2026-11-07

> 이 문서는 VM/로컬 관측과 미실행 범위를 함께 기록한다. HTTP 응답·Mock·로컬 검사만으로 DB 영속 저장이나 종단 간 성공을 추정하지 않는다. 민감값은 포함하지 않는다.

## 1. 실행 및 환경 관측

| 시각/버전 경계 | 확인 항목 | 실제 결과 | 범위와 한계 |
|---|---|---|---|
| 2026-11-05 관제 기록 | 웹 터미널 파일 전송 | 8,192 byte 파일 put/get 후 내용 일치 | 전송 무결성만 확인; 배포/서비스 기능 검증과 별개 |
| VM 통합 관측, main `952f704` | PostgreSQL·마이그레이션 | PostgreSQL healthy, Alembic `0005`; role catalog 조회 | DB readiness와 revision 관측. 색인·검색용 로그인 권한의 실제 연결/최소 권한 검증 결과는 별도 확인 필요 |
| 동일 관측 | 데이터 행 수·운영 모드 | `rag.documents=0`, `rag.chunks=0`, `app.tickets=0`; `practice` | 해당 시점 관측값. `app` 모드 영속 저장 결과가 아니며 기존 볼륨은 유지 |
| workflow 본체 실행 ID `manual-38042b9550d14ce3b3b447a1bdbef2c8` | 질문 `비밀번호 초기화 절차를 알려주세요` | HTTP 200; 응답 `reason=search_unavailable`, `route=담당자 이관`, ticket `T-2001`, `sources=[]` | 이관 응답이 사용자에게 반환된 사실만 확인. practice 경로의 응답이며 C05 DB 기록/영속성 증거가 아님. 실행은 이후 최신 main `952f704` 재배포/검증보다 앞선 버전 경계이며 최신본에서 재실행한 결과로 취급하지 않음 |
| 후속 배포 후, VM main `952f704` | C03 검색 요청 | HTTP 000, connection reset | 응답 본문·근거 결과 없음. 정상 검색으로 집계하지 않음 |
| 후속 배포 후, VM main `952f704` | 서비스/스모크 | RAG 검색 컨테이너 0개, 8765 listener 없음; deploy 전체 스모크 미완료 | n8n 재시작과 주요 workflow 활성은 확인했으나 deploy 스모크 PASS는 아님 |

## 2. 로컬 정적·회귀 검사

| 검사 | 결과 | 적용 범위 |
|---|---|---|
| `python3 -m json.tool` — root support/search JSON | 통과 | JSON 문법만 확인 |
| `git diff --check` | 통과 | 공백/patch 오류 점검 |
| VM 배포 스크립트 `bash -n` | 통과 | shell 문법. VM 서비스 정상성은 확인하지 않음 |
| 원민 `node --test develop/wonmin/tests/*.test.mjs` | 일부 실패 | Mock startup timeout과 외부 C05 응답 계약 오류가 발생. 성공 건수/실패율을 공식 공통 통과 수로 환산하지 않음 |
| 유빈 `6780432`의 기록된 Fake 경계 검사 | Python 190개·JavaScript 3개 통과 기록 | 해당 커밋의 Fake/Mock 범위. 이 문서 작성 중 재실행하지 않았고 PostgreSQL/n8n/VM 실제 검색 결과가 아님 |

## 3. 시나리오별 실행 판정

| 경로 | 현재 관측 | 판정 |
|---|---|---|
| 본체 정상 형식 요청 | 위 실행에서 HTTP 200 응답이지만 C03 `search_unavailable` 후 이관 | HTTP 응답은 관측. 정상 검색·근거 답변 시연은 미확인 |
| 검색 C03 | 최신 배포 뒤 HTTP 000/reset; 검색 서비스 없음 | 실패/미완료 |
| 이관 C04 | `manual-38042b9550d14ce3b3b447a1bdbef2c8`에서 T-2001 응답 | 이관 응답 관측. 실제 저장 API·DB 영속성·재시작 보존은 미증명 |
| practice/app 저장 모드 | VM practice, app tickets 관측 0 | app 저장 검증 미실행 |
| 입력 400·주입 차단 | 해당 8교시 VM HTTP/실행ID 근거 없음 | VM 시연 미확인 |
| WF-08/WF-13 본인·타인 조회 | 동일 VM의 본인 성공/타인 403 근거 없음 | 미실행/미확인 |
| 공식 `flow.py test cases/common.json` | 공식 키트·실행 결과 미확인 | 공통 14개는 미실측. `0/14`는 이전 템플릿 문자열일 뿐 결과값이 아님 |
| 일반/IT 권한별 실제 문서 검색 | DB 문서/청크 0/0, 권한 근거·서비스 경로 미완성 | 미실행. 권한 위반 0건이나 hit@3 수치를 주장하지 않음 |

## 4. 제출·시연 요구와 피드백 추적

공식 8교시 체크리스트의 7개 항목은 WORKFLOW-DESIGN 1~4절, RAG 설계와 청크 실측, 팀 VM 라이브 시연, 400·주입 차단, WF-08/WF-13, 공통 14개 실행 결과, DAY80 기록 및 강사 피드백이다. WORKFLOW-DESIGN 1~4절은 저장소에 있으나 나머지 실행/실측 항목은 위 증거로 미완료 또는 미확인이다. 공식 표의 미체크 양식과 본 실행 결과 판정은 구분한다.

사용자가 전달한 7교시 피드백은 “실문서 DB 검색 한 경로”, “실제 색인 수·청크 길이·권한별 결과”, “`security-incident` 권한 및 인증 계약 정렬”, “동일 VM의 정상 및 이관 근거”를 요구한다. 현재 색인 0/0, C03 HTTP 000/reset, 이관은 과거 practice 응답만 확인됐으므로 피드백 요구를 완료하지 못했다. 본 기록은 강사 승인·검토를 뜻하지 않는다.

## 5. 알려진 한계와 다음 검증 순서

1. Python search listener가 없고 n8n과의 네트워크/URL 경로가 정렬되지 않았다. root URL `/search`와 서비스 수신 경로 `/webhook/oke-search`가 일치하지 않는 관측이 있다. 검색 프로세스의 실제 실행 정의·도달 주소·접근 통제를 확정한 뒤 동일 VM에서 HTTP 응답/본문을 확인한다.
2. 실제 규정 권한 근거와 검색용 환경 설정이 검증되기 전에는 색인하지 않는다. 승인된 실제 문서로 색인 후 문서 수·청크 수·청크 길이 최소/중앙/최대와 일반/IT 결과를 기록한다.
3. `practice`의 응답과 `app` 모드 C05 영속 저장은 별도다. 앱 티켓/알림/DLQ API의 저장·ACK·멱등/재시작 검증 전에는 T-2001 응답을 DB 기록으로 해석하지 않는다.
4. 이후 동일 VM 버전에서 정상 답변과 이관의 실행ID·요청·HTTP·본문·근거를 각각 저장하고, 입력400·주입 차단·WF-08/WF-13 및 공식 common 14개를 실제 도구로 실행한다. 미실행·실패를 별도 행으로 남긴다.

## 6. 버전 및 근거

- main 통합 기준: `952f704` (기존 통합 및 선택 반영 커밋 `36e01ce`, `eb3e8a4`, `7b9b383`, `e03833b`, `952f704`). 팀별 구현은 `develop/jihye/Doc/IMP-PLAN.md`, `develop/dahyeok/Doc/IMP-PLAN.md`, `develop/yubeen/Doc/IMP-PLAN.md`, `develop/wonmin/Doc/`의 P1 결과/HANDOFF를 참조한다.
- 실제 반영 커밋과 문서 정리 커밋은 구분한다. 이 보고서 갱신은 코드/워크플로우 변경이나 VM 재배포가 아니다.
- 기록에 없는 workflow execution ID, 처리시간, 청크 분포, hit@3/MRR, 비용, LLM 호출 수는 미기록/미측정으로 둔다.

## 7. 후속 VM 통합 실행 · main `3e0f701`

아래 결과는 위 952f704 시점 기록 이후 `unified-vm-finish-2`로 수행한 별도 실행이다. 초기 관측의 0/0·`practice`·HTTP 000은 그 시점의 역사적 상태로 보존한다.

| 버전/실행 | 실제 결과 | 판정/한계 |
|---|---|---|
| main/VM `3e0f701` | VM `origin/main` fast-forward; `SERVICE_MODE=app`를 backend/n8n/runners에서 선별 조회. 기존 PG/n8n named volume과 encryption key 유지 | `develop/jihye/deploy/.env.backend`, RAG `search.env`/`index.env`, compose private env mode 600. 비밀값은 출력·문서·Git에 포함하지 않음 |
| official employee seed | `seed-employees` HTTP/source adapter 경로 실행, `created=6`; DB employees=6, users=0 | data-api 고정 내부 origin 무인증 계약을 실측했고 원본 6명 검증 후 기존 seed service 사용. 계정/admin 생성은 별개 |
| RAG preflight/index | manifest source hash 8개 검증; 7=`all`, 1=`it`; index HTTP 200, `ok=true`, indexed=8, rejected=0, failed=0, 33 chunks | DB `rag.documents/chunks=8/33`. indexer 반환 mode string은 `postgres_unverified`였으나 별도 DB 쿼리로 rows/permissions를 검증했다. threshold/청크 길이 분포는 미측정 |
| direct search, request `vm-search-general-1` | HTTP 200, `ok=true`, evidence=3; 문서 key는 `password-policy` | 실제 OpenAI embedding과 read-only scoped DB search. 답변 품질/threshold 통과 판정은 아님 |
| direct search, request `vm-search-it-1` | HTTP 200, evidence=3; `security-incident` 포함. `all` 범위 검색은 IT-only key를 반환하지 않았음 | source fallback `security-incident=it`의 권한 필터 결과를 실측. 사용자별 IAM 연동은 아직 없음 |
| n8n `/webhook/oke-search` | HTTP 200, evidence=3; 일반 정책 문서 검색 | n8n Team credential → search 전용 `X-Team-Key` → `rag-search` 경로 실호출. header 종류가 같다는 이유로 credential을 공유하지 않음 |
| n8n `/webhook/oke-handoff`, correlation request `vm-fin2-handoff-20261105-01` | 첫 요청 HTTP 200 `T-2001`/duplicate=false/alerted=true/DLQ=false. 동일 request key 재호출 HTTP 200 같은 `T-2001`/duplicate=true/alerted=true/DLQ=false | app C04와 alert 실제 저장. DB에는 test key ticket 1건, 해당 event key alert 1건 |
| n8n `/webhook/oke-support`, correlation request `vm-fin2-support-20261105-01` | 일반 비밀번호 초기화 질문. HTTP 200, route=`담당자 이관`, reason=`low_confidence`, ticket=`T-2002`, sources=[] | 정상 사용 경로의 triage 후 보수 이관과 실제 C04 저장. 응답 근거가 없으므로 자동 답변/검색 품질 PASS로 취급하지 않음 |
| 입력/주입 | 빈 질문은 HTTP 400 `question_required`. 주입 시도는 HTTP 200, route=`차단`, `security.reason=prompt_injection`, ticket=null | 이 root workflow의 계약은 입력 검증 오류 400, 정책 차단 응답 200이다. 주입 차단을 HTTP 400이라고 쓰지 않음 |
| FE/API 내부 smoke | VM localhost `/login` HTTP 200, unauthenticated `/api/auth/me` HTTP 401 | FE 컨테이너 build/health와 proxy 경로 확인. 로그인 계정이 없어 인증 성공/로그아웃/비밀번호 변경은 미실행 |
| PostgreSQL restart persistence | PostgreSQL container restart 후 healthy; backend `/health/ready` HTTP 200, FE `/login` HTTP 200. DB employees/users/tickets/alerts/DLQ=`6/0/2/3/1`; RAG documents/chunks=`8/33`; `T-2001` 유지 | 기존 PG volume을 사용한 restart 보존 실측. 기존 C05 데이터와 신규 test C04 저장을 구분함 |
| resources | RAM total 2646 MiB, available 1344 MiB, swap used 343 MiB; disk free 41 GiB; n8n/backend/FE/RAG/search/index/PG OOM=false | 주요 컨테이너 OOM 없음. 자원 snapshot 시각 기준 |
| 외부 URL | HTTPS `/` 502, `:5678/healthz` 200, `:3000/login` timeout; VM host 80/443 listener/proxy config 없음 | FE 외부 제공 미완료. 내부 `:3000` health는 공개 연결 증거가 아님. 기존 ingress 설정 변경 필요 |

### Workflow/tool checks

- Latest root workflows `oke-support`, `oke-search`, `oke-handoff`, `oke-errors` were imported by their stable IDs and published; `oke-index` remains inactive/manual. Four typed HTTP Header credentials were imported (team webhook, search, index, backend `X-Api-Key`); the existing OpenAI credential was reused. Temporary plaintext credential import staging was removed after import; private VM env files remain mode 600.
- VM course tool: `/home/toor/aio-01d4-stu/Last3Mon/79/tools/flow.py`, SHA-256 `6b0059cb3af135b08954559d0e6b757991fc2fc42a0624244d129e618284fb6f`. Its `test` accepts `cases`/`request`/`expect.status`, but its HTTP helper sends only `Content-Type` and cannot send the required root `X-Team-Key`. Therefore the root custom team/handoff suites were not run through that tool. No official common-14 JSON case file was found in the course tree.
- `flow.py check` on root source reports course-specific credential-ID errors (`openAiCourse0001` expected, source placeholders supplied) for support/search/handoff/errors; search/handoff also produce node-version warnings. This static course check does not reflect VM runtime credential mapping. Live n8n C03/C04 calls above are the runtime evidence; no case expectations were changed.
- The course `flow.py` check is distinct from `develop/dahyeok/tools/flow.py`, which reports itself as a Mock-only checker. Neither is evidence of the official common-14 suite passing.

### Still pending

- Controller answer for first administrator (`김민지/minji.admin` or `정우성/woosung.admin`) remains pending. No admin was bootstrapped; users=0. Thus FE successful login, forced password change, logout/relogin, own/other 403, and admin views are not tested.
- External ingress must route `https://aio-t1.isitsoft.kr/` to FE. No local VM proxy was present; no extra public port was opened.
- The support execution safely handed off with empty final sources after low confidence. Direct C03 search succeeded, but RAG threshold, measured quality, and automatic answer acceptance remain unapproved/unmeasured. No accuracy or hit-rate PASS is claimed.
- Official common-14 suite was not available in the course tree; test runner authentication limitation blocks running the custom header-protected cases as-is. Keep that separate from successful targeted HTTP checks and the two local suites (`jihye` 18/18; `yubeen` 34/34).
- The current request IDs above are correlation IDs, not captured n8n execution IDs. Do not claim or infer execution IDs, LLM call counts, cost, p95, or chunk length distribution.

## 8. OKE runtime cleanup and project rename · 2026-11-05

This is a later runtime observation after the `3e0f701` integration snapshot above. GitHub `main` was advanced by runtime implementation commit `c1a4c8b` (`ops(vm): rename unified compose project to oke`), pushed, and the VM fast-forwarded to it before cutover. Later docs-only updates were also pushed and fast-forwarded without restarting services. The historical `3e0f701` results above remain the earlier baseline.

| Check | Result | Evidence / limit |
|---|---|---|
| Backup and rollback | Verified pre-switch backup at `/home/toor/backups/oke-runtime-cleanup-20261105-final`; directory mode 700, private files mode 600. PostgreSQL dump 1,336,239 bytes; n8n data copy 7.87 MB / 10 files; checksums validated | Full PostgreSQL dump, n8n volume copy, existing private env/admin handoff copies, compose and mount metadata. The copy was made before stopping old services. Two incomplete preflight backup directories were retained but are not rollback sources |
| Compose/config | `docker compose ... -p oke config --quiet` passed before and after startup | Project name changed; app mode is explicit/default `app`; SearXNG `optional-search`; RAG index remains `indexing` profile |
| Runtime | Project `oke` has n8n, runners, sandbox API/runner, PostgreSQL, data-api, backend, frontend and RAG search. Healthy PG, sandbox API, backend, FE, search | n8n `/healthz`, backend `/health/ready`, FE `/login` all local HTTP 200; external existing n8n `https://aio-t1.isitsoft.kr:5678/healthz` HTTP 200 |
| Volumes/network | `day65-n8n_n8n-data`, `oke-jihye-p0_postgres_data`, `day65-n8n_sandbox-tls`, and existing DinD volume ID are attached to corresponding `oke` containers. Existing `day65-n8n_default` external network reused | Service DNS names stay n8n/backend/frontend/postgres/data-api/rag-search. n8n encryption key, user/credential store and workflow history remain in the same volume; no parallel n8n or PostgreSQL writer ran |
| SearXNG/index | Old SearXNG and indexer are stopped, not deleted. No default `oke` SearXNG/index container exists | SearXNG is retained under optional profile `optional-search`; RAG index remains a manual `indexing` profile. RAG search stays running. OKE workflow reference list showed no SearXNG dependency |
| C03 | Direct general and IT-scope search each returned HTTP 200, `ok=true`, evidence=3. n8n `oke-search` HTTP 200, `ok=true`, evidence=3, document `password-policy` | Request IDs `oke-cleanup-general-20261105`, `oke-cleanup-it-20261105`, `oke-cleanup-n8n-search-20261105`. No answer-quality/threshold PASS claimed |
| C04/idempotency | n8n `oke-handoff` first and same-key retry both HTTP 200; ticket `T-2003` same; duplicate false then true; alerted true; DLQ false | New request key `oke-runtime-cleanup-20261105-c04-1`; PostgreSQL confirms that key persisted once. This is new verification data, separate from the prior two tickets |
| DB preservation | Before: employees/users/tickets/alerts/DLQ=`6/1/2/3/1`; RAG documents/chunks=`8/33`. After: `6/1/3/4/1`; RAG remains `8/33` | Delta is exactly the new ticket and alert. No employee, user, document or chunk rows changed |
| Admin gate | Login/relogin for `minji.admin` HTTP 200, `must_change_password=true` before/after. Protected admin API HTTP 403; logout HTTP 200; old session then HTTP 401; final logout HTTP 200 | Password was read from VM-only `.env.admin-handoff` in process memory; it was not printed or changed. Existing handoff file remains mode 600. This test does not complete password change or admin features |
| Credentials/workflows | Six credential records remain: Header Auth account `9a7e5JYI5ez9SXYB`, OKE Backend Internal `bbbd7d3ca8844561`, OKE RAG Index `2d789bbf47004b3f`, OKE RAG Search `a01bde174d3040de`, OKE Team Webhook `6eba4fcbc08d4d75`, OpenAI account `bZrnbEv127VVq5mT`. All 16 workflow credential references resolve | Support/search/handoff/errors active; index inactive. Header Auth account has no current OKE workflow reference but is retained. Distinct typed credentials were not remapped or deleted |
| FE/image/resources | Local FE login 200. Running image now matches `oke-team-frontend:unified` (`2d2a43fd…`); previous container image ID `578a77e2…` remains with stopped old container | Before image mismatch came from an existing tag pointing to a newer built image while the old container retained its original immutable image ID. No image deletion. RAM available 1347→1433 MiB; disk free 41 GiB; swap used 392→235 MiB |

All old project containers remain stopped and retained. Old index/search/data-api had exit 137 and `OOMKilled=false`; old sandbox runner exit 143 and `OOMKilled=false`. Prior `oke-jihye-p0-postgres-1`, `day67-data-data-api-1`, and completed sandbox-certs exit-0 container remain. No volume, image, container, backup, credential or course file was deleted. The official `flow.py` and common-14 kit were not run. External HTTPS FE root/3000 routing was not changed or retested; the earlier 502/timeout remains a separate issue. No Netbird, nginx, or external ingress setting was modified.

Rollback: first stop project `oke`, then start the retained `day65-n8n` PostgreSQL, data-api, sandbox API, sandbox runner, backend, RAG search, frontend, n8n and runners in dependency order as listed in `deploy/README.md`. Do not start both projects at once because they share exact volumes and host ports. SearXNG and RAG index remain stopped during rollback.

## 9. DAY81 1교시 baseline · 2026-11-06

This is a later **read-only** observation than the 2026-11-05 cleanup record in section 8. The older external FE `502`/`:3000` timeout in sections 7–8 is historical and superseded for public FE routing by the checks below; it is not the current external route status. No VM deployment, account, password, workflow, credential, DB, service, or volume was changed for this report.

| Observation | Actual result | Scope / limit |
|---|---|---|
| Git/runtime version boundary | Repo `main=997ea60`; VM repo `a3dd276`; runtime implementation `c1a4c8b` | These commits refer to different environments. `997ea60` is not claimed deployed to VM. VM values are from the controller's read-only snapshot at `2026-11-06T01:01:00Z`. |
| VM containers / readiness | Compose project `oke`; 9 containers running: n8n, runners, sandbox API/runner, PostgreSQL, data-api, backend, frontend, RAG search. PostgreSQL, sandbox API, backend, frontend, RAG search report healthy. Backend readiness `ready`, `service_mode=app`; n8n/backend/runners mode `app`. | Container/runtime metadata only; no new end-to-end request was sent. |
| DB baseline | Alembic `0005`; employees/users/tickets/alerts/DLQ = `6/1/3/4/1`; RAG documents/chunks = `8/33` | Read-only counts from the stated VM snapshot. Existing 8-document / 33-chunk index is a baseline, not a new indexing run or a quality result. |
| Admin readiness | `minji.admin` active admin; `must_change_password=true` | Read-only metadata. No login, password change, or account creation in this task. There is one user account and no general employee login account in this snapshot. |
| n8n workflow state | `oke-support`, `oke-search`, `oke-handoff`, `oke-errors` active; `oke-index` inactive/manual. Six credential records present. | Metadata only. Active runtime versions are documented in `docs/VM-TEAM-TESTING.md`; version UUIDs are not Git commits. No credential values or IDs recorded here. |
| Resource snapshot | RAM total `2646 MiB`, available `1436 MiB`; swap total `2965 MiB`, used `224 MiB` | Snapshot-only values, not a sustained load test. |
| Public FE/API routing (read-only curl during report) | `http://aio-t1.isitsoft.kr/login` → HTTPS (`301`, one redirect); HTTPS `/login` `200` HTML; Next static JS asset `200`; no-cookie `/api/auth/me` `401`; `https://aio-t1.isitsoft.kr:5678/healthz` `200` | Confirms FE HTML/static asset, public `/api` prefix authentication response, and n8n health only. External `/api/docs`, `/api/openapi.json`, `/docs`, `/openapi.json` all return 404; Swagger/OpenAPI is not externally supported. No authenticated FE question/ownership/save flow was run. This resolves the earlier routing observation, not the application test gap. |
| Official common-14 source / runner | No `cases/common.json` found in the repository or the inspected `Last3Mon/79` course tree. Available `Last3Mon/79/tools/flow.py` SHA-256 `6b0059cb3af135b08954559d0e6b757991fc2fc42a0624244d129e618284fb6f`; its request helper sends JSON content type only and does not support the custom `X-Team-Key` required by current root workflow. | Official common-14 execution not run; pass/total, coverage result, and raw output are N/A/not available. Do not report `0/14` failed or `14/14` passed. Mock checker and team cases are not the official suite. |

The public FE routing check and the controller VM snapshot above are separate observations. The VM snapshot source is the read-only `DAY81-VM-READONLY-SNAPSHOT.txt` handoff; public URL checks used read-only HTTP requests. The report does not imply a login, RAG search, ticket write, alert/DLQ, fault, restore, or common-14 test.

### 1교시 출발점 판정

The 1교시 report material is prepared, but the official common-14 test starting point remains incomplete: the original case file and compatible official runner/authentication procedure have not been handed off. The 81-day checklist's other same-day required checks, including normal evidence-backed answer and its timing criterion, are not complete merely because the VM is healthy or retains 8/33 indexed records. Yubeen's RAG follow-up is scheduled for the weekend after feature freeze/final submission; that does not postpone today's required measurements. The team lead must decide whether to assign a same-day substitute and reserve a safe test window. No substitute owner or score threshold is invented here.

## 10. DAY81 Swagger 공개 경로 · 2026-11-06T10:24:37.289524+09:00

- TASK `vm-public-swagger-1`; FE source `e7f5161`, 이전 VM repo `a3dd276`/통합 runtime `c1a4c8b`와 구분. ff-only 후 frontend만 rebuild/up --no-deps. 나머지 8개 OKE 서비스 ID·StartedAt·image 동일.
- `GET https://aio-t1.isitsoft.kr/docs`: 200 HTML/SwaggerUIBundle, schema URL `/openapi.json`.
- `GET https://aio-t1.isitsoft.kr/openapi.json`: 200 JSON, OpenAPI 3.1.0, 18 paths; `/api/auth/login`, `/api/auth/me`, `/api/ask`, `/api/my-requests`, `/api/admin/tickets`, `/tickets` 존재.
- 회귀: FE `/login`200, HTML에서 찾은 Next static JS200, cookie없는 `/api/auth/me`401, n8n `:5678/healthz`200. `/api/docs`·`/api/openapi.json`은404 유지.
- 기존 cookie/header 인증을 바꾸지 않았다. 스키마 열람만 확인했으며 실제 업무 POST/삭제·계정/비밀번호·DB변경 시험을 수행하지 않았다. UI 접근200은 인증 API 무조건 성공/공통14 통과의 근거가 아니다.

## 11. FE/BE 통합 배포 및 실 API·DB 대조 · 2026-11-06 11:52–11:55 KST

### 코드·배포 경계

- FE/BE 통합 commit `99fff9c`를 GitHub main에 push했다. FE는 세션/역할 가드, 로그아웃/비밀번호 변경, 질문·내 문의 및 관리자 API 호출을 사용하고 UI fixture 경로를 제거했다. BE `/api/my-requests`는 인증 직원 소유 문의에 연결된 현재 티켓 상태/담당자 답변을 소유자·request key·inquiry 연결 조건으로 결합한다. `npm run typecheck`, `npm run build` 성공; BE `uv run pytest -q`: 162 passed, 65 skipped, 1 기존 deprecation warning. FE 빌드 성공은 브라우저 화면 통과와 구분한다.
- VM은 `99fff9c`로 ff-only 동기화 후 `SERVICE_MODE=app`에서 backend/frontend만 build/up 했다. 두 컨테이너 healthy. workflow, n8n, RAG search/index, PostgreSQL, data-api 및 기존 볼륨은 변경하지 않았다.
- 관리자 forced-first-change route guard의 순서 결함을 최소 수정한 FE-only commit `3ff836a`를 이후 push하고 frontend만 추가 배포했다. `npm run typecheck`·`npm run build` 재통과, frontend healthy. 이 수정의 로그인 암호변경 실제 화면 시연은 현재 관리자 계정이 이미 `must_change_password=false`여서 직접 검증하지 않았다.
- 최종 배포 뒤 공개 GET: `/login` 200, no-cookie `/api/auth/me` 401, `/docs` 200, `/openapi.json` 200, 기존 n8n `:5678/healthz` 200. 브라우저 host unavailable로 시각·클릭 검증은 미실행이다.

### 계정·단일 QA 실행

- 공식 API 검증 후 metadata: `minji.admin` active admin / `must_change_password=false`; `teamtest.employee1` active employee / `must_change_password=false`. 직원 시험 계정은 공식 roster에서 미발급 ID를 확인해 발급했다. 공식 첫 비밀번호 변경, 재로그인, `/api/my-requests` 200, employee의 admin endpoint 403, logout/세션종료가 확인됐다. 비밀값은 저장소 밖 private handoff에만 둔다.
- 공개 HTTPS QA runner의 고유 `request_id=real-qa-36352d26c53e48eab65a42c4a0c5ec85`, attempt 1, `default_vpn_attempt_1`: `POST /api/ask` HTTP 200, route `담당자 이관`, elapsed 7.341초, sources `[]`. 직원 문의 목록 조회, logout 후 재로그인 조회, admin 처리 PATCH 후 재조회, 직원의 관리자 경로 403가 확인되어 **안전 이관→실 DB 저장→관리자 처리→직원 재조회 API 경로만 PASS**다. 비밀 없는 raw JSON은 `develop/wonmin/runs/real-qa-api-20261106T1150KST.json`이다. 자동답변/검색 근거·8초 normal answer PASS는 아니다.
- API 목록에서 신규 row를 유일하다고 단정하지 않고, 11:52:07 KST read-only PostgreSQL query로 해당 고유 키를 대조했다: `app.inquiries` request_id 1행, `app.tickets` request_key 1행, ticket `T-2005`; inquiry ID 3 ↔ ticket inquiry_id 3, requester employee ID 1 일치, request key 일치, status `in_progress`, PATCH 답변 일치. 상세 대조는 운영자 비밀 없는 별도 관제 기록에 있으며 raw question/답변 본문은 이 문서에 복제하지 않는다.
- 배포 직후 전체 read-only count는 users/employees/inquiries/tickets/alerts=`2/6/2/4/5`였다. 이전 기준선과의 총량 차이는 동시 쓰기 가능성 때문에 이 시험의 row 근거로 사용하지 않았으며 기존·타인 row를 삭제/초기화하지 않았다.

### 남은 미검증

- Browser UI click/render, alert/DLQ와 중복 재요청, 본인/타인 API 대조, 재시작 영속성, 일반/IT 정상 문서검색, WF-01 자동답변 및 8초, 공식 common-14 suite는 미실행 또는 이 시험으로 입증되지 않았다. 안정 이관 API pass를 전체 업무/검색 품질 pass로 확대하지 않는다.


## 12. 6교시 팀장 지정 WF-02b 라이브 VM E2E 실측 · 2026-11-06 15:04 KST

### 실행 배경 및 입력

- **실행자**: 원민(QA), 팀장(오현) 지정 시나리오
- **환경**: 공개 운영 VM `https://aio-t1.isitsoft.kr`, VM 배포본 `3ff836a`, origin/main 최신 병합 후 `feat/wonmin-p0` @ `90fab63`
- **시나리오**: **WF-02b (보완 질문 한도 도달 후 자동 이관: attempt=3)**
- **입력**: 질문="접속이 안 돼요", attempt=3, context=없음
- **고유 요청 키**: `request_id=real-qa-4a2c0b16ce4341deb887c458f9d8aaa6`

### 실제 응답 및 10개 검사 결과

- **응답**: POST `/api/ask` HTTP 200, route `담당자 이관`, elapsed **4.535초**, sources `[]`, 티켓 `T-2011` (`in_progress`)
- **10개 검사 항목 전원 PASS (`PASS_API_SEQUENCE`)**:
  1. `employee_admin_forbidden_403`: true (일반 직원 계정의 관리자 엔드포인트 접근 403 차단)
  2. `forbidden_body_not_recorded`: true (차단된 응답 본문 미기록)
  3. `ask_created_one_ticket_response`: true (단일 티켓 생성 응답 확인)
  4. `inquiry_saved_and_listed_before_logout`: true (문의 저장 및 로그아웃 전 목록 조회 일치)
  5. `employee_logout_http_200`: true (직원 정상 로그아웃 200)
  6. `inquiry_and_ticket_visible_after_relogin`: true (재로그인 후 문의 및 티켓 상태 정상 조회)
  7. `admin_ticket_query_found_created_row`: true (관리자 티켓 쿼리에서 생성된 행 일치)
  8. `admin_status_and_reply_persisted`: true (관리자 상태 변경 및 답변 저장 정상 반영)
  9. `employee_latest_ticket_status_visible`: true (직원 화면에서 최신 티켓 상태 확인)
  10. `employee_latest_reply_visible`: true (직원 화면에서 최신 관리자 답변 확인)
- **증적 자료**: `develop/wonmin/runs/real-qa-WF02b-lead-20261106T060403Z.json`, 실행 맥락 `real-qa-WF02b-lead-context-20261106T060403Z.json`
- **판정**: **WF-02b 라이브 E2E 실측 통과 (PASS)**.

## 13. DAY81 Period 7 deployment 2 and QA snapshot · 2026-11-06 16:40–16:49 KST

### Version and deployment boundary

- GitHub `main` and the VM repository are at `17007f1`. Selected changes: FE visual update from `67ef41b` as main commit `840c5e6`; support workflow 15 from `aedbb95` as `bb3ef06`; explicit support-to-error workflow link as `17007f1`.
- The VM rebuilt and recreated **frontend only** from main `bb3ef06` (design commit `840c5e6`); the short recreate interval was about 8 seconds. Frontend returned healthy. No backend, RAG search, PostgreSQL, data-api, n8n, runner, or sandbox service was part of that scoped deployment.
- n8n support uses stable ID `okeSupportFlow01`, published runtime version `d0d6396d-08f4-4b8a-8514-4e8473a6203d`, 61 nodes, and `settings.errorWorkflow=okeErrorsFlow01`. The active Error Trigger workflow remained ID `okeErrorsFlow01`, version `8bab332b-8ca5-44f7-98d7-c824a75dd803`, with one Error Trigger node. The six existing support Credential references were preserved by ID/name/type; credential values are not recorded. Runtime exported support JSON SHA-256: `5ee90ae3514028c4ba5b46b1fdc8752b1567a0598d9653d578d861590d52cb8a`.
- n8n CLI reported that publication changes require a restart while n8n is running. Only `oke-n8n-1` was restarted; afterward health was HTTP 200, support and the existing search/handoff/errors workflows were active, and a production webhook POST without its auth header returned HTTP 403 (registration/authentication probe; the workflow did not execute). This was not an authenticated business-flow test.
- Rollback export captured the prior active support version `ece576c6-9c22-4243-9d18-68ba93a7a167` before replacement. VM backup: `/home/toor/.local/share/oke-backups/oke-support-before-bb3ef06-20261106T072504+0000.json`, SHA-256 `d7b4ed81a87973442ad0905df415d0f3d2885a6d086512d88c1c350fb20b1ad8`, mode 600.

### Read-only public and database evidence

- After FE deployment: `/login` HTTP 200; a Next static CSS asset HTTP 200; no-cookie `/api/auth/me` HTTP 401; `/docs` HTTP 200 with Swagger UI; `/openapi.json` HTTP 200 with OpenAPI 3.1.0 and 18 paths; n8n `/healthz` HTTP 200. No login, ticket mutation, or authenticated workflow POST was run by the deployer.
- Read-only PostgreSQL snapshot at 16:41:17 KST: `app.inquiries=13`, `app.tickets=12`, `app.alerts=14`, `rag.documents=8`, `rag.chunks=33`. The existing 8/33 RAG index was retained; no reindex or threshold change was performed.
- QA row correlation is in `orchestrator/status/PERIOD7-DB-ROWS.txt`: among 19 unique request IDs, 12 each matched exactly one ticket row and 7 matched no ticket row. `T-2018` was one ticket for WF-09; `T-2017` was the high-priority WF-12 ticket. This is QA-owned row evidence, not a total-suite pass count.
- The first six QA calls returned 403 because the private test harness key differed from the VM backend's webhook key; this does not establish a workflow feature failure. The server key/Credential was not changed. QA used the existing mode-600 private handoff file for a six-call retry; status/route/code matched the expected values for all six, while trace evidence remained incomplete.
- Final QA snapshot collected at 16:50 KST: 22 requests / 21 unique IDs. The base 20 requests (19 IDs) recorded observed-field tally 2 pass, 14 partial, 4 fail; two additional WF-01 repeats bring the total tally to 2 pass / 14 partial / 6 fail. The first six authentication-mismatch 403 responses are retained separately and are not classified as feature failures.
- WF-01 normal-answer repeats all handed off/failed: 4.270s, 3.585s, and 2.251s. No successful normal answer within 8 seconds was established.
- PostgreSQL read-only correlation: 14 ticket-response IDs each matched exactly one ticket row (the original 12 plus T-2025 and T-2026); 7 no-ticket IDs matched zero rows. WF-09 T-2018 had one row; WF-12 T-2017 was high priority. Detailed evidence: `orchestrator/status/PERIOD7-DB-VERIFICATION.md` and `PERIOD7-DB-ROWS.txt`.
- QA called n8n directly. This does not revalidate FE-to-FastAPI inquiry storage. Official common-14 coverage/score, WF-04/10/11 fault cases, alert/DLQ row verification, and actual Error Trigger auto-fire remain unverified. The 8-document/33-chunk RAG index was retained; no reindex or threshold change occurred. This is partial evidence, not a 7교시 completion claim.

### Evidence and remaining boundary

- The T-2011 raw/context records were selected from `90fab63`, scanned for secret/token/password, email, and phone content, and restored at the exact paths referenced by the DAY81 report. No credential value was included.
- `sources=[]` remains an observed response field, not proof that the live VM lacked regulations; the database retained 8 documents/33 chunks and direct C03 search evidence exists. `test_recovery.py` is a Fake/MockStore test and is not a real PostgreSQL recovery pass.
- Official 14-type and full five-team regression were not complete in this snapshot. QA continues against the fixed VM/runtime versions; no further deploy or workflow edits are part of this report update.

## 14. DAY81 기능 동결 및 v18 로컬 측정 요약 · 2026-11-07

### 실행 경계

아래 `develop/dahyeok/runs/*.json`은 다혁 담당의 `oke-local` 격리 로컬 통합 스택 결과다. v18 로컬 측정/회귀 증거이며 팀 VM 라이브 전체 회귀나 공식 KSM common-14 러너 결과가 아니다. 지원 워크플로우의 새 VM 배포·기능 활성화·공식 체크리스트 전체 통과를 의미하지 않는다. 원본 입력/기대값은 바꾸지 않았다.

| JSON 원본 | 기록 범위 | 관측 요약 | 판정 경계 |
|---|---|---|---|
| `develop/dahyeok/runs/search-score-dist-20261106-1.json` | C03 Q01–Q13, Q08-it, X01–X04 (18개 HTTP 200) | C03 top-3 결과와 top-1 score 기록. 일반 Q08은 `security-incident`가 아닌 `software-usage`로 제한 검색됐고, IT 양성 Q08-it은 `security-incident` score 0.380. 기대 문서 score 범위는 0.380–0.709; 범위 밖 질문 top-1은 0.235–0.383. | 질문 파일은 `draft_not_frozen`; 고정 정답셋 평가가 아니므로 hit-rate·품질 통과나 임계값 승인으로 집계하지 않음. score 분포 관측은 VM live 값이 아님. |
| `develop/dahyeok/runs/common-regress-20261106-1.json` | WF-02, WF-02b, WF-03, WF-05, WF-06, WF-12 (6행) | 기록된 동작: 보완 질문 3.7s, attempt 한도 이관 1.9s, 무근거 이관 2.6s, 권한제한 안전 이관 3.1s, 타인 조회 거절 2.0s, 긴급 high 이관 2.0s. | JSON `ok` 필드는 runner 관측이며 DB 영수증 또는 전 공식요건 통과 증명 아님. |
| `develop/dahyeok/runs/common-rest-20261106-1.json` | WF-13 세 입력, WF-07, WF-05, WF-09, WF-11, WF-10, WF-04 (10행) | 400 입력 거절 3건; 마스킹 응답 2.9s; WF-09 동일 키 T-2048 재요청 duplicate=false→true (2.1/1.8s); LLM 장애 1.2s 안전 이관; ticket 장애 2.2s 안전 이관; timeout/느린 경로 4.4s. | WF-04/10은 격리 로컬 장애 시험. DLQ/alert 실 DB 행과 자동 Error Trigger 발화는 별도 입증 필요. |
| `develop/dahyeok/runs/practice-20261106-1.json` | WF-01, WF-12, WF-09×2, WF-04, TM-07, WF-11 (7행) | 로컬 `SERVICE_MODE=practice`; 자동답변 WF-01 10.8s, 긴급 high 2.6s, 동일 요청 T-2002 중복 표식, 장애 안전 응답. | WF-01 10.8s는 8초 기준을 넘는다. practice/로컬 결과이며 운영 VM 응답/DB 영수증으로 간주하지 않음. |
| `develop/dahyeok/runs/team-repeat-20261106-1.json` | TM-01–06, TM-08, TM-11–13, TX-1–5 (16행; TM-06 2회 포함) | runner 14/16, 반복 경로 5/5 (각 3/3)로 기록. TM-01 자동답변 9.9s; TM-02 질문 1.7s; TM-03 이관 T-2055 2.0s; TM-04 권한 거절 2.2s; TM-05 긴급 high T-2056 2.1s; TM-06 T-2057 중복 false→true. | 모든 개별 `ok=true`가 기대 동작 적합을 뜻하지 않음. 14/16은 보고서 집계이고 오류 2건/기대 차이를 보존. TM-01은 8초 초과. |

### Common 14 시나리오 종합표 (v18 로컬 근거)

| ID | 시나리오 | 측정 결과 / 증거 | 판정 |
|---|---|---|---|
| WF-01 | 정상 근거 자동답변 | `practice` 10.8s 자동답변; `team-repeat` TM-01 9.9s 자동답변과 remote-work-vpn 근거. | 로컬 동작 확인, 두 측정 모두 8초 기준 초과. VM 정상답변·시간 PASS 아님. |
| WF-02 | 정보 부족 1차 | `common-regress`: HTTP 200, 보완 질문, 3.7s. | 로컬 회귀 확인 |
| WF-02b | 보완 한도 도달 | `common-regress`: attempt 한도 이관, max_attempts, T-2051, 1.9s. | 로컬 회귀 확인; 라이브 영수증은 아래 T-2011 |
| WF-03 | 검색 결과 없음/무근거 | `common-regress`: HTTP 200 안전 이관, sources 빈 목록, 2.6s. | 로컬 회귀 확인; 라이브 영수증은 아래 T-2005 |
| WF-04 | 티켓 API 장애 | `common-rest`/`practice`: HTTP 200, ticket=null, tickets_down. | 격리 장애 시험; 라이브 DLQ/alert 영수증 미입증 |
| WF-05 | 권한 제한 | `common-regress`/`common-rest`: 제한 결과 안전 이관, 일반 요청 sources 빈 목록. | 로컬 관측; C03 일반/IT 라이브 권한 자료는 RAG 실측 절 참조 |
| WF-06 | 타인 티켓 조회 | `common-regress`: route=권한 없음, 타인 정보 미출력, 2.0s. | 로컬 회귀 확인 |
| WF-07 | 개인정보 마스킹 | `common-rest`: 연락처 마스킹, masked=2, 2.9s. | 로컬 회귀 확인 |
| WF-08 | 프롬프트 주입 | support-18 `LOCAL-TEST.md`는 차단/LLM 0회/티켓 미생성 PASS를 기록. 해당 다혁 runs JSON에는 별도 WF-08 행이 없음. | 로컬 보고 기록만; 해당 JSON raw 미포함 |
| WF-09 | 중복 요청 | `common-rest`: T-2048 duplicate=false→true; `practice`: T-2002 중복 표시. | 로컬 회귀 확인; 라이브 DB 멱등성은 T-2030 |
| WF-10 | LLM 장애 | `common-rest`: HTTP 200 안전 이관, `llm_down`, 1.2s. | 로컬 장애 시험 |
| WF-11 | 느린 외부 API/시간 | `common-rest` 4.4s 안전 응답, `practice` 6.6s. | 로컬만 확인; 경계별 6초/8초 기준 해석 및 VM 회귀 별도 |
| WF-12 | 긴급 보안 문의 | `common-regress`: high 이관, 보안 안내/마스킹, 2.0s; practice 2.6s. | 로컬 회귀 확인 |
| WF-13 | 잘못된 입력 | `common-rest`: 빈 질문·unknown_user·501자 모두 HTTP 400. | 로컬 회귀 확인 |

### Team 5 시나리오 종합표 (team-repeat v18 로컬)

| ID | 시나리오 | 실제 결과 | 판정 / 한계 |
|---|---|---|---|
| TM-01 | 정상 VPN 근거 답변 | HTTP 200 자동 답변, remote-work-vpn `2. VPN 인증서`, score 0.4142, 9.9s. | 동작 확인, 8초 초과 |
| TM-02 | 정보 부족 1차 | HTTP 200 보완 질문, 1.7s. | 기록상 예상 경로 일치 |
| TM-03 | 보완 질문 한도 | HTTP 200 담당자 이관, max_attempts, T-2055, 2.0s. | 기록상 예상 경로 일치; 로컬 ticket |
| TM-04 | 타인 접수 권한 거절 | HTTP 200 route=권한 없음, 타인 문의 정보 없음, 2.2s. | 기록상 예상 경로 일치 |
| TM-05 | 긴급 사고 + 본인 접수 | HTTP 200 high 이관, urgent, T-2056, masked=2, 2.1s. | 기록상 예상 경로 일치; 알림 DB 별도 대조 아님 |

## 15. 라이브 VM 결과와 DB 영수증 매핑 · 2026-11-07

| 요구/ID | 실환경 관측 | DB 영수증 | 증거와 경계 |
|---|---|---|---|
| 백엔드/DB 세션 인증·RBAC 및 문의 저장 (박지혜) | 비로그인 `GET /api/auth/me` **401** ➔ 직원 로그인 **200** (`HttpOnly` 세션 쿠키 발급 확인) ➔ 직원 세션의 관리자 API(`GET /api/admin/tickets`) 접근 **403 차단(RBAC 실증)** ➔ 직원 문의(`POST /api/ask` **200**, `route="자동 답변"`, source 1건) ➔ 내 문의(`GET /api/my-requests` **200**, 고유 `request_id` 1건 일치) ➔ 관리자 로그인 **200** 및 티켓 목록 **200** ➔ 양쪽 세션 로그아웃 **200**. | 웹 터미널 TLS 검증 세션에서 `oke-postgres-1` 읽기 전용 트랜잭션(`BEGIN READ ONLY / SELECT / COMMIT`)으로 `app.inquiries`에 해당 `request_id`의 `status="completed"` 1건 저장 확인 (자동 답변이므로 연결 ticket 0건·alert 0건). | [`runs/be-db-integration-20261107.json`](../runs/be-db-integration-20261107.json). 티켓-알림 조인은 아래 `T-2034`/`T-2030`/`T-2011` 영수증으로 상호 보완. |
| RAG 색인·pgvector 및 WF-05 권한 격리 (신유빈) | VM 배포 코드 `af82c3b` 및 `origin/main@8fda3f7`: 원문 API와 해시 정합한 **8문서/33청크** (`all` 7문서·30청크, `it` 1문서·3청크); `text-embedding-3-large`, pgvector `vector(3072)` 전 청크 차원 일치. `cl100k_base` 문서 본문 240–433자(195–375 tokens), 청크 13–156자(10–163 tokens), 임베딩 입력 26–182자(22–192 tokens). **WF-05 실서버 비교**: 동일 보안사고 질의 시 `access_levels=["all"]`에서 IT 규정 누출 **0건**(`wf05_leaked_it_count: 0`), `["all","it"]`에서 `security-incident` **2건** 정상 반환(HTTP 200). | read-only RAG 집계 (`rag.documents=8`, `rag.chunks=33`, `vector_dims=3072`) | [`runs/rag-search-eval-20261107.json`](../runs/rag-search-eval-20261107.json), [`runs/vm-search-observed-20261106.json`](../runs/vm-search-observed-20261106.json). |
| WF-01 / WF-02 / WF-02b / WF-03 메인 워크플로우 v18 실측 (임다혁) | `oke-support` v18 (63노드, `APPROVED_MIN_SCORE=0.40`) VM `oke-handoff` 30노드 복구 직후 2차 재시험 전원 **PASS**:<br>- **WF-01**: 자동 답변 정상 반환 (`password-policy` 2건, score `0.6687`/`0.6679`), 1차 호출(8.754s) 이후 연속 재측정 **6.9s · 4.8s · 3.8s** (1차 시험 재측정 **7.0s · 4.3s · 6.2s · 4.0s**, 전원 8초 이내)<br>- **WF-02**: 1차 보완 질문(`접속 대상 / 오류 메시지 / 발생 시점`) **1.812s PASS**<br>- **WF-02b (보완 한도 도달)**: 담당자 이관(`reason="max_attempts"`) 및 **신규 티켓 `T-2035` 발급 PASS** (**2.188s**)<br>- **WF-03 (무근거 질의)**: 담당자 이관(`reason="low_confidence"`, `sources=[]`) 및 **신규 티켓 `T-2036` 발급 PASS** (**3.004s**) | n8n `oke-support` v18 실행 및 신규 티켓 `T-2035`·`T-2036` 발급 확인 | 2차 재시험 [`runs/support-v18-integration-20261107.json`](../runs/support-v18-integration-20261107.json), 1차 복구 전 하위 장애 격리 기록 [`runs/support-v18-integration-20261107-before-fix.json`](../runs/support-v18-integration-20261107-before-fix.json). |
| WF-09 멱등성 및 `oke-handoff` 실서버 복구 (`T-2033` / `T-2034` / `T-2030`, 이원민·총괄 집무실) | 1) 초기 QA 호출 시 `oke-handoff` H01 웹훅 노드 유실(29노드)로 HTTP 500 발생 진단([`runs/live-integration-qa-20261107.json`](../runs/live-integration-qa-20261107.json))<br>2) **정본 30노드 재게시 후 실서버 검증 (`T-2033`, `T-2034`)**: 총괄 집무실 스모크(`T-2033`, `duplicate: false → true` 200 OK)에 이어 원민 님 2차 QA 재시험([`runs/live-integration-qa-20261107T113546Z.json`](../runs/live-integration-qa-20261107T113546Z.json))에서 1차 `T-2034` (`duplicate: false`, 2.257s), 2차 동일 `request_id` 재전송 `T-2034` (`duplicate: true`, 0.594s) **7/7 항목 PASS**<br>3) `/api/ask` 경유 멱등성(`T-2030`): 동일 request ID 2회 호출 시 HTTP 200 (5.433s, 2.919s), `duplicate: false → true` | `T-2034` 기준 1차 후 `app.tickets +1 (33→34)`, `app.alerts +1 (36→37)`, `app.dlq +0 (8→8)` / 2차 재전송 후 **`tickets +0`, `alerts +0`, `dlq +0`** (중복 티켓·중복 알림 0건 완벽 실증) | 복구 후 재시험 [`runs/live-integration-qa-20261107T113546Z.json`](../runs/live-integration-qa-20261107T113546Z.json), 1차 진단 [`runs/live-integration-qa-20261107.json`](../runs/live-integration-qa-20261107.json), `develop/wonmin/runs/live-duplicate-api-20261107T0124Z.json` (`T-2030`). |
| WF-02b / `T-2011` | VM `/api/ask` HTTP 200, attempt=3, 안전 이관, 4.535s, sources=[], T-2011. | QA sequence는 문의·티켓 생성/관리자 변경/직원 재조회 10 checks PASS. | `develop/wonmin/runs/real-qa-WF02b-lead-20261106T060403Z.json`, DB 상세는 해당 보고 경로. 2026-11-06 VM 배포 `3ff836a`. |
| WF-03 / `T-2005` | VM `/api/ask` HTTP 200, attempt=1, 안전 이관, 7.341s, sources=[], T-2005. | read-only DB에서 `app.inquiries` request_id 1행 ↔ `app.tickets.request_key` 1행; inquiry/ticket link·requester id 일치, 관리자 PATCH 및 직원 재조회 일치. | `develop/wonmin/runs/real-qa-api-20261106T1150KST.json`. 2026-11-06 배포 `3ff836a`. |

## 16. 실패·개선 사례 (6칸 표준)

| 증상 | 재현 조건 / 확인 근거 | 원인 | 조치 / 개선 | 재시험 결과 | 잔여 위험 |
|---|---|---|---|---|---|
| **1.** 실제 모드(v15)에서 정상 규정 질문(WF-01)까지 초기 N12 `0.80` 게이트에서 전부 `low_confidence`로 탈락하여 자동 답변이 0건 발생 (임다혁). | 로컬 및 VM 실제 모드에서 박서연 WF-01 질문 호출; C03 `search-score-dist-20261106-1.json` 측정에서 기대 문서 score는 `0.380–0.709`(중앙값 `0.571`), 범위 밖 최고는 `0.383`. | ① 초기 `0.80`은 Mock 전용 분기값이어서 실제 임베딩 코사인 점수를 수용하지 못함 ② N15가 Mock 모드일 때만 자동 답변을 허용하는 잠금이 남아 있었음. | v16~v18에서 실측 분포 기반으로 N12 기준값을 `0.40`으로 조정하고, Writer(`answerable` 판정·원문 근거만 사용) 및 Verifier(문장 단위 2차 검증) 필터를 결합. FAQ 보조 조회를 5노드→2노드로 경량화(전체 66→63노드). | 로컬 WF-01 5/5 자동 답변(p50 4.1s), 3회 반복 3/3(4.2~5.4s) 통과. **실서버 VM(`runs/support-v18-integration-20261107.json`)에서도 WF-01 자동 답변(재측정 `6.9s·4.8s·3.8s`), WF-02b(`T-2035`), WF-03(`T-2036`) 전원 PASS 확인.** | 기준값 `0.40`과 범위 밖 최고 `0.383`의 간격(`0.017`)이 좁으므로 Writer(`answerable=false`)와 Verifier 2차 검증을 필수 유지하고, VM 첫 호출 콜드 스타트(8.7~11.9s) 지연을 모니터링한다. |
| **2.** 로컬 통합 스택에서 `rag-search` 호출 시 HTTP 503 `search_unavailable` 발생 (임다혁). | `develop/dahyeok/Doc/LOCAL-TEST.md`의 N09 C03 재현. DSN 형식 수정 전 검색 호출. | `DATABASE_URL`이 `postgresql+psycopg://` SQLAlchemy URL로 생성되었으나 `rag-search`의 직접 `psycopg.connect()`는 `+psycopg` 스킴을 허용하지 않음. | `python3 local/setup.py repair-rag-dsn` 적용 후 `rag-search` 컨테이너 재생성. 실제 키는 노출하지 않음. | 로컬 n8n `/webhook/oke-search` HTTP 200, evidence 3건 확인. 실서버 VM(`runs/rag-search-eval-20261107.json`)에서도 C03 HTTP 200 및 WF-05 권한 격리(누출 0건) PASS 확인. | 배포 스크립트 및 환경변수 템플릿에서 SQLAlchemy 전용 DSN과 `psycopg` 표준 DSN을 분리 관리해야 한다. |
| **3.** 실서버 VM n8n `/webhook/oke-handoff` 호출 시 `Cannot read properties of null (reading 'disabled')` (HTTP 500) 발생 및 티켓 미발급 (이원민 / 총괄 집무실). | 2026-11-07 실서버 통합 QA(`runs/live-integration-qa-20261107.json`) 및 `oke-support` v18 1차 호출(`runs/support-v18-integration-20261107-before-fix.json`)에서 `handoff_unavailable` 발생. | 읽기 전용 진단 결과, VM에 게시된 `okeHandoffFlow01` 워크플로우에서 입구 웹훅 노드(`H01 Handoff Webhook`)와 연결이 유실되어 **29노드** 상태였음(`main` 정본은 **30노드**). | 총괄 집무실(`oc:0.1`)에서 H01 웹훅 노드가 포함된 `main` 정본 **30개 노드 `workflows/oke-handoff.json`을 VM n8n에 재게시(Publish)**하고, 사전 구조 점검 스크립트(`tools/live-wf09-check.py`)를 추가함. | **실서버 재호출 즉시 HTTP 200 OK 복구 완료**: 총괄 스모크(`T-2033`), 원민 님 WF-09 재시험(`T-2034`, `duplicate: false → true`, DB 티켓 +1·중복 +0, `runs/live-integration-qa-20261107T113546Z.json`), 다혁 님 WF-02b(`T-2035`)·WF-03(`T-2036`) **전원 PASS**. | n8n CLI/UI 반입 시 입구 웹훅 노드나 `webhookId`가 누락되지 않도록 정본 30노드 구조 사전 점검(`live-wf09-check.py`)을 배포 절차에 포함한다. |
| **4.** 웹 터미널에서 PostgreSQL 접속 시 `fe_sendauth: no password supplied`로 접속 거절 (박지혜). | 컨테이너 OS 계정을 `postgres`로 변경(`docker exec -u postgres ... psql`) 후 PostgreSQL 로컬 소켓 연결을 시도했을 때 발생. | VM DB가 로컬 소켓에서도 비밀번호 인증을 요구함. 비밀번호를 추측하거나 로그에 출력하는 방식은 보안 원칙상 금지됨. | `oke-postgres-1` 컨테이너에 이미 주입된 접속 설정을 컨테이너 내부 프로세스에만 사용하고, TLS 인증서 검증을 켠 웹 터미널 세션에서 `BEGIN READ ONLY` 트랜잭션을 수행함. | 동일 `request_id`(`jihye-int-20261107T134130-fbfb0e26`)의 완료 문의(`status=completed`) 1건 조회 성공 및 `COMMIT` 정상 종료 (`runs/be-db-integration-20261107.json`). | 해당 API 호출이 자동 답변 경로여서 티켓-알림 1:1 DB 조인은 이 요청만으로 검증되지 않음 (원민 님의 `T-2034`/`T-2030`/`T-2011` 영수증으로 상호 보완 완료). |

## 17. 범위·제출 상태

- 실서버 VM 검증 영수증 7종([`be-db-integration-20261107.json`](../runs/be-db-integration-20261107.json), [`rag-search-eval-20261107.json`](../runs/rag-search-eval-20261107.json), [`support-v18-integration-20261107.json`](../runs/support-v18-integration-20261107.json), [`support-v18-integration-20261107-before-fix.json`](../runs/support-v18-integration-20261107-before-fix.json), [`live-integration-qa-20261107T113546Z.json`](../runs/live-integration-qa-20261107T113546Z.json), [`live-integration-qa-20261107.json`](../runs/live-integration-qa-20261107.json), [`vm-search-observed-20261106.json`](../runs/vm-search-observed-20261106.json))을 루트 [`runs/`](../runs/) 디렉터리에 정식 취합 완료했다.
- 공통 14개 시나리오 정본([`cases/common.json`](../cases/common.json))과 팀 확장 시나리오([`cases/team.json`](../cases/team.json))가 루트 `cases/`에 완비되었으며, `WORKFLOW-DESIGN.md`·`RAG-ARCHITECTURE.md`·`EXECUTION-RESULT.md` 3대 핵심 산출물의 수치가 실서버 측정값과 1:1로 동기화되었다.


### 11/08 후속 검증 · 문의 연결과 첫 응답 지연

실서버 checkout은 `15ab6c9694acf7fbf692d54dd97309937c63ad49`이며, 아래는 11/07 원본 시험과 분리한 후속 관측이다. 원본 PASS/PARTIAL·실패 기록을 덮어쓰지 않는다.

- **DB 연결:** 기존 API 실요청 `qa-idempotency-93f0e5f3de6549109a17245cd1e84121` / `T-2030`을 읽기 전용 트랜잭션으로 다시 대조했다. 문의·티켓·알림 각 1건, 완료 문의, 직원 소유권·문의 FK·요청 키·응답 티켓 일치, 해당 요청 DLQ 0건을 확인했다. [근거](../runs/db-link-followup-20261108.json). 새 로그인·API 전송을 한 시험은 아니다.
- **지연 재현:** 비밀번호 규정 질문을 숨은 예열 없이 직접 `oke-support`에 전송해 12.425초·4.612초·3.633초를 관측했다. 첫 실행의 `N02 Normalize input`은 2944ms였다. 실행기 유휴 종료 값은 15초였다.
- **조치:** main의 `deploy/compose.vm.yaml`에서 `N8N_RUNNERS_AUTO_SHUTDOWN_TIMEOUT=0`으로 설정했다. VM에는 `/home/toor/.config/oke/runner-latency.yaml` overlay를 적용해 `runners`만 재생성했다. 다른 8개 컨테이너 ID는 전후 동일했다. DB·n8n·FE·백엔드 재시작이나 전체 main 재배포는 하지 않았다.
- **재측정:** 첫 측정 7.224초, 20초 유휴 간격 후 3.864초·3.887초로 모두 자동 답변·`password-policy` 근거·8초 이내를 확인했다. 첫 Code 노드는 2464ms였고 이후 두 번은 10ms·11ms였다. 전체 스택 콜드 재시작 조건이나 FE/API 전체 응답 시간을 보장하지 않는다.
- **재현 자산:** [실서버 검사 안내](../eval/LIVE-CHECKS.md)에 main 안의 실행 도구와 범위를 기록했다. 기존 인계의 로그인 정보가 현재 거절돼, 새 직원 세션의 전체 API·DB 회귀는 최신 비공개 계정 정보가 필요하다. 계정·비밀번호는 수정하지 않았다.

종합 기록: [후속 확인](../runs/integration-followup-20261108.json), [변경 전](../runs/workflow-latency-before-20261108.json), [변경 후](../runs/workflow-latency-after-20261108.json), [노드 시간](../runs/workflow-node-timings-20261108.json).

## 18. KSM-REQ §6 제출 전 체크리스트 (원문 15항목)

아래 15개 항목은 `KSM-REQ.md` §6 및 `08-SUBMISSION.md` 기준을 전수 대조하여 `WORKFLOW-DESIGN.md`, `RAG-ARCHITECTURE.md`, `EXECUTION-RESULT.md` 및 루트 `runs/` 영수증 취합 완료 상태를 반영했다.

**노코드 워크플로우 설계서**

- [x] Trigger → 처리 → 출력 흐름이 실제 구현과 일치한다.
- [x] 병렬·분기·루프 구조의 사용 목적이 명확하다.
- [x] 외부 연동별 인증 및 오류 처리를 기록했다.
- [x] 노드 간 페이로드의 필수·선택 필드와 변환 로직을 작성했다.

**RAG 아키텍처 설계서**

- [x] 청킹 단위·오버랩·길이 분포와 선정 근거를 작성했다.
- [x] 임베딩 모델 선정 이유와 실제 벡터 차원을 기록했다.
- [x] 거리 계산 방식과 인덱스·메타데이터 구조를 작성했다.
- [x] 백업·복구 및 확장 방안을 작성했다.

**워크플로우 실행 결과서**

- [x] 주요 시나리오별 실행 테스트 로그가 있다.
- [x] 예외 상황의 실제 처리 결과가 있다.
- [x] 기대 결과와 실제 결과를 구분했다.
- [x] 실패 사례와 재시험 결과를 기록했다.

**공통**

- [x] 세 설계서·결과서의 내용이 실제 구현과 일치한다.
- [x] 예시 수치를 팀의 실제 측정값으로 교체했다.
- [x] 인증정보와 개인정보가 문서·로그·저장소에 노출되지 않았다.
