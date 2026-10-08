# Issue #5370 T7 — formal result

**Disposition: `PASS_COMPOSITION_METHOD_SCOPED`.** The frozen candidate emitted 36 rows and the independent raw-only auditor reconstructed all 36 with zero errors. This is a small synthetic method result, not evidence about an operating-system scheduler, an Agent Interface runtime, GUI behavior, or user-visible latency.

## Outcome

The inversion subset had 7 deadline misses under `DEADLINE_ONLY` and 6 under `COMPOSED_BOUNDED_PI`; the unbounded negative control had 1. Thus the bounded composition improved this finite set by one missed deadline, while the deliberately unsafe control scored better and demonstrated why the result is not a general performance win.

The composed policy refused the cyclic wait graph, did not inherit from expired, forged, incomplete, or non-live claims, released boosts on cancellation, and drained resources. The first eligible medium-priority service after the configured cap occurred within the one-tick bound. The independent audit reported `errors: []` and no source-hash errors. Construction suite: 10/10 passed, including nine corruption controls.

## Formal allocation

- Allocation: `5370-COMPOSED-BOUNDED-PI-T7-20261002-01`; successor Issue #6723 to historical Issue #5370.
- Candidate and auditor each ran once in separate OrbStack Docker containers; zero formal retries. Raw output, audit receipt, exact Docker events, invocation/configuration metadata, and source freeze are retained alongside this report.
- Candidate raw SHA-256: `43b6d562c763ed78aecd9b3264838d4e2267b2bcf3c344306ba693ad9e761ed3`.
- Audit SHA-256: `0180d33bd4a7e5dc52482e7e66df887ee96e3513b924ed10c8ad07901b522b2c`.
- Both processes exited 0 with empty stdout and stderr. Docker was configured with no network, read-only root/source, 256 MiB memory, 32 PIDs, all capabilities dropped, and no-new-privileges. Although `--cpus=0.25`/`NanoCpus=250000000` was configured, inspect showed `CpuQuota=0` and `CpuPeriod=0`; no effective CPU limit is claimed.

See [`formal/RUN.json`](formal/RUN.json), [`formal/RAW.json`](formal/RAW.json), [`formal/AUDIT.json`](formal/AUDIT.json), [`formal/docker-events.jsonl`](formal/docker-events.jsonl), and [`FREEZE.json`](FREEZE.json). Reproduction contract and scope are in [`PROTOCOL.md`](PROTOCOL.md).

## Limits and lineage

The improvement is one case in a deterministic toy scheduler with logical time. It does not establish real contention, priority inheritance semantics in a production scheduler, fairness under workload, model-driven decisions, GUI integration, safety, or end-to-end responsiveness. Any later runtime experiment needs its own authorization, resource lane, preregistration, and evidence.

Historical #5370 T6 `STOP_PROTOCOL_DEVIATION` and its raw evidence are unchanged. This is a fresh successor and must not be used to overwrite or relabel that disposition.
