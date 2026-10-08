# A2 supervision-only freeze

A1 (`fifo2-seqkey-20260917-a1`) is retained `INCOMPLETE_SUPERVISION_TIMEOUT` and contributes zero rows.

A2 allocation: `fifo2-seqkey-20260917-a2`.
Fresh IDs: n01..n12. Scientific `model.py`, `worker.py`, `run_case.py`, `audit.py`, policies, arrival orders and gates are unchanged from the premeasurement source freeze. Only outer supervision changes: each `run_case.py` is invoked by a separate container-tool call. After all twelve first outcomes, frozen `assemble_a2.py` creates one aggregate and the original frozen `audit.py` is applied read-only.

No A1 ID rerun, no A1 pooling, no replacement, no threshold/source tuning.
