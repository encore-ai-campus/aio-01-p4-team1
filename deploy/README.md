# Unified VM deployment

`compose.vm.yaml` joins the existing n8n/runners/sandbox services, pgvector PostgreSQL, the course-provided data-api, FastAPI, Next.js frontend, and RAG HTTP services on the existing `day65-n8n_default` network. It deliberately references the existing named volumes for n8n, PostgreSQL, sandbox TLS/DinD, and SearXNG as external volumes. It does not recreate their contents.

Run from the repository root on the VM, after making and validating the private backups recorded in `UNIFIED-VM-TONIGHT.md`:

```sh
docker compose \
  --env-file /home/toor/n8n/day65-n8n/.env \
  --env-file develop/jihye/deploy/.env \
  -f deploy/compose.vm.yaml -p day65-n8n config --quiet
docker compose \
  --env-file /home/toor/n8n/day65-n8n/.env \
  --env-file develop/jihye/deploy/.env \
  -f deploy/compose.vm.yaml -p day65-n8n up -d --build
```

The VM-local `develop/jihye/deploy/.env.backend` supplies runtime-only FastAPI settings. `develop/yubeen/search.env` supplies RAG service credentials. These files are private, ignored, and never committed. The RAG indexer uses the `indexing` profile and must remain off until the approved source documents, their hashes, permission manifest, and scoped DB/OpenAI settings are all present. Search returns an unavailable response until its own runtime dependencies are configured.

Use `SERVICE_MODE=app` explicitly for the shared VM integration run so n8n, runners, and backend select the same app DB path. The employees/docs source is the existing read-only internal service `http://data-api:8800`. Its observed unauthenticated contract is enabled only by the explicit `DATA_API_EMPLOYEES_NO_AUTH=true` CLI setting, fixed to that service origin; do not invent a key/header. Search and indexing use separate `oke_rag_search` and `oke_rag_index` group roles through distinct LOGIN credentials. `develop/yubeen/.env.openai` supplies the existing n8n OpenAI credential key to both RAG processes without putting it in workflow JSON or logs. `search.env` and `index.env` carry separate DB URLs and X-Team-Key values; all three VM env files are mode 600 and Git-ignored. The indexer mounts the original course `data-api/data/docs` directory read-only and checks `rag-permissions.json` hashes before any embedding call.

The compose file does not configure the external HTTPS reverse proxy. Before team use, route the existing `https://aio-t1.isitsoft.kr/` ingress to the FE without publishing additional ports; test the HTTPS URL itself. `:3000` binding alone is not proof of external reachability.

The data-api remains a read-only input source at its existing course-provided bind mount. Its data directory and `server.py` must not be removed, copied into the repository, or modified as part of deployment. The database URL for FastAPI must use the dedicated application LOGIN granted `oke_app`; do not pass the PostgreSQL superuser URL to backend or RAG containers. Keep `SERVICE_MODE` explicit and do not claim app persistence while backend runtime settings or service checks are incomplete.

The frontend listens on port 3000 and proxies `/api/*` server-side to `backend:8000`. PostgreSQL remains loopback-only on 5432; backend remains loopback-only on 8000; n8n keeps its existing 5678 port. Do not run `down -v`, `volume prune`, or delete the course source directory.
