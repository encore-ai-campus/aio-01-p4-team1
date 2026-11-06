#!/usr/bin/env python3
"""Run the approved eight-document real indexer once through its local internal HTTP endpoint."""

import subprocess
import sys

CODE = r'''import json, os, urllib.error, urllib.request
request = urllib.request.Request("http://127.0.0.1:8766/internal/oke-index", data=b"", method="POST",
                                 headers={"X-Team-Key": os.environ["INDEX_TEAM_KEY"]})
try:
    response = urllib.request.urlopen(request, timeout=600)
    status, data = response.status, json.load(response)
except urllib.error.HTTPError as error:
    status = error.code
    try: data = json.loads(error.read())
    except Exception: data = {}
print(json.dumps({"http": status, "ok": data.get("ok"), "mode": data.get("mode"),
                  "counts": data.get("counts"),
                  "documents": [{"doc_key": d.get("doc_key"), "status": d.get("status"),
                                 "chunk_count": d.get("chunk_count"), "reason": d.get("reason")}
                                for d in data.get("documents", [])]}, ensure_ascii=False))
sys.exit(0 if status == 200 and data.get("ok") else 1)
'''


def main() -> None:
    result = subprocess.run(["docker", "exec", "oke-local-rag-index-1", "python", "-c", CODE],
                            capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode:
        print("Local RAG indexing did not complete; secret configuration was withheld.", file=sys.stderr)
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
