"""Operator-controlled, expiring fault for one authenticated C05 ticket request."""

import json
import math
import re
import time
from pathlib import Path

MAX_SECONDS = 300
REQUEST_ID = re.compile(r"audit-fault-[a-f0-9]{32}")


def ticket_fault_active(path: Path, request_id: str) -> bool:
    # No HTTP endpoint can arm this switch. The runtime mounts its directory read-only.
    if not REQUEST_ID.fullmatch(request_id):
        return False
    try:
        with path.open("rb") as stream:
            raw = stream.read(1025)
        if len(raw) > 1024:
            return False
        rule = json.loads(raw)
        if not isinstance(rule, dict) or rule.get("request_id") != request_id:
            return False
        armed, expires = rule.get("armed_at"), rule.get("expires_at")
        if any(type(value) not in (int, float) or not math.isfinite(value)
               for value in (armed, expires)):
            return False
        now = time.time()
        return armed <= now < expires and 0 < expires - armed <= MAX_SECONDS
    except (OSError, ValueError, TypeError, RecursionError):
        # Missing, expired or invalid operator configuration leaves normal writes intact.
        return False
