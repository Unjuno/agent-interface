"""Candidate root-confined host path mapper; not production code."""
from pathlib import Path
from urllib.parse import unquote


def resolve_host_path(value: str | None, repo: Path) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("path must be a string or null")
    root = repo.resolve(strict=True)
    if value in ("/repo", "/workspace"):
        return str(root)
    prefix = "/repo/" if value.startswith("/repo/") else "/workspace/" if value.startswith("/workspace/") else None
    if prefix is None:
        raise ValueError("absolute or unscoped host path rejected")
    rel = value[len(prefix):]
    decoded = rel
    for _ in range(3):
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    if "\\" in decoded or "\x00" in decoded:
        raise ValueError("ambiguous path separator or NUL")
    parts = decoded.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError("non-canonical or traversing path")
    candidate = (root / Path(*parts)).resolve(strict=True)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("resolved path escapes repository root") from exc
    return str(candidate)
