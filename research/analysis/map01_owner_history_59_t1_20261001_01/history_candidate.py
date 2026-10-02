"""Offline, fail-closed collector contract for workflow-path owner history."""
from __future__ import annotations

from urllib.parse import urlencode


class IncompleteHistory(ValueError):
    pass


def build_runs_url(api_root: str, repository: str, workflow_file: str, *, page: int, per_page: int = 100) -> str:
    """Build the all-events list-workflow-runs URL; event is intentionally absent."""
    if not repository or "/" not in repository or not workflow_file.endswith(".yml") and not workflow_file.endswith(".yaml"):
        raise ValueError("repository and workflow file are required")
    if page < 1 or not 1 <= per_page <= 100:
        raise ValueError("invalid pagination")
    return (
        f"{api_root.rstrip('/')}/repos/{repository}/actions/workflows/{workflow_file}/runs?"
        + urlencode({"per_page": per_page, "page": page})
    )


def collect_pages(pages, *, max_pages: int, page_size: int) -> dict:
    """Collect supplied API pages, rejecting any view that cannot prove completeness."""
    if max_pages < 1 or not 1 <= page_size <= 100:
        raise ValueError("invalid page bounds")
    rows = []
    seen = set()
    total = None
    for page_number, payload in enumerate(pages, start=1):
        if page_number > max_pages:
            raise IncompleteHistory("page limit exceeded")
        if not isinstance(payload, dict) or type(payload.get("total_count")) is not int:
            raise IncompleteHistory("missing or malformed total_count")
        page_rows = payload.get("workflow_runs")
        if not isinstance(page_rows, list) or len(page_rows) > page_size:
            raise IncompleteHistory("malformed or oversized page")
        if total is None:
            total = payload["total_count"]
        elif payload["total_count"] != total:
            raise IncompleteHistory("total_count changed during pagination")
        for row in page_rows:
            if not isinstance(row, dict) or type(row.get("id")) is not int or row["id"] <= 0:
                raise IncompleteHistory("malformed workflow run")
            if row["id"] in seen:
                raise IncompleteHistory("duplicate run id across visible pages")
            seen.add(row["id"])
            rows.append(row)
        if len(rows) > total:
            raise IncompleteHistory("visible rows exceed total_count")
        if len(rows) == total:
            if page_rows and len(page_rows) == page_size:
                # A full page at the claimed total is complete; no further page is needed.
                return {"total_count": total, "workflow_runs": rows, "pages_read": page_number}
            return {"total_count": total, "workflow_runs": rows, "pages_read": page_number}
        if len(page_rows) < page_size:
            raise IncompleteHistory("short page before total_count was reached")
    raise IncompleteHistory("page limit or supplied history ended before total_count")
