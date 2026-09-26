# Obstac/OrbStack runbook

The repository's Obstac contract is implemented through the OrbStack Docker context plus frozen `OBSTAC_*` values checked inside the container. The container has no network route; only a host-side bridge can contact `127.0.0.1:11434`.

## Construction only

After `FREEZE.json` is complete, run:

```sh
python3 research/integration/issue_3843_qwen_valid_png_probe_v1/src/launcher.py --construction
```

This uses an isolated mock namespace and makes zero Ollama requests. Confirm that the runner emits one request, the bridge returns a mock response, the image hash matches the filter-0 preregistration, and the `OBSTAC_*` values match the freeze. Construction is not model evidence.

## Formal one-shot

Record branch/head and freeze on Issue #3843 before execution. Confirm that `formal/output/` and `formal/exchange/` are empty and that the exact local Qwen digest is installed. Execute exactly once:

```sh
python3 research/integration/issue_3843_qwen_valid_png_probe_v1/src/launcher.py
```

There is a one-request budget. HTTP errors are retained with headers and exact body bytes. No retry or fallback is permitted.

## Independent audit

After preserving formal bytes, stage and audit them using:

```sh
python3 research/integration/issue_3843_qwen_valid_png_probe_v1/src/audit_launcher.py
```

The audit runs in the pinned linux/arm64 image under OrbStack with `--network none`, read-only source/evidence and a separate writable audit-output mount.
