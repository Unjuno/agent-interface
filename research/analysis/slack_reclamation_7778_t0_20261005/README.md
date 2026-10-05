# Issue #7778 T0 — demand-guarded slack reclamation

## H / T / D / C / U

**H.** On eligible one-CPU traces with a complete sporadic control-arrival
contract, a demand-guarded slack-stealing policy preserves every control
deadline and completes more optional service than a fixed replenishment server
when reserved slots would otherwise be idle.

**T.** Compare PRIORITY_ONLY, STATIC_RESERVATION (one control slot every four
ticks, idle reservations are wasted), and DEMAND_GUARDED_SLACK_STEAL. The latter
may use an otherwise idle slot for optional work only after exhaustively
checking all future control release sequences allowed by the frozen
single-processor envelope. Use new finite traces, exact integer-tick preemptive
jobs, and an independent exhaustive schedule oracle. Cover idle gaps,
replenishment-boundary bursts, exact demand boundaries, infeasible joint demand,
unknown WCET/non-preemptive models, invalid job classes, early replenishment,
double-spent slack, and omitted controls. No GUI, host scheduler, GPU, model, or
input is involved.

**D.** METHOD_PASS_SCOPED requires complete trace accounting; exact agreement
with an independent exhaustive oracle on hard feasibility and maximum optional
service; no missed hard deadline or capacity overrun on any eligible trace;
explicit UNKNOWN/HOLD on infeasible or incomplete models; and rejection of
every frozen malformed-input and raw-log mutation. H_PASS_SCOPED additionally
requires strictly more optional service than static reservation on the
predeclared positive-slack subset. Any eligible hard miss or unsupported claim
is FAIL_METHOD; malformed model/runtime evidence is HOLD_MODEL_MISMATCH.

**C.** Fixed reservation or simple priority may be equally good if control work
is frequent; conservative demand checks may spend more CPU than they recover;
overhead may consume reclaimed slack.

**U.** Finite synthetic, preemptive, single-processor integer-time model only.
This cannot establish Linux/WSL/cgroup timing, OS scheduling behavior, physical
input release, end-to-end control latency, or any runtime guarantee.

## Frozen protocol

- Allocation: UNJUNO-7778-SLACK-RECLAMATION-T0-20261005-01.
- Base: main 86a2694c6251c2d7df2f69dbea490ec037903ff7.
- Candidate, independent auditor, fixtures and decision gates are frozen by
  FREEZE.json and SHA256SUMS before formal generation.
- Runtime: digest-pinned Python 3.12.15 WSLc container, --pull never,
  network disabled, source read-only, separate output directory.
- One generator, candidate and auditor invocation; no retry or seed tuning.
- --memory 1g is a request only. The host has previously reported unavailable
  swap/cgroup memory limits; no memory enforcement is claimed.
- CPU-only by design; a GPU does not accelerate the exact finite schedule
  enumeration at this scale.

## Runtime and commands

The digest is
python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
(Python 3.12.15, linux/amd64). Construction checks are run before freeze.
Formal commands and one-shot receipts are retained in RUN.md.
