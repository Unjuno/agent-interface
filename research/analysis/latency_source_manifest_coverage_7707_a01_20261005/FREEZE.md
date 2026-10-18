# A01 one-shot pre-execution freeze

- Successor Issue: #7707 (open), distinct source-manifest coverage hypothesis after closed #7501.
- Base `main` observed immediately before fixture generation: `e561b25b700680df4e6ffd2b92faf1dde1682ef7`; remote `git ls-remote` confirmed the same ref before freeze.
- Branch: `research/7501-manifest-coverage-a01-20261005`; path: `research/analysis/source_bound_conflict_cores_7501_manifest_coverage_a01_20261005/`.
- Runtime target: WSLc `3.0.1.0`, pinned cached image `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; candidate/auditor invocations use `--pull never`, `--network none`, one requested CPU, requested 512 MiB, source read-only at `/src`, output separate at `/out`. Requested memory is not treated as enforced absent verified cgroup evidence.
- Local WSLc `--version` and `run --help` return successfully. A read-only `list --all --format json` issued before this freeze is still pending after >60 seconds; multiple pre-existing WSLc list/image/stats requests were visible. They are not stopped or modified. Candidate invocation is one-shot and will not be retried if launch/result is uncertain.
- Construction: generator ran once before freeze; `python3 -m py_compile generate.py candidate.py audit.py` passed before freeze. Candidate and auditor formal counts are both 0 at freeze; retries 0.
- Formal order: invoke candidate exactly once. Invoke the independent auditor exactly once only after a confirmed candidate exit code 0. No model/GPU/GUI/live app/input or external effects.

## Frozen source/input hashes (SHA-256)

| File | SHA-256 |
|---|---|
| `README.md` | `fe3ee64889244484efa0705558c5b759d743553c130750c538633ea802475cdd` |
| `generate.py` | `fa4f806fb0e569e15b0fa2c8c876126858b037dc7126a63cef1ebba38d7d3660` |
| `candidate.py` | `f63b522ad7fef033840c1b4783293a15ef086469cdf0f97ff8f240bf969e5e13` |
| `audit.py` | `7e4032ab4d1bf7822a8c55a2c756cb10aacc0ec39c2556cec02b83d6bc55cfc2` |
| `INPUT.json` | `e386b6880f56e197fba9ad85e1c26c51a5e00f4c7145d55e9fdc91830566550d` |

## Frozen decision gates

`PASS_MANIFEST_COVERAGE_BOUNDARY` requires exact independent reconstruction of all ten rows; source digest/UTF-8 validity; one complete, non-overlapping span for every nonempty physical source line; no duplicate/empty clause IDs; omitted source line as `INCOMPLETE_MANIFEST`; malformed span/identity as `INVALID_MANIFEST`; declared unparseable clause as `UNKNOWN`; exact complete minimal cores for pair and two-MUS rows; all authority/dispatch flags false; and rejection of all six in-memory mutations. Any candidate/auditor/result mismatch is `FAIL_METHOD`; any terminal launch/image/artifact failure is `STOP_INFRA`. An invocation whose terminal/result cannot be authoritatively observed remains unresolved; it is never repeated.
