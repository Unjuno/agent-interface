# Construction evidence (excluded from formal allocation)

All construction work used the local cached image ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`, Docker `--pull=never --network none --read-only`, one CPU, 2 GiB, 64 PIDs, and a read-only source mount. No model, provider, GUI, user data, or task input.

## Retained final construction invocation

Retained local output directory: `outputs/reader-memoryview-hash-4451-v2/` (final source/freeze verification is in a `construction-pre*` subdirectory).

- Runner: 6 resource rows + 2 contract workers; all exited 0.
- Corpus: 64 × 256 bytes, separate from formal corpus.
- Independent audit: `PASS_CONSTRUCTION`, 40 checks, errors=[].
- Copied-evidence mutations: 10/10 rejected; each has an explicit audit error and empty stderr.
- Injected timeout: a real 0.1-second child-process timeout produced paired fsync journal events and a readable `STOP_WORKER_TIMEOUT`; `PASS_DURABLE_TIMEOUT_STOP`.

The local output directory retains corpus, invocation manifest, raw summary, per-worker JSONL, fsync journal, independent audit, corruption-control results, and timeout-control result. Formal source did not change after this construction run except the freeze metadata, which is not imported by the runner or auditor.

## Construction harness failures preserved

Two earlier, nonformal control-harness attempts were not counted as successful controls:

1. The first mutation harness copied only the raw summary and corpus. The auditor then rejected all mutations because sidecar invocation/journal files were absent. This was a vacuous false positive; it exposed missing support-file copying.
2. The next harness copied sidecars but omitted `return r` from its mutation helper, writing JSON null. The auditor errored before producing an audit decision; all ten rows remained rejected=false.

Both were corrected before the final construction invocation. The final 10/10 result above uses the complete bundle and requires a structured `FAIL` audit with nonempty errors and empty stderr for every mutation. No formal worker ran during any construction attempt.

## Runtime-freeze mount STOP

After adding a pre-run check of the freeze digest and source hashes, the first invocation STOPped before creating an output directory or starting a worker: the container mount exposed only `source/`, while the verifier correctly expected the sibling `FREEZE.json`. The corrected invocation mounted the complete bundle at `/study:ro`. This local path/mount STOP is retained and no resource worker ran in that attempt.
