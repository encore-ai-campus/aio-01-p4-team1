# Root deployment

Application build contexts are `apps/backend/`, `apps/frontend/`, and `apps/rag/`. Both Compose definitions use only files in this checkout for code and input data. [LOCAL-MAC](LOCAL-MAC.md) initializes an isolated local stack without a separate course checkout. This path migration changes repository configuration; it does not deploy or restart the VM.

## 11/09 운영 VM 보존과 시험 준비

**기존 `/home/toor/Aio-4pj-1team`에서는 바로 `git pull`하지 않는다.** [11:52 KST 읽기 확인](../runs/vm-pull-safety-20261109.json)에서 VM은 `15ab6c9`이며 data-api가 그 폴더의 `data-api/data`·`data-api/server.py`를 직접 사용 중이었다. 비교한 main `5d13efb`는 해당 데이터 22개와 서버 파일을 새 경로로 옮겼다. 운영 폴더의 pull은 실제 연결 중인 파일을 제거할 수 있고, 컨테이너가 읽기 전용으로 연결했어도 호스트 Git 변경은 막지 못한다. 최신 Compose 파일을 받는 것만으로 기존 mount가 새 경로로 바뀌지는 않는다.

1. **Mac에서 현재 VM을 시험:** Mac의 저장소 루트에서 아래 정상 요청 검사기를 실행한다. VM 소스 업데이트는 필요 없다. 비공개 시험 환경 파일에는 대상 VM 문의 웹훅의 `OKE_TEAM_KEY`를 준비하고, Mac 로컬 스택용 키와 구분한다. 키는 Git·명령 인수·출력에 넣지 않는다.

   ```sh
   python3 eval/webhook_latency.py \
     --env-file /path/to/private-test.env \
     --repeats 1 --idle-seconds 0 \
     --output "/private/tmp/oke-webhook-test-$(date +%Y%m%d-%H%M%S).json"
   ```

   현재 VM에 실제 질문 1건을 보내므로 API 비용과 실행 기록이 발생한다. 자동 답변·규정 출처·티켓 없음·8초 이내를 확인하며, FE·API 세션·DB 연결이나 공식 전체 사례를 검사하지 않는다. 계정·DB까지 확인하는 별도 범위는 [실서버 검사 안내](../eval/LIVE-CHECKS.md)를 따른다.

2. **VM에서 도구만 준비:** 서비스에 연결되지 않은 별도 폴더를 사용한다. 아래 경로는 확인 시점에 없었으며, 이미 존재한다면 운영 mount와 무관한 시험 폴더인지 먼저 확인한다.

   ```sh
   git clone --depth 1 --branch main \
     https://github.com/hyunport/Aio-4pj-1team.git ~/oke-test-runner
   cd ~/oke-test-runner
   uv run tools/flow.py --help
   ```

   여기까지는 파일 준비·도움말 확인이다. 공식 원본은 웹훅 인증과 일부 사례의 추가 판정을 지원하지 않으므로 `test` 전체를 바로 실행할 준비가 끝난 상태가 아니다. [도구 한계](../tools/README.md)를 확인한다. 시험 폴더에서 Compose 실행·`flow.py push`를 하지 않는다. 기존 컨테이너·볼륨·활성 워크플로우·운영 키·app 모드를 유지한다.

현재 main의 경로 구조로 운영 VM을 옮기는 작업은 별도 배포 계획·승인 대상이다. 아래 배포 절차를 이 시험 준비의 다음 단계로 실행하지 않는다. 실제 Mac 요청 결과와 미실행 항목은 [DAY82 검토 결과](../docs/DAY82-TEST-REVIEW.md)에 있다.

# Unified VM deployment

For a separate Mac-local copy of this stack (isolated Compose project, local-only secrets and volumes, FE at port 3001), see [LOCAL-MAC.md](LOCAL-MAC.md). The Mac setup does not use the VM's volumes or mutate VM runtime/configuration/data.

`compose.vm.yaml` runs the team stack as Compose project `oke`. It keeps the existing service DNS names (`n8n`, `backend`, `frontend`, `postgres`, `data-api`, `rag-search`) and reuses the existing `day65-n8n_default` network. Reusing the established network preserves the current VM ingress and other attached peers; this task does not change ingress or publish new ports.

The three critical data volumes are external and retain their exact existing names: `day65-n8n_n8n-data`, `oke-jihye-p0_postgres_data`, and `day65-n8n_sandbox-tls`; sandbox DinD uses its existing external volume ID. The Compose file also retains the existing SearXNG volumes. Never run `down -v`, volume prune, or delete old containers/backups as part of a project rename.

## Standard deployment

The commands below are for a new installation or a separately reviewed migration after sources and private environment paths are provisioned. They are not instructions to pull into the retained live checkout described above. From the intended deployment root on the VM, use the private environment files and explicitly set app mode. The operator validates Compose, builds and starts the target services, then checks readiness under the approved deployment plan. These commands can recreate services. PostgreSQL and n8n must never share their volumes with another running project concurrently.

```sh
SERVICE_MODE=app docker compose \
  --env-file /home/toor/n8n/day65-n8n/.env \
  --env-file apps/backend/deploy/.env \
  -f deploy/compose.vm.yaml -p oke config --quiet
SERVICE_MODE=app docker compose \
  --env-file /home/toor/n8n/day65-n8n/.env \
  --env-file apps/backend/deploy/.env \
  -f deploy/compose.vm.yaml -p oke up -d --build
```

Backend private configuration belongs in `apps/backend/deploy/.env.backend`; RAG configuration belongs in `apps/rag/.env.openai`, `apps/rag/search.env`, and `apps/rag/index.env`. Existing installations must provision these root paths before their next recreation. These files are not committed. The private n8n env file is supplied by the deployment environment. The n8n encryption key, user database, credentials, workflow history, PostgreSQL data, and app/RAG records are preserved in the existing external volumes. The backend uses the dedicated application LOGIN, never the PostgreSQL superuser.

## Optional services

SearXNG is excluded from the default service set and retained for recoverable manual use with `--profile optional-search`. No OKE workflow currently references it; C03 search uses `rag-search`, and safe handoff uses the app backend. The RAG index service remains off by default under the `indexing` profile. Start it only for an approved indexing run:

```sh
SERVICE_MODE=app docker compose --env-file /home/toor/n8n/day65-n8n/.env \
  --env-file apps/backend/deploy/.env -f deploy/compose.vm.yaml -p oke \
  --profile indexing up -d rag-index
```

After indexing, stop that service without removing it: `docker compose ... --profile indexing stop rag-index`. Search remains continuously available at the internal `rag-search` service DNS. The indexer reads root `knowledge/` read-only and checks `apps/rag/rag-permissions.json`. The data API reads root `data/`, `knowledge/`, and `prompts/`.

## Rollback

Never run old and new Compose projects simultaneously: they intentionally reference the same n8n and PostgreSQL volumes and host ports. If target readiness fails, first stop project `oke`, then restart the retained old containers in dependency order. SearXNG and RAG index remain stopped as directed.

```sh
docker compose --env-file /home/toor/n8n/day65-n8n/.env --env-file apps/backend/deploy/.env \
  -f deploy/compose.vm.yaml -p oke stop
docker start day65-n8n-postgres-1 day65-n8n-data-api-1 day65-n8n-sandbox-api-1
docker start day65-n8n-sandbox-runner-1-1 day65-n8n-backend-1 day65-n8n-rag-search-1 day65-n8n-frontend-1
docker start day65-n8n-n8n-1 day65-n8n-runners-1
```

This starts the existing containers with their original image IDs and mount bindings; it does not recreate or delete them. Verify n8n `:5678/healthz`, backend health, and PostgreSQL before considering rollback complete. The existing external HTTPS ingress is unchanged. A working local port binding alone does not prove external FE access; prior external FE 502/3000 timeout remains a separate ingress issue.

## Cleanup record · 2026-11-05

`c1a4c8b` is the deployed runtime implementation commit. Follow-up docs-only changes were pushed and fast-forwarded to the VM without restarting services. The pre-switch backup is `/home/toor/backups/oke-runtime-cleanup-20261105-final` (directory mode 700; private files mode 600; PostgreSQL dump nonempty; n8n volume copy 7.87 MB; recorded checksums verified). Local Compose `config --quiet` passed on the VM before the switch and after startup.

| Verification | Result |
|---|---|
| Project/services | `oke` project: n8n, runners, sandbox API/runner, PostgreSQL, data-api, backend, frontend, RAG search are up; health checks healthy for PostgreSQL, sandbox API, backend, FE and RAG search |
| Service mode and endpoints | n8n/runners/backend `SERVICE_MODE=app`; localhost n8n `/healthz`, backend `/health/ready`, FE `/login`: HTTP 200. External `https://aio-t1.isitsoft.kr:5678/healthz`: HTTP 200 |
| Persistent storage | Existing `day65-n8n_n8n-data`, `oke-jihye-p0_postgres_data`, `day65-n8n_sandbox-tls`, existing DinD volume ID all mounted by the new project; service DNS and `day65-n8n_default` network retained |
| RAG/SearXNG | Search stayed up. General direct search and IT-scope direct search each returned HTTP 200 with 3 evidence rows; n8n `oke-search` returned HTTP 200/`ok=true`/3 evidence (`password-policy`). SearXNG and old RAG index containers are stopped and retained; default compose creates neither. `rag-index` remains manually startable with profile `indexing`; SearXNG with `optional-search` |
| App DB | Before: employees/users/tickets/alerts/DLQ = `6/1/2/3/1`, RAG documents/chunks `8/33`. After one new verification ticket and same-key retry: `6/1/3/4/1`, RAG `8/33`; retry returned same `T-2003`, duplicate=true. No duplicate ticket or DLQ row was added |
| Admin gate | `minji.admin` login/relogin succeeded; `must_change_password=true` throughout. Protected admin API returned expected 403 before password change; logout was 200, old session then 401. No password change was performed |
| n8n objects | Five OKE workflows present: support/search/handoff/errors active, index inactive. Six credentials retained; 16 credential references resolve. `Header Auth account` remains present despite no OKE references. No import/remapping was done |
| FE image | Before cutover, running FE used image ID `578a77e2…` while `oke-team-frontend:unified` pointed elsewhere. After rebuild/recreation, running ID equals the intended tag ID `2d2a43fd…`; the old stopped container/image was retained |
| Resources | Before: RAM available 1347 MiB, swap used 392 MiB, disk free 41 GiB. After: RAM available 1433 MiB, swap used 235 MiB, disk free 41 GiB. The stopped old index/search/data-api containers reported exit 137 with `OOMKilled=false`; no OOM is inferred |

All old `day65-n8n-*` containers remain stopped and available for rollback; the prior `oke-jihye-p0-postgres-1`, `day67-data-data-api-1`, and completed `day65-n8n-sandbox-certs-1` were also retained. No volume, image, backup, credential, course file, or container was deleted. Sandbox cert bootstrap exit 0 was a completed one-shot task. The official `flow.py`/common-14 kit was not run. Existing external FE root 502 / port 3000 timeout is outside this rename and remains unresolved; no HTTPS proxy or external route was changed.

## Runner idle latency · 2026-11-08

The root VM Compose sets `N8N_RUNNERS_AUTO_SHUTDOWN_TIMEOUT=0` to retain external Code-node workers between inquiries. The [official task runner documentation](https://docs.n8n.io/hosting/configuration/task-runners/) defines `0` as disabling idle shutdown. Isolation, authentication and execution timeouts remain configured as before. This increases idle worker memory use; the observed runners usage after the trial was about 84 MiB and VM available memory about 1163 MiB.

The live VM still has checkout `15ab6c9`. For the scoped change it uses `/home/toor/.config/oke/runner-latency.yaml` as an additional Compose file, and only `runners` was recreated. Before the VM switches to the latest root Compose, preserve this overlay on runner recreation:

```sh
docker compose --env-file /home/toor/n8n/day65-n8n/.env \
  --env-file /home/toor/Aio-4pj-1team/deploy/.env.vm \
  -f /home/toor/Aio-4pj-1team/deploy/compose.vm.yaml \
  -f /home/toor/.config/oke/runner-latency.yaml -p oke \
  up -d --no-deps --no-build runners
```

The `.env.vm` file above belongs to the retained **old VM runtime**. New deployment of current main uses the root paths documented above. Do not substitute the latest root Compose on the old checkout without first provisioning its root sources and private environment paths. Rollback of this scoped setting on the old checkout is the same command without the overlay, which restores its original 15-second idle timeout.

Measurements and container preservation are in [the follow-up receipt](../runs/integration-followup-20261108.json). This is a scoped runtime setting change, not a full main deployment or proof of whole-stack cold-start performance.

## Scoped ticket failure verification · 2026-11-08

The current backend has a request-scoped operator fault gate. The [test and recovery guide](../eval/TICKET-FAULT.md) explains its read-only directory, 300-second expiry and actual app-mode test. No public fault-setting endpoint was added.

The retained old VM checkout uses `/home/toor/.config/oke/ticket-fault.yaml` for the backend image, read-only gate directory, and **explicit `SERVICE_MODE=app`**. Preserve that overlay when recreating only the backend. The old Compose defaults can otherwise select practice storage. Runner-only recreation continues to use its separate latency overlay. The [final deployment receipt](../runs/ticket-fault-deploy-final-20261108.json) records the rollback image, source hashes and unchanged other eight containers. This is not a full current-main deployment.
