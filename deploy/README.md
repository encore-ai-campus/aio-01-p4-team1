# Unified VM deployment

`compose.vm.yaml` runs the team stack as Compose project `oke`. It keeps the existing service DNS names (`n8n`, `backend`, `frontend`, `postgres`, `data-api`, `rag-search`) and reuses the existing `day65-n8n_default` network. Reusing the established network preserves the current VM ingress and other attached peers; this task does not change ingress or publish new ports.

The three critical data volumes are external and retain their exact existing names: `day65-n8n_n8n-data`, `oke-jihye-p0_postgres_data`, and `day65-n8n_sandbox-tls`; sandbox DinD uses its existing external volume ID. The Compose file also retains the existing SearXNG volumes. Never run `down -v`, volume prune, or delete old containers/backups as part of a project rename.

## Standard deployment

From the repository root on the VM, use the existing private environment files and explicitly set the app mode. The deploy helper performs this same sequence. The operator command is `python3 deploy.py deploy` from the private `vm_deploy` folder on the Mac. It fast-forwards VM `main`, validates Compose, builds the three `oke-team-*` images while the old project is available, stops old containers without removing them, then starts project `oke` and checks local readiness. PostgreSQL and n8n never share their volumes concurrently.

```sh
SERVICE_MODE=app docker compose \
  --env-file /home/toor/n8n/day65-n8n/.env \
  --env-file develop/jihye/deploy/.env \
  -f deploy/compose.vm.yaml -p oke config --quiet
SERVICE_MODE=app docker compose \
  --env-file /home/toor/n8n/day65-n8n/.env \
  --env-file develop/jihye/deploy/.env \
  -f deploy/compose.vm.yaml -p oke up -d --build
```

The private n8n environment file, backend environment file, and RAG `search.env`/`index.env` remain at their established VM paths and are not committed. The n8n encryption key, user database, credentials, workflow history, PostgreSQL data, and app/RAG records are preserved in the existing external volumes. The backend uses the dedicated application LOGIN, never the PostgreSQL superuser.

## Optional services

SearXNG is excluded from the default service set and retained for recoverable manual use with `--profile optional-search`. No OKE workflow currently references it; C03 search uses `rag-search`, and safe handoff uses the app backend. The RAG index service remains off by default under the `indexing` profile. Start it only for an approved indexing run:

```sh
SERVICE_MODE=app docker compose --env-file /home/toor/n8n/day65-n8n/.env \
  --env-file develop/jihye/deploy/.env -f deploy/compose.vm.yaml -p oke \
  --profile indexing up -d rag-index
```

After indexing, stop that service without removing it: `docker compose ... --profile indexing stop rag-index`. Search remains continuously available at the internal `rag-search` service DNS. The indexer reads the existing course documents read-only and checks the committed permission/hash manifest.

## Rollback

Never run old and new Compose projects simultaneously: they intentionally reference the same n8n and PostgreSQL volumes and host ports. If target readiness fails, first stop project `oke`, then restart the retained old containers in dependency order. SearXNG and RAG index remain stopped as directed.

```sh
docker compose --env-file /home/toor/n8n/day65-n8n/.env --env-file develop/jihye/deploy/.env \
  -f deploy/compose.vm.yaml -p oke stop
docker start day65-n8n-postgres-1 day65-n8n-data-api-1 day65-n8n-sandbox-api-1
docker start day65-n8n-sandbox-runner-1-1 day65-n8n-backend-1 day65-n8n-rag-search-1 day65-n8n-frontend-1
docker start day65-n8n-n8n-1 day65-n8n-runners-1
```

This starts the existing containers with their original image IDs and mount bindings; it does not recreate or delete them. Verify n8n `:5678/healthz`, backend health, and PostgreSQL before considering rollback complete. The existing external HTTPS ingress is unchanged. A working local port binding alone does not prove external FE access; prior external FE 502/3000 timeout remains a separate ingress issue.

## Cleanup record · 2026-11-05

GitHub `main` and VM repository both run commit `c1a4c8b` (GitHub implementation commit; VM fast-forward target). The pre-switch backup is `/home/toor/backups/oke-runtime-cleanup-20261105-final` (directory mode 700; private files mode 600; PostgreSQL dump nonempty; n8n volume copy 7.87 MB; recorded checksums verified). Local Compose `config --quiet` passed on the VM before the switch and after startup.

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
