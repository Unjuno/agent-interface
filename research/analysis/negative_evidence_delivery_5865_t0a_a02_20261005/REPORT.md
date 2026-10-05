# Issue #5865 T0a A02 — execution record

## Disposition

**STOP / audit incomplete.** The frozen candidate completed once. The
independent auditor was invoked once and crashed in its mutation-control setup
with `KeyError: 'A'` at `audit_result.py:211`. It expected a route-keyed
`failure_snapshot`; the captured `failure_forward` record has
`failure_snapshot: {}`. No auditor result was created. No retries were made,
and no scientific PASS/FAIL is claimed.

## Preserved first output

- Candidate raw events: `run-01/events.jsonl`
- Candidate result summary: `run-01/results.json`
- SHA-256 values are recorded in `STOP.md`.
- Source/environment freeze: `FREEZE.json`, pinned to repository HEAD
  `19a6b723e58ccfd2b8265e88659589ef9223fcc9`.

The summaries show the intended policy contrasts in several cases (for
example, origin-bound reuse uses fewer producer attempts than no reuse in the
forward-cycle and exact-expiry cases). These are descriptive candidate output
only; the failed independent audit prevents interpreting them as validated
findings. The model is CPU-only and standard-library based. It does not test
GUI state, production cache behavior, real clocks, latency, or target effects.

## Next gate

Keep this allocation closed. If the hypothesis remains worth testing, define a
new allocation with an auditor that handles empty and populated failure
snapshots, tests each mutation control before freeze, and is independently
reviewed against the frozen candidate protocol. Do not retrofit this run or
rerun A02.
