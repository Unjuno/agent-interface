# Issue #6689 T0 preregistration

## H / T / D / C / U

**H.** In a finite append-only verification contract, a prefix certificate can soundly finalize a negative claim before all optional sources close when (and only when) a current-generation decisive failure exists and that generation is sealed. It must not infer PASS from missing evidence, timeout, or an unclosed source.

**T.** Exhaustively enumerate a small finite state machine with three mandatory checks, two optional verifier sources, timeout markers, an explicit generation seal, and at most one pre-seal generation invalidation. For every reachable prefix state, enumerate all legal continuations to cutoff and compare their terminal outcomes with a prefix classifier. Compare the first sound finalizable state to wait-for-all-mandatory-and-sources-closed and deadline-only baselines. An independent raw-only auditor reconstructs the state graph and all continuation outcome sets. Controls: omit a mandatory failure, forge source closure, relabel stale-generation evidence as current, and treat timeout as source completion. No GUI, model, provider, task input, or actuation.

**D.** `PASS_METHOD_SCOPED` only if every stable certificate's outcome is invariant across all legal continuations; all open-frontier states remain non-final; negative results preserve pending obligations; no missing/timeout evidence yields PASS; the independent graph exactly matches every candidate state/outcome; and all four controls are rejected. A failure is any false-final result, suppressed mandatory obligation, or PASS without both explicit source-closed markers. HOLD if the continuation contract cannot be enumerated.

**C.** The finite contract is authored and may omit realistic source semantics. Wait-for-all may already be sufficient; the measured gain can be only an early-negative diagnostic, not user-visible completion.

**U.** No claim about live verifier correctness, latency, action safety, GUI state, or general asynchronous systems. Stability is not truth, freshness, or actuation authority.

## Frozen execution boundary

- Allocation: `PREFIX-STABILITY-6689-T0-20261002-01` (candidate 1, separate raw-only auditor 1 iff candidate exits 0, retries 0).
- Main base: `5f1cc2624469dea4624e98062423e928da083ca4`.
- Runtime: WSLc native container, local cached `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, linux/amd64, Python 3.12.15, pull never, network none, CPU 1, requested memory 512 MiB (kernel cgroup/swap enforcement unverified; no claim).
- Source and fixture hashes are in `FREEZE.json`. Source mount is read-only; only the new formal output directory is writable. Output paths must be absent before invocation.
- The WSLc running-container inventory was empty at preparation time. Recheck immediately before every invocation. Do not inspect/delete/stop any existing exited container or image.
- Candidate emits one raw JSON; auditor reads only that raw and frozen fixture, emits one audit JSON, and exercises the four corruptions in memory. Preserve exit/stdout/stderr receipts. Never rerun either formal executable.
