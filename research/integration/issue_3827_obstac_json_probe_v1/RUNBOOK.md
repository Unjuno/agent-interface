# Obstac/OrbStack runbook

No standalone `obstac` CLI or MCP surface is exposed in this session. Repository precedents implement the Obstac-managed container contract through OrbStack's Docker context and the `OBSTAC_*` provenance environment variables. The runner checks all three values before emitting its one request.

## Construction only

After finalizing `FREEZE.json` and before the formal run:

```sh
python3 research/integration/issue_3827_obstac_json_probe_v1/src/launcher.py --construction
```

The construction namespace is separate and mock-only; its bridge never connects to Ollama. Verify its one-cell request/response plumbing and `OBSTAC_*` binding. Do not treat it as task/model evidence.

One earlier host-only launcher preflight failed before Docker/model invocation due to an incorrect script-root calculation; exact exception and correction status are retained in `construction/LAUNCHER_PREFLIGHT_STOP.md`. `construction-final/` is retained as a first mock run; its summary correctly records zero submitted calls, but its runner mislabeled a mock HTTP 200 as one completed model response. That reporting bug was fixed before formal execution, and the corrected final smoke is retained separately under `construction-final-02/`.

## Formal one-shot

Record the current head and full source freeze on Issue #3827 before execution. Verify that `formal/output/` and `formal/exchange/` are empty and that the exact frozen model digest is present. Then execute once:

```sh
python3 research/integration/issue_3827_obstac_json_probe_v1/src/launcher.py
```

The command uses OrbStack Docker with `--network none`, read-only `/task` and root filesystem, and a dedicated writable `/out` and `/exchange`. The host bridge accepts one runner-produced request and talks only to `127.0.0.1:11434`. HTTP errors are stored with status, headers and exact body bytes; nothing is retried.

## Independent audit

After retaining the result, stage the audit script, all frozen source files, freeze, preregistration, manifest, result, image, raw request/response and bridge summary under a fresh `audit/` directory. Run `src/audit.py` in the pinned image under OrbStack with `--network none`, source/evidence read-only and a separate writable output mount at `/out`. The auditor recomputes byte links and the narrow outcome without importing the runner or bridge.

Exact staging and audit command:

```sh
python3 research/integration/issue_3827_obstac_json_probe_v1/src/audit_launcher.py
```

The host audit launcher copies formal bytes without modifying them, verifies the pinned image ID, then runs only the frozen auditor in a network-none container.

## Prior allocation

The #3204 allocation-02 STOP and its bytes are retained in PR #3823. This issue and allocation do not edit or reinterpret those files.
