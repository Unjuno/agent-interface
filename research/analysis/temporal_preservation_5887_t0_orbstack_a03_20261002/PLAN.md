# Issue #5887 T0 successor A03 — timed and edge-sensitive trace preservation

Allocation: `TEMPORAL-PRESERVATION-5887-T0-ORB-A03-20261002-01`.
Base main: `4d3c8d3612e3c57f354f5e1be553ae4f5a7801e0`.
This is a distinct prospective allocation, superseding A02's pre-run STOP without modifying it. The earlier #5887 source-contract audit identified missing event-count and populated-timestamp deadline checks; this candidate explicitly includes both.

## H / T / D / C / U

**H.** In a finite typed trace, conservative timed projection preserves named temporal predicates only when it preserves the relevant source times, edge multiplicity, and authority generation. A lossy semantic-only or latest-state projection can change a deadline/count/provenance predicate. Missing timestamps must yield `UNKNOWN`, never a positive preservation certificate.

**T.** Deterministic standard-library model; five fixed traces × four projection arms. Traces cover exact timed stutter, repeated edge occurrences, a sole within-deadline witness followed by a late state, missing timestamp, and pixel-equal authority-generation change. Arms are identity, exact-row timed stutter collapse, semantic-only collapse (deliberately ignores time/edges), and latest-row-only. Candidate emits every input row, projected source indices, predicate values, and preservation classifications. A separately implemented raw-only auditor recomputes projections and predicates without importing candidate code. Construction tests are separate from formal execution. Candidate once, auditor once after candidate success, zero retries.

**D.** `PASS_METHOD_SCOPED` iff: (1) candidate/auditor agree on all 20 trace×arm rows; (2) exact-row timed stutter collapse preserves all decidable predicates in the benign-stutter trace; (3) semantic-only and latest-only projections are classified `NOT_PRESERVED` with replayable witnesses when they lose repeated-edge multiplicity, the only within-deadline witness, or an authority-generation transition; (4) all deadline predicates over a trace containing any missing timestamp return `UNKNOWN`; (5) no lossy projection is labeled preserved; and (6) each construction mutation (missing row, changed edge count, forged timestamp/classification) is rejected. Any false `PRESERVED` is `FAIL_METHOD`; missing/malformed evidence is `STOP`/`HOLD`, not scientific failure.

**C.** Exact-row equality may be too conservative; the finite projector set may miss other temporal operators; hand-authored predicates may encode the answer. Exact timed duplicates are safe here only because the frozen predicates are insensitive to duplicate copies at the same timestamp.

**U.** Synthetic finite traces only: no real capture coverage, continuous-time guarantee, clock-skew bound, hidden application state, runtime integration, GUI effect, action authority, latency benefit, or user-tempo claim.

## Freeze and execution

Image: local `python:3.12-slim`, linux/arm64; image identity and engine version are recorded in `RUN_RECORD.json` after formal execution. Candidate/auditor containers use `--network none`, read-only source, distinct fresh containers and separate writable output directory. No shared container is stopped, inspected for workload contents, or modified. Any source/main/path/runtime gate mismatch before first formal invocation is a typed pre-run STOP. Formal outputs are new files under `formal_01_20261002/`; no result tuning or retries.
