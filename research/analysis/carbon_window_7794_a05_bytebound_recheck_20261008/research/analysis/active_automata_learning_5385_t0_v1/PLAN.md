# Issue #5385 — T0 bounded active lifecycle learning

## H / T / D / C / U

**H.** On a deterministic four-state lifecycle oracle with seven actions, a bounded active observation-table learner using membership and bounded equivalence queries will identify all four reachable, safety-distinguishable states within a fixed query budget, while a deliberately small hand-authored suite identifies fewer states. The learned model is an exploration artifact only; every candidate trace is checked against the safety oracle and no learned transition grants authority.

**T.** Freeze a pure-Python, no-dependency Mealy-style lifecycle oracle (`fresh`, `stale`, `half_open`, `comp_pending`) and an observation-table learner. Compare the learner to five fixed hand-authored traces. Use bounded equivalence queries over all action words of length 0–4, then independently audit a raw JSONL trace of the complete same bounded language (2,801 words). Run exactly one formal invocation in pinned `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, OrbStack context, network disabled, read-only root/source, one CPU, 256 MiB, 64 pids. Freeze source and hashes before invocation. No GUI/model/network/task input, and no rerun, replacement, tuning, or post-hoc source edits.

**D.** `PASS_ACTIVE_LEARNING_SCOPED` iff the learner infers all four reachable behavioral states, bounded equivalence returns no counterexample through depth 4, all 2,801 raw predicted output traces equal an independently reimplemented oracle, every `GRANTED` occurs only in `fresh`, all seven action-symbol outputs are recorded, the learner uses at most 500 uncached membership queries, the five-trace manual baseline identifies fewer than four states, and the independent audit plus mutation controls pass. Any missed state or counterexample is `FAIL_LEARNER_BOUNDARY`; any unsafe grant is `FAIL_AUTHORITY_INVARIANT`; provenance/schema disagreement is `STOP_PROVENANCE_OR_AUDIT`.

**C.** The apparent advantage may come from the oracle's deliberately chosen distinguishing actions and from giving the learner an exhaustive bounded equivalence oracle; the manual baseline is only five traces, not an optimized human test suite. A production interface may have nondeterminism, observation aliasing, unreachable states, hidden side effects, or expensive/non-resettable membership queries.

**U.** This first unit measures only a deterministic synthetic finite oracle. It does not establish real-interface discovery, query efficiency against a live GUI/API, strategic-agent behavior, model quality, latency/tokens, or safety certification. Bound depth 4 is finite conformance evidence, not equivalence over unbounded traces.

## Frozen artifacts and execution

- Candidate/oracle: `experiment.py`
- Raw-only independent auditor: `audit.py`
- Formal output: `raw/formal.jsonl`
- Audit output: `raw/audit.json`
- Exact one-shot commands and environment receipt: `EXECUTION.md`
- Source SHA-256 values are captured in `SOURCE_MANIFEST.md` before the formal run.

Formal allocation: `active-automata-5385-t0-orbstack-20260930-01` (one invocation maximum).
