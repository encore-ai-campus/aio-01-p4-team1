"""Explicit employee response adapter; live response/authentication remain unverified."""

import httpx

EXPECTED_EMPLOYEES = {
    "이준호": "영업팀", "박서연": "재무팀", "최유진": "인사팀",
    "한지훈": "개발팀", "김민지": "IT팀", "정우성": "IT팀",
}


class SourceError(ValueError):
    pass


def validate_employees(rows: object) -> dict[str, str]:
    if not isinstance(rows, list) or len(rows) != 6:
        raise SourceError("employee_source_mismatch")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not isinstance(row.get("dept"), str):
            raise SourceError("employee_source_mismatch")
        if row["name"] in result:
            raise SourceError("employee_source_mismatch")
        result[row["name"]] = row["dept"]
    if result != EXPECTED_EMPLOYEES:
        raise SourceError("employee_source_mismatch")
    return result


def fetch_employees(client: httpx.Client) -> dict[str, str]:
    # Caller supplies a confirmed base URL and authentication; never infer headers.
    try:
        response = client.get("employees")
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError):
        raise SourceError("employee_source_unavailable") from None
    # Supported Mock contract only; other envelopes need a verified adapter.
    if not isinstance(data, dict) or "employees" not in data:
        raise SourceError("employee_response_unsupported")
    return validate_employees(data["employees"])
