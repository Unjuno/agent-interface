# T1 attempt-01 archival note

This directory preserves the immutable pre-run stop for allocation
`issue5665-failure-mode-yield-t1-20261001-01`. The attempt stopped during the
source-hash preflight: runner and auditor invocations were both zero, and no
raw output was created. The machine-readable original is retained at
`results/t1-host-01/STOP.json`.

This is not a failed scientific run and not a method result. The corrected
successor allocation `issue5665-failure-mode-yield-t1-20261001-02` is separately
reported under `unseen_failure_mode_yield_5665_t1_v2/`; its scoped method result
does not overwrite or change this STOP. The v1 runner and auditor source blobs
are byte-identical to the v2 sources on current main
(`eab198a005ab90d19a1e4b211ec315563684b6ce` and
`c8de1110855c0886b142ec0400677120b9f6a216`). The original complete source tip,
including its exact frozen manifests, remains recoverable at tag
`archive/recovered/5665-t1-attempt01-source-stop-original-20261002`.
