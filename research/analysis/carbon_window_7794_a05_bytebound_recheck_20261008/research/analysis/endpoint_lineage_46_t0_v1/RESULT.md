# Result — Issue #46 T0 endpoint-lineage uncertainty

Disposition: **`PASS_ENDPOINT_LINEAGE_T0_SCOPED`**, a synthetic exact-arithmetic
method result only. It does not close #46's real two-domain instrumentation
objective, does not change any #59/MAP01 timing claim, and does not establish
calibrated clock uncertainty or real latency.

## Frozen source and execution

- Allocation: `ENDPOINT-LINEAGE-46-T0-20261001-01`.
- Source main: `0afd3e33b9da5e8ed4c8307609fec3264d4b93f2`; branch
  `research/endpoint-lineage-46-t0-20261001`, commit
  `417cb8b1a2f139982b58ce1da5558ee933c60d53`.
- Additive path: `research/analysis/endpoint_lineage_46_t0_v1/`.
- Freeze file binds fixture, reducer and independent-auditor SHA-256 before the
  primary. All six frozen files were read back from GitHub; their Git blob IDs
  matched the returned source blobs. `SHA256SUMS` verified before run.
- Candidate invoked once: `python3 research/analysis/endpoint_lineage_46_t0_v1/reducer.py`, exit 0.
- Independent auditor invoked once afterward:
  `python3 research/analysis/endpoint_lineage_46_t0_v1/audit_independent.py`, exit 0.
- No container, model, provider, network call from the experiment, GUI, X11,
  input, game, or shared runtime was used. This is exact finite standard-library
  arithmetic and no local Docker allocation was attempted.

## Exact retained output

Candidate stdout, byte-for-byte as retained in `candidate_stdout.json`:

```json
{"cases":[{"case":"shared_same_clock_boundary","expression":{"endpoint:t0":"-1","endpoint:t2":"1"},"joint":["19","21"],"naive_sum":["17","23"],"segments":[["9","12"],["8","11"]],"status":"NUMERIC"},{"case":"independent_middle_measurements","expression":{"endpoint:t0":"-1","endpoint:t1_left":"1","endpoint:t1_right":"-1","endpoint:t2":"1"},"joint":["17","23"],"naive_sum":["17","23"],"segments":[["9","12"],["8","11"]],"status":"NUMERIC"},{"case":"cross_clock_shared_affine_map","expression":{"endpoint:t0":"-1","endpoint:t2":"1"},"joint":["60","60"],"naive_sum":["39","81"],"segments":[["25","46"],["14","35"]],"status":"NUMERIC"},{"case":"incompatible_epoch","expression":{},"joint":null,"naive_sum":null,"segments":[],"status":"HOLD_INCOMPATIBLE_CLOCK"},{"case":"missing_endpoint","expression":{},"joint":null,"naive_sum":null,"segments":[],"status":"HOLD_MISSING_ENDPOINT"},{"A":["9","12"],"B":["10","14"],"case":"near_tie","nominal_center_winner":"A","reverse_order_witness":{"A":"12","B":"10"},"robust_decision":"UNRESOLVED_OVERLAP"}],"schema":"endpoint-lineage-46-t0-result-v1"}
```

Independent auditor stdout, retained as `audit_stdout.json`:

```json
{"audit":"PASS_ENDPOINT_LINEAGE_T0_SCOPED","cases":6,"errors":[],"mismatches":0,"scope":"synthetic exact finite method only","vertices_checked":36}
```

## Interpretation

For the same-clock reused middle ID, separately bounded segments sum naively to
`[17,23]`, while retaining identity cancels the middle endpoint and gives the
tight outer-endpoint total `[19,21]`. With two distinct middle measurement IDs,
the joint feasible interval remains `[17,23]`; the reducer does not assert that
the measurements are the same variable. Under one shared affine map across
the source-clock boundary, the segment-wise independent sum is `[39,81]`, but
the joint total is `[60,60]` because both rate and offset terms cancel at the
reused boundary. Incompatible epochs and absent endpoints return nonnumeric
HOLD dispositions.

For the synthetic comparison, nominal centers suggest A is faster (`10.5 <
12`), yet A's interval `[9,12]` overlaps B's `[10,14]`; feasible `A=12, B=10`
reverses that ranking. The reducer returns `UNRESOLVED_OVERLAP`, not a winner.

The independent auditor separately enumerated all 36 fixture-box vertices,
recomputed bounds and verified the near-tie reversal. It imports neither the
candidate reducer nor its helpers. These exact finite checks show only that the
method preserves the declared symbolic endpoint relations in these fixtures.
They do not show that a real system's endpoint IDs, clock epochs, affine model,
uncertainty bounds or semantic events are correct. Existing #4363 analysis and
direct outer-endpoint reports may be sufficient; no live measurement or
decision-value comparison was made.
