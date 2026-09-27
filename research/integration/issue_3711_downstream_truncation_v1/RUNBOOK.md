# Reproduction and handoff

The exact allocation-02 runner and auditor commands are retained in [formal-02/CONTAINER_RUN.md](formal-02/CONTAINER_RUN.md). They document the historical execution and are **not** authorization to repeat allocation 02 with the same identity.

For independent verification, an integration worker should:

1. Recompute the source, raw, request/report, and audit hashes from the committed bundle.
2. Run the corrected read-only evidence-binding audit from [audit-v2-successor-02/CONTAINER_RUN.md](audit-v2-successor-02/CONTAINER_RUN.md) with the source and evidence mounts read-only.
3. If repeating the experiment itself, create a distinct successor path and allocation identity, preregister new H/T/D/C/U and a complete dependency/source freeze on Issue #3711, use a fresh output directory, and retain any STOP/FAIL unchanged. Do not relabel or overwrite formal-01/formal-02.

## Safe output setup for a new successor

The committed `formal-02/` tree is evidence, never a writable container output. Do not invoke the allocation-02 runner or auditor with a different output path: their source hashes and allocation identity are frozen. A successor needs its own reviewed runner/auditor, preregistration, and source/dependency freeze before execution.

For a successor, create a unique allocation identity and an empty host output directory outside the repository evidence tree; verify emptiness before mounting it:

```sh
allocation="issue3711-downstream-truncation-successor-$(date +%Y%m%d-%H%M%S)"
output="$(mktemp -d "${TMPDIR:-/tmp}/${allocation}.XXXXXX")"
test -z "$(find "$output" -mindepth 1 -print -quit)"
```

Adapt the historical container invocation only after freezing the successor's own commands. Bind the new output directory at `/out`; keep source and prior evidence mounts read-only, and write new artifacts under a distinct successor evidence path only after the run and independent audit. The historical container command documents allocation 02; it is not a rerun recipe.

Scope to recheck: the CLI producer reports a full write and exit code 0, while a synthetic downstream sink truncates delivery and a JSON parser rejects it. The retained `attempt-status` recovery is read-only. Whether actual integration callers reject malformed stdout rather than trusting only process exit status remains open.
