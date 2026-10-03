# Begun-execution cancellation release boundary — Issue #6864

**GAP_REPRODUCED_SCOPED / PASS_CANDIDATE_SCOPED.** The frozen main kernel accepts
a verified empty release observed before the accepted execution begin when
`RequestLifecycle.stop()` cancels that command. In the complete declared finite
matrix, the baseline accepts eight stale post-begin cancellations; the isolated
candidate accepts zero. This is ordinary sequential API construction evidence,
not a formal/live allocation or proof of physical input release.

Source base: `11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`. Worker/chat:
`01a0ff52-93c2-7272-9fbc-2d01287bc6aa`; policy FINAL-v5; parent
[Issue #6864](https://github.com/Unjuno/agent-interface/issues/6864).
Branch: `research/kernel-receipt-boundary-20261003-01a0ff52`.

## H / T / D / C / U

- H: a release lower bound tied to the first accepted begin closes the specific
  stale-snapshot cancellation gap.
- T: exact copied kernel bytes; 12 lifecycle histories, eight release timestamps,
  three supplied receipt kinds and one missing-receipt case per history. Each
  arm executes 300 rows. A separate raw-only oracle reconstructs all identities,
  before/after state, acceptance and release claims without importing the kernel
  or probe. Five corruption controls and three implementation mutations test the
  evidence and behavioral checks.
- D: baseline must show the gap; candidate must reject every stale post-begin
  cancellation without lifecycle mutation, accept equality/later empty verified
  release, and preserve missing/unverified/held-input and terminal boundaries.
  The finite candidate and oracle match in all 300 rows.
- C: all timestamps are authored values in one synthetic clock. Valid
  authorization without an accepted begin retains its original cancellation
  semantics. Completed execution already has its own release receipt; this
  package does not replace that evidence or its validation.
- U: no backend signature/behavior, clock provenance, OS input, concurrency,
  end-to-end task, latency, benefit or product correctness is established.
  Mutable public lifecycle fields and untrusted receipt producers remain outside
  this construction's trusted sequential API assumptions.

## Minimal candidate and ownership

`candidate_lifecycle.py.txt` adds an optional first-accepted-begin timestamp and
refuses older release observations in the active cancellation path. It updates
that timestamp only after an accepted begin. Rejected begins leave it unset;
the existing duplicate-begin behavior cannot move it later. The separate
#6852/#6853 repair should reject that duplicate begin altogether.

**No shared runtime source is changed.** All executable verification helpers
are explicit entry points in this additive result package. The copied kernel
and candidate are `.txt` evidence; no workflow or automatic test-discovery entry
is added. `probe.py` reconstructs temporary independent packages only when
explicitly called. Integration of a runtime repair must coordinate with #6852's
lifecycle owner and #6855's execution-release owner and obtain FINAL-v5 review.
Neither the Issue nor this package is a merge approval.

## Results and repairs

- Test-first baseline: five methods, four expected failing stale-release
  subtests (`ContractError` was not raised); retained log and exit code 1.
- Isolated candidate: five regression methods pass; retained original kernel
  suite passes 18/18 against both baseline and isolated candidate.
- Raw-only audit: baseline 300 rows / eight stale acceptances; candidate 300 rows
  / zero stale acceptances; both independent reconstruction audits have no errors.
- Audit controls: unchanged raw passes; missing row, duplicate row, fabricated
  stale acceptance, refusal-state mutation and boolean timestamp each reject.
- Implementation mutations: removing the lower bound produces four assertion
  failures; rejecting equality and overwriting the first begin each produce one
  expected `ContractError` in a required-success control. All three are detected.
- The first mutation harness failed before tests because a dynamically loaded
  dataclass module was absent from `sys.modules`. That first exit/log is retained.
  After module registration, an overly restrictive classifier rejected the two
  expected contract-error mutation detections. That first classifier output is
  retained separately. The final classifier records exception types and requires
  zero unrelated errors. These are ordinary helper repairs; no raw matrix was
  regenerated, result threshold changed or formal allocation retried.

The source freeze was reread after execution: all original kernel and pinned
candidate/probe/oracle/test source hashes match. `logs/*.receipt.json` records
the actual commands, start/end UTC and child exit codes. The wrapper's own exit
is never substituted for the child regression failure.

## Reproduce

From the repository root with standard-library Python 3.12+ (executed here on
macOS arm64 Python 3.14.5):

```bash
P=runtime/results/kernel-cancel-release-01a0ff52
python3 -B "$P/check_candidate.py" -v  # expected baseline failure
CANCEL_TEST_MODE=candidate python3 -B "$P/check_candidate.py" -v
python3 -B "$P/check_kernel.py"
python3 -B "$P/audit.py" baseline "$P/baseline.raw.json"
python3 -B "$P/audit.py" candidate "$P/candidate.raw.json"
python3 -B "$P/check_audit.py" -v
python3 -B "$P/check_mutations.py"
```

The stored matrix can be independently audited without executing either
lifecycle. `probe.py baseline|candidate` regenerates a construction matrix to
stdout; redirect to a **new** output rather than overwrite the retained raw.
No Docker/OrbStack/WSLc, GPU/model/GUI/input or shared execution lock was used.
Hosted CI and mandatory main-integration gates are not claimed satisfied.

| Field | Japanese meaning | SI unit | Definition / range | Type |
|---|---|---|---|---|
| `execution_started_ns` | 最初に受理された実行開始時刻 | ns = 10^-9 s | 合成の共通時計、未開始時は None、受理時300 | optional nonnegative integer |
| `observed_ns` | 入力解放を観測した時刻 | ns = 10^-9 s | 同じ合成時計、0/199/200/299/300/301/700/800 | nonnegative integer |
| `release_verified` | 空の入力解放が検証済みという出力 | 1, dimensionless | true/false; rejection has no terminal outcome | boolean / null |

The nanosecond values describe relationships in authored fixtures, not measured
nanosecond precision or actual release latency.
