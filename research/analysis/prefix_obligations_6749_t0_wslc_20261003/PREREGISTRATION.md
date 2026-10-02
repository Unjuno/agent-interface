# Issue #6749 successor T0 — prefix obligations and disjoint metrics

Status: construction passed; formal allocation not yet invoked. This package is additive to #6689. The #6689 T0 records and #6704/#6706 artifacts remain byte-unchanged and are not rerun or pooled.

## H / T / D / C / U

**H.** In this finite append-only evidence contract, every source-current decisive mandatory FAIL remains a stable-negative disposition if every legal completion preserves failure, while every still-uncompleted mandatory check and source-frontier obligation remains visible. Disposition-class counts can be kept disjoint from derived early-finalization prefix metrics, and an independent raw-only oracle rejects violations of both rules.

**T.** Enumerate all legal interleavings and every prefix of a deterministic finite model with two independently arriving mandatory PASS/FAIL checks, one immutable CURRENT/INVALID generation event, and an optional stream with exactly three ordered paths: clear→complete, clear→conflict, clear→timeout-without-completion. Each optional path is internally ordered; its events interleave with both mandatory arrivals and the generation event. Candidate emits ordered-prefix rows, observed state, disposition, pending obligations, a disposition-only histogram, and separately keyed early-finalization metrics. Auditor independently enumerates its contract directly from this specification; it imports no candidate module or candidate helper. Five in-memory corruptions must be rejected: suppress an uncompleted mandatory check after stable FAIL, mix an early metric into disposition counts, forge optional completion, relabel INVALID as CURRENT, and treat timeout as COMPLETE. Construction tests are pre-freeze only. Formal allocation is one candidate invocation and, only on candidate exit 0, one separate raw-only auditor invocation; no retries or tuning.

**D.** `PASS_METHOD_SCOPED` only if candidate and auditor agree row-for-row over all legal interleavings/prefixes; every current-generation decisive FAIL is stable-negative without erasing pending checks/frontiers; PASS appears only after both mandatory PASS results, CURRENT generation, and explicit optional COMPLETE; conflict, timeout, or missing completion never yields PASS; disposition counts contain only dispositions and early metrics are separate; all five mutations are rejected. Any discrepancy is `FAIL_METHOD` or `FAIL_AUDIT`; an ambiguous continuation rule is `HOLD`. No authority or external effect is exercised.

**C.** The authored finite model omits corrections, source semantics beyond its event grammar, scheduler timing, GUI freshness, verifier truth, and useful latency. A richer certificate may add no value over a partial-verdict ladder or wait-for-all. This is structural enumeration, not a performance experiment.

**U.** No inference about live-system correctness, action authority/safety, real-world benefit, user behavior, or general asynchronous systems. Stability is not truth, freshness, or authorization.

## Frozen execution boundary

- Allocation: `PREFIX-OBLIGATIONS-6749-T0-WSLC-20261003-A01`; candidate=1, auditor=1 iff candidate exits 0, formal retries=0.
- Main base: `25532de0bf5dca01901150eb2ea0799f86ff4c56`; branch: `research/6749-prefix-obligations-t0-wslc-20261003`; additive path: `research/analysis/prefix_obligations_6749_t0_wslc_20261003/`.
- Environment amendment: Issue #6749 initially named OrbStack. This successor uses Microsoft WSLc 3.0.1.0, as explicitly authorized by the user. The experiment contract, event model, one-shot gates, and no-network restriction are unchanged; this is not a claim that the engines are equivalent.
- Runtime base: already-cached `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, linux/amd64, CPython 3.12.15. Pull never, network none, CPU=1, requested memory=512 MiB, UID/GID 65532. WSLc warns cgroup/swap enforcement is unavailable; no hard memory-limit claim is made.
- Candidate image includes only `candidate.py` and `contract.py`; auditor image contains only `audit.py`, with raw passed read-only as input. Source bind mounts are read-only; formal result directories are writable. Each formal container has a unique name. No other containers/images are inspected, stopped, removed, or changed.
- Recheck running-container inventory immediately before each formal invocation. Output destinations must be absent. Preserve command/stdout/stderr/exit/hash receipts. Never rerun either formal executable after invocation, regardless of result.
- No packages, network, model/provider, GPU, GUI, task/user data, runtime edits, native input, or external effect.

The candidate-side contract implementation also orders optional-path events internally, and the independent implementation reconstructs that rule separately. The two check arrivals and generation event can occur in every ordering consistent with that optional-path order.
