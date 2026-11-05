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

The data-api remains a read-only input source at its existing course-provided bind mount. Its data directory and `server.py` must not be removed, copied into the repository, or modified as part of deployment. The database URL for FastAPI must use the dedicated application LOGIN granted `oke_app`; do not pass the PostgreSQL superuser URL to backend or RAG containers. Keep `SERVICE_MODE` explicit and do not claim app persistence while backend runtime settings or service checks are incomplete.

The frontend listens on port 3000 and proxies `/api/*` server-side to `backend:8000`. PostgreSQL remains loopback-only on 5432; backend remains loopback-only on 8000; n8n keeps its existing 5678 port. Do not run `down -v`, `volume prune`, or delete the course source directory.
