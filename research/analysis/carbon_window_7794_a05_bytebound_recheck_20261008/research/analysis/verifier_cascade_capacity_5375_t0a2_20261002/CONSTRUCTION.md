# Construction record

Before freeze, six construction tests passed on host CPython 3.14.5. The finite candidate/auditor smoke reconstructed 270 rows across 9 groups with `PASS_METHOD_AND_HYPOTHESIS_SCOPED`. The tests verify exact group/horizon count, per-tick joint capacity accounting, intended synthetic contrast, and independent auditor rejection of planted joint-capacity, queue-conservation, and authority mutations.

The construction output is not the formal result. The formal candidate and auditor were invoked separately once each after `FREEZE.json`; their raw output and hashes are retained under `results/`.
