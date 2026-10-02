# Issue #6533 T0 result — frame-qualified collateral checks

**Disposition: `PASS_METHOD_SCOPED` for the frozen synthetic structured-state fixture only.** The one-shot candidate emitted 44 rows (11 traces × 4 policies); the separate auditor independently reconstructed all 44 from the raw before/after states and event manifests, with `errors=[]`. Candidate and auditor each ran once and exited 0. No retry occurred.

## Result

The full-state oracle found collateral changes in five cases: transitive formula write, alias write, hidden callback, external writer, and missing dependency edge. Both `TARGET_ONLY` and `STATIC_DIRECT` called all 11 rows `CLEAN`, so each missed all five planted collateral changes. `QUALIFIED_FRAME` matched the full-state outcome on all 11 cases and had no false-clean qualified result: it used the local frame on five eligible cases and charged a full-state fallback on the six cases with alias, incomplete callback/external/dependency coverage, stale generation, or non-durable state.

| Predeclared disjoint size | Full-state accounted bytes | Qualified-frame accounted bytes | Change |
|---|---:|---:|---:|
| 8 unrelated cells | 473 | 1,007 | 2.13× higher for frame |
| 64 unrelated cells | 2,881 | 1,009 | 65.0% lower |
| 256 unrelated cells | 11,137 | 1,007 | 91.0% lower |
| **Aggregate** | **14,491** | **3,023** | **79.1% lower** |

The preregistered aggregate cost gate passed by a wide margin, but the smallest fixture regressed because certificate/event-manifest overhead exceeded the avoided scan. This is a size-dependent method result, not a universal win. `accounted_bytes` is checker-level canonical bytes after snapshots are already materialized; it charges the certificate, event manifest, and full fallback, but excludes snapshot-file ingestion, application rendering, durable storage I/O, certificate issuance, and external audit. The reported read counts are virtual record accesses, not OS syscalls.

Wall-time medians over 31 in-process evaluations per row are descriptive only: on the three disjoint cases, full-state was 22.208/106.584/416.254 μs and qualified-frame was 17.500/17.833/17.458 μs. They are not end-to-end application latency or a production performance claim. A smaller checked footprint can still be slower when certificate work dominates.

## Formal execution

- Preregistration was posted on Issue #6533 before the run: [comment](https://github.com/Unjuno/agent-interface/issues/6533#issuecomment-5946266161).
- Frozen source commit: `d2fe1122163146263397e030859b14d309568dbb`; frozen base main: `648be0cb805a4cf44b9d8f6e1ad2a793b83bbf9a`.
- Allocation: `frame-qualified-collateral-6533-t0-20261002-01`, 2026-10-02 05:42:21–05:42:25 UTC.
- OrbStack Docker, Linux/arm64, pinned Python image `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; network disabled, read-only root/source, 1 CPU, 512 MiB and 64 PIDs configured, all capabilities dropped, no-new-privileges. `docker info` reported cgroup v2 and 16,819,609,600 bytes host memory; actual hard memory-limit enforcement was not independently established and is not claimed.
- Candidate container: `d64fd0cfd9a75cd861f0fa8cfc79c9b24d0006d41731a07d463947de56b67176`; auditor: `59f05ee30fa827544799eab60ed3a36659fb83b282bfca600544e36155420804`. Both were removed with `--rm`; post-run container-list readback found neither ID.
- Raw candidate, stdout/stderr, exit code, command and container receipt: [`results/allocation-01/`](results/allocation-01/). Independent audit: [`audit.json`](results/allocation-01/audit/audit.json). Exact host/image/command/limit receipts: [`RUN.json`](results/allocation-01/RUN.json).
- Frozen source hashes: [`SOURCE_SHA256SUMS`](SOURCE_SHA256SUMS). A complete post-run package checksum manifest is also retained at [`SHA256SUMS`](SHA256SUMS).

## Scope and limits

This is a synthetic, no-model method fixture. The “cells”, formula, aliases, callback, external writer, save state, generations, and event stream are authored data—not a real document application or observed GUI. The fixture's complete-state oracle makes these particular outcomes identifiable; it cannot establish that a real app's writers/dependency closure are complete, prevent a check-to-effect race, prove causal attribution, or support user-workspace safety. No runtime component was promoted and no GUI, product, or general safety claim follows. The Issue remains open for a separately authorized, independently qualified live-app transfer if warranted.

One pre-run command attempted the committed checksum manifest from the repository root with package-relative paths and therefore read no listed files; the formal run was unaffected. The manifest was subsequently checked from the package directory, with all source hashes passing. Two earlier construction-only audit/test issues are documented separately in [`CONSTRUCTION.md`](CONSTRUCTION.md); neither was a formal allocation outcome.
