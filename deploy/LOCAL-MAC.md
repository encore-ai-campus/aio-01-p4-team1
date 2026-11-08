# Mac-local unified environment

This runs the `oke` app from the same repository revision as the VM in an isolated Mac-only Compose project. It does not connect to or change the VM. Use it when you want to test the FE locally or repeat the local integration checks.

## Local runtime

- Baseline source: GitHub `main` at `a3dd276` (the local-only support changes in this document are being committed separately).
- Verified host: Apple Silicon / ARM64, Docker Engine ARM64, Docker Compose 5.5.0, 16 GiB RAM. The active Docker memory limit was 7.8 GiB; measured service use was approximately 1.2 GiB after startup.
- FE: <http://localhost:3001/login>
- n8n: <http://localhost:15679>
- PostgreSQL, if a local host client is needed: `127.0.0.1:15432`.
- Backend, data-api, RAG and runners have no host-published ports.
- Compose project/network/volumes: `oke-local`, `oke-local-internal`, and `oke-local_*`. These do not reuse VM volumes or the existing Mac `chat-memory-db` volume. The existing database remains bound to `127.0.0.1:5432`; an SSH tunnel already occupies port 15678.
- SearXNG is optional and not started by default. RAG index is an on-demand profile; RAG search stays available.
- The n8n DinD sandbox runner remains enabled because the n8n stack depends on it. It is privileged inside Docker but has no host-published ports. The task broker listens on the isolated Docker network and is not published to the Mac host.
- The Mac overlay sets `N8N_RUNNERS_BROKER_LISTEN_ADDRESS=0.0.0.0` so the separate runner container can reach n8n over the private Compose network. This listener is not host-published. This is a local network setting; `compose.vm.yaml` was not changed.

## Fresh setup

Run from `deploy/` in this repository. Docker Desktop/Engine must already be running.

```sh
python3 local/setup.py init
```

`init` verifies all eight approved source-document hashes and creates local-only environment files in `local/.private/` with directory mode `0700` and file mode `0600`. It creates new Mac-only database, app, RAG, n8n, runner, team, session, and initial admin secrets. It never copies a VM environment file, password, credential, or database dump. The repository root `data-api/server.py`, `data/`, `knowledge/`, and `prompts/` are mounted read-only. `init` verifies the eight local `knowledge/` documents against `rag/rag-permissions.json`; no course checkout or external source directory is required.

If an approved OpenAI key is supplied as a macOS textClipping file, import it without printing its content:

```sh
python3 local/setup.py import-openai-clipping /path/to/approved-key.textClipping
```

The command accepts only a single OpenAI key in the clipping's UTF-8 text, stores it in `local/.private/openai.env`, and does not alter the source clipping. The key is also imported to a local-only OpenAI n8n credential by the n8n bootstrap below.

Validate the Mac overlay before starting containers:

```sh
docker compose --env-file local/.private/compose.env \
  -f compose.vm.yaml -f compose.local.yaml -p oke-local config --quiet
```

Build ARM-native application images and initialize the TLS material, then initialize the isolated database and roster:

```sh
docker compose --env-file local/.private/compose.env \
  -f compose.vm.yaml -f compose.local.yaml -p oke-local --profile tls-bootstrap run --rm sandbox-certs
docker compose --env-file local/.private/compose.env \
  -f compose.vm.yaml -f compose.local.yaml -p oke-local build backend frontend rag-search
docker compose --env-file local/.private/compose.env \
  -f compose.vm.yaml -f compose.local.yaml -p oke-local up -d postgres data-api
docker compose --env-file local/.private/compose.env \
  -f compose.vm.yaml -f compose.local.yaml -p oke-local --profile local-setup run --rm db-migrate
python3 local/setup.py provision-db-roles
docker compose --env-file local/.private/compose.env \
  -f compose.vm.yaml -f compose.local.yaml -p oke-local --profile local-setup run --rm seed-employees
docker compose --env-file local/.private/compose.env \
  -f compose.vm.yaml -f compose.local.yaml -p oke-local --profile local-setup run --rm bootstrap-admin
docker compose --env-file local/.private/compose.env \
  -f compose.vm.yaml -f compose.local.yaml -p oke-local up -d
python3 local/bootstrap_n8n.py
```

The official employee seed uses the course data-api's verified internal no-auth mode against the fixed `data-api:8800` service origin. It does not modify the six source employees. `bootstrap-admin` creates the local `김민지 / minji.admin` account from the official backend bootstrap service, keeps `must_change_password=true`, and uses a Mac-only random password. Do not change that password as part of verification. The generated handoff is `local/.private/admin-handoff.env` (0600). The separate local n8n owner handoff is `local/.private/n8n-owner.env` (0600). Keep these on the Mac; neither belongs in Git or chat.

`bootstrap_n8n.py` creates the local n8n owner if needed, imports separate Header Auth credentials for the team webhook, RAG search, RAG index, and backend internal API, and imports an OpenAI credential only if `openai.env` exists. It prepares and imports the five current root workflows with local credential IDs. Support, search, handoff and errors triggers are published. `oke-index` remains inactive because it has no incoming trigger and the service is run manually. This script is idempotent for already-existing credentials/workflows and does not replace them.

## Start, stop, and recover

Run these from `deploy/`:

```sh
# Start the standard stack. The optional SearXNG and indexing profiles remain stopped.
docker compose --env-file local/.private/compose.env -f compose.vm.yaml -f compose.local.yaml -p oke-local up -d

# View service state or follow logs (never use `config` without --quiet in shared output).
docker compose --env-file local/.private/compose.env -f compose.vm.yaml -f compose.local.yaml -p oke-local ps
docker compose --env-file local/.private/compose.env -f compose.vm.yaml -f compose.local.yaml -p oke-local logs -f backend frontend n8n rag-search

# Stop containers while retaining all local data.
docker compose --env-file local/.private/compose.env -f compose.vm.yaml -f compose.local.yaml -p oke-local stop

# Resume stopped containers.
docker compose --env-file local/.private/compose.env -f compose.vm.yaml -f compose.local.yaml -p oke-local start
```

Never use `down -v`, `volume prune`, or `system prune` for this environment. If containers need to be recreated, use the explicit `-p oke-local` command and preserve the `oke-local_*` named volumes. The Mac data volume is `oke-local_postgres-data`; n8n state and encryption key are in `oke-local_n8n-data`.

To perform the one-time real index in the isolated local database:

```sh
docker compose --env-file local/.private/compose.env -f compose.vm.yaml -f compose.local.yaml -p oke-local --profile indexing up -d rag-index
python3 local/index_once.py
docker compose --env-file local/.private/compose.env -f compose.vm.yaml -f compose.local.yaml -p oke-local --profile indexing stop rag-index
```

The indexer accepts exactly the eight approved read-only Markdown documents, verifies their hashes and permission manifest, and writes to the local RAG tables. Re-running with unchanged data skips unchanged documents; it does not re-embed them. Do not copy the VM's database or indexed vectors into the Mac environment.

## Verification and known limits

Verified on this Mac:

- ARM64 backend, RAG, and Next.js 15 production builds succeeded.
- FE `/login` and n8n `/healthz` returned HTTP 200. Backend readiness returned HTTP 200 from inside the Compose network; it is intentionally not published on the Mac host.
- The local roster and administrator bootstrap produced 6 employees and 1 user. Admin login through the FE API proxy returned 200 with `must_change_password=true`; the pre-change protected tickets API returned 403; logout returned 200; `/me` after logout returned 401; relogin returned 200 with the first-change flag still set. The administrator password was not changed.
- n8n stored 5 local credentials (4 purpose-specific Header Auth plus 1 OpenAI). Every reference in the five imported workflows resolved to an existing local credential. Support/search/handoff/errors were active; index remained inactive/manual.
- Real local indexing stored 8 documents and 33 chunks: 7 `all` documents and `security-incident` as `it` (3 chunks). No VM documents or live tickets were copied.
- Three direct C03 requests returned HTTP 200: normal search returned `password-policy`; IT search included `security-incident`; an `all`-only request did not return `security-incident`. These verify service execution and access filtering, not answer quality or an unmeasured score threshold.
- The published n8n `oke-search` webhook also returned HTTP 200 / `ok=true` with `remote-work-vpn` evidence through its local Header Auth mapping.
- One real support webhook completed HTTP 200 through its conservative `담당자 이관` / `low_confidence` route and stored ticket `T-2002`; it did not produce a sourced automatic answer.
- C04 handoff returned HTTP 200 with `T-2001`, `duplicate=false`, `alerted=true`; a same-key request returned the same ticket with `duplicate=true`. The local DB contains one row for that request key.
- After restarting only the local PostgreSQL container, the counts remained employees/users/tickets/alerts/DLQ/documents/chunks = `6/1/2/2/0/8/33`; FE login, n8n health, and internal backend readiness remained HTTP 200.
- The official course `flow.py check` is static and course-specific. On the local support workflow it reported six credential-ID errors because it requires the course placeholder ID `openAiCourse0001`, while this isolated local stack correctly uses its own credential IDs. `flow.py test` was not used: it cannot add the required `X-Team-Key` header for the protected webhooks. The direct HTTP checks above exercised the local endpoints with their dedicated local credentials.

The app administrator remains in the required first-password-change state. No separate changed-password validation account was created. FE login and its API proxy were verified over HTTP; an authenticated FE question could not be run as that admin without changing the retained initial password. Direct C03 service calls and one authenticated n8n support call were tested instead. Search threshold and answer quality remain unmeasured, so these results are not a quality PASS. VM runtime, configuration, and data were not changed.
