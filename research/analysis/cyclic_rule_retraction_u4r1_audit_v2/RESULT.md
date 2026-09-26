# Issue #4583 — `STOP_POSTHOC_AUDIT`

## Outcome

One raw-only OrbStack audit invocation completed against the immutable #4449
formal files. Source and raw provenance errors were **0**; the independent
least-model semantic errors were **0** across 256 rows; candidate/full-rebuild
mismatch rows were **0**. The newline-delimited condition digest matches the
actual raw bytes (`80469fe9…`); the original frozen digest matches the
escaped-backslash-n encoding (`0af2eedb…`). The audit also reconstructs 36
local-support false-retained claims and 200 blind-invalidation
false-removed claims.

The predeclared audit gate still fails: only **7/10** copied-evidence controls
were effective. Controls 6–8 targeted row 1, which is mask 1's NO_CHANGE row;
its `affected_cone`, `clear_and_rederive`, and `full_rebuild` are already empty.
The audit returns `STOP_POSTHOC_AUDIT`, not PASS. Inputs and the frozen audit
source are unchanged. This one audit invocation is consumed; no retry or
post-result code/target repair was made. Issue #4449 remains `STOP_AUDIT`; this
posthoc result cannot relabel that allocation.

## Exact inputs and execution

- Rows SHA-256: `c7b2f3dacf65a5d5c1799883ce037d8ffab039de10472e9efb2c4f238b0c5a0e`
- Conditions SHA-256: `80469fe9fd4434682ff00eb101417b053cd5b683edde7573043d3de1b24461a9`
- Frozen independent auditor SHA-256:
  `5da1fed96e313a5758a17d70b90076817ffc6283d8bb04a15fc3e9a49ddb63e5`
- Posthoc report SHA-256:
  `2ad80b1c2ac58aafedd5918725b3d819a8f3a75d971503d563b41e59dbbb285a`
- Container exit code: **2** (expected STOP result).

The isolated invocation used OrbStack image
`sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`,
Linux/arm64, CPython 3.12.14, network none, read-only root and source/raw
mounts, 1 CPU, 256 MiB, 32 PIDs, all capabilities dropped, and a separate
writable output mount. It ran only `audit.py`; the #4449 candidate/formal
runner was not invoked.

`results/posthoc01/REPORT.json` preserves the complete audit output. The
construction self-test is separately retained in [CONSTRUCTION.md](CONSTRUCTION.md).
