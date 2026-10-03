# Ordered event-prefix successor — #6809 A04

**Status:** preregistered; formal candidate and auditor have not yet run.

This is a new, narrowly scoped successor experiment under [Issue #6809](https://github.com/Unjuno/agent-interface/issues/6809). It preserves the earlier #6689 and #6809/#6812 results and asks a different question from the retained five terminal snapshots: does the classifier retain the right obligations at every ordered event prefix, rather than inferring history from the final snapshot?

## H / T / D / C / U

- **H:** A source-derived, order-sensitive prefix evaluator will preserve every still-pending mandatory obligation after an early negative, permit a complete mandatory negative without waiting on an unrelated optional source, and refuse a positive until the declared generation frontier is sealed.
- **T:** Allocation `PREFIX-STABILITY-6689-ORDERED-PREFIXES-A04-WSLC-20261003-01`. Freeze four combinations of two mandatory result values (`fail`/`pass`) and all six orders of the two result events and generation-seal event. Emit the initial state and every prefix: 24 traces, 96 rows. A separate raw-only auditor reconstructs the trace and prefix set from `input.json`. Candidate and auditor each run exactly once in separate WSLc 3.0.1.0 containers using the cached pinned Python image, no network, one requested CPU, read-only package/input and a distinct writable output mount. Six corruption controls are rejected by the independent auditor. No retries.
- **D:** `PASS_METHOD_SCOPED` only if all 24 ordered traces and 96 prefixes appear exactly once and are independently reconstructed; incomplete mandatory vectors remain unresolved with every missing obligation listed, including after a decisive failure and generation seal; a complete mandatory failure finalizes while the unrelated optional source is open; all-pass remains unresolved before seal and finalizes only after seal; mutually exclusive disposition counts remain separate from derived prefix metrics; all six frozen mutations are rejected. Otherwise retain the first cause-specific FAIL/STOP without retry.
- **C:** Authored deterministic traces do not establish completeness of a live verifier's evidence vocabulary, event delivery, or future-event semantics.
- **U:** No live verifier/runtime, GUI/action safety, model, latency, product, migration-speed, or general memory/OOM claim. This tests WSLc execution for this bounded CPU workload only. Requested memory is not treated as an enforced limit.

## Frozen runtime and execution boundary

- Base main: `10fba1d3c9aa0a6fbf39983cdcda099a10df497c`
- Branch: `research/prefix-stability-6689-ordered-prefixes-a04-20261003`
- Additive path: `research/analysis/prefix_stability_6689_ordered_prefixes_a04_20261003/`
- Image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64; cached)
- Container options: `--pull never --network none --cpus 1 --memory 512M`
- Source and input: read-only; candidate/audit results: separate writable directories.
- Candidate: one invocation. Auditor: one invocation only if the candidate exits 0 and its output is retained. Retries: zero.

The recorded cgroup/swap warning, if emitted, is retained verbatim. The requested 512M is not a hard-memory-limit or OOM-prevention claim. No Docker Engine, GUI, GPU, model, user data, or external effect is used.

## Frozen PowerShell commands

Run from the repository root after the freeze commit. The two output directories must be new and empty. Stop without retry if the candidate exits nonzero; invoke the auditor only after the candidate output is retained.

```powershell
$pkgPath = (Resolve-Path 'research/analysis/prefix_stability_6689_ordered_prefixes_a04_20261003').Path
$candidateOut = Join-Path $pkgPath 'formal/candidate'
$auditOut = Join-Path $pkgPath 'formal/audit'
$image = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
New-Item -ItemType Directory -Path $candidateOut | Out-Null
New-Item -ItemType Directory -Path $auditOut | Out-Null

wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M `
  --volume "${pkgPath}:/pkg:ro" --volume "${candidateOut}:/out:rw" --workdir /pkg `
  $image python -B /pkg/run_wslc.py candidate
if ($LASTEXITCODE -ne 0) { throw 'Candidate STOP/FAIL; do not retry or start auditor.' }

wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M `
  --volume "${pkgPath}:/pkg:ro" --volume "${candidateOut}:/input:ro" `
  --volume "${auditOut}:/out:rw" --workdir /pkg `
  $image python -B /pkg/run_wslc.py audit
```

See `FREEZE.json` for the byte-level preregistration, `RESULT.md` for the first formal outcome, and `REPORT.md` for the bounded interpretation.
