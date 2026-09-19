from __future__ import annotations

from typing import Any


def audit_captures(first: list[dict[str, Any]], second: list[dict[str, Any]], required_apps: set[str]) -> dict[str, Any]:
    missing_apps = sorted(required_apps - {str(row.get('app', '')) for row in first + second})
    missing_fields: set[str] = set()
    rows = first + second
    for row in rows:
        for field in ('window_id', 'pid', 'title', 'wm_class'):
            value = row.get(field)
            if value in (None, '', 0) or (field in {'window_id', 'pid'} and (not isinstance(value, int) or value <= 0)):
                missing_fields.add(field)
    stable = first == second
    pairs = [(row.get('window_id'), row.get('pid')) for row in first]
    distinct = len(pairs) == len(set(pairs)) and len(pairs) == len(first)
    complete = not missing_apps and not missing_fields and stable and distinct
    return {'decision': 'PASS_IDENTITY_READINESS' if complete else 'HOLD_IDENTITY_DISCOVERY', 'missing_apps': missing_apps, 'missing_fields': sorted(missing_fields), 'stable': stable, 'distinct_window_pid': distinct}
