# Issue #5318 — semantic serializability T0

Status: frozen before formal execution.

## H / T / D / C / U

**H.** On this finite fixture, semantic-footprint scheduling will retain a legal serial outcome (or explicitly defer/abort) for every pair, expose the write-skew counterexample admitted by raw parallel/coalesced execution, and permit more parallel cases than global serialization when operations are disjoint or have a trusted commutativity rule.

**T.** One deterministic simulator; six frozen two-proposal scenarios: disjoint writes, same-resource commutative increments, identical noncommutative assignments, write-skew cycle, unknown/incomplete footprint, and delayed irreversible effect. Compare `RAW_COALESCE`, `GLOBAL_SERIAL`, `SEMANTIC_SERIALIZABILITY`, `OPTIMISTIC_VALIDATE_COMMIT`, and `UNKNOWN_AS_CONFLICT`. Candidate emits one JSON object per scenario/policy. A separate stdlib auditor reconstructs all 30 rows from raw output without importing candidate code.

**D.** `PASS_METHOD_SCOPED` only if all rows reconstruct exactly; cycle/unknown cases never commit parallel effects under the guarded policies; all committed guarded results equal at least one legal serial execution; RAW_COALESCE retains a concrete counterexample or source-loss case; and semantic policy parallelizes the frozen disjoint and trusted-commutative cases while GLOBAL_SERIAL parallelizes none. Otherwise retain typed FAIL/STOP without tuning.

**C.** Finite integer state, deterministic ordering, and abstract effects. Policies receive the same proposals and initial state. The optimistic policy uses a reversible sandbox and aborts on validation conflict. CPU-only, no model, network, GUI, user data, external effects, or authority.

**U.** Does not validate extraction/truth of real footprints, commutativity certificates, external effect receipts, compensation, fairness, throughput, or runtime safety. No inference about arbitrary tools or GUI actions. Hidden overlap is conservatively represented as unknown, not magically inferred.

## Frozen environment / invocation

- Allocation: `semantic-serializability-5318-t0-20261001-01`
- Main base: `3d6ffc76d535309cf3820ed33cb9327354f03648`
- Branch: `research/semantic-serializability-5318-t0-20261001`
- Path: `research/analysis/semantic_serializability_5318_t0_v1/`
- Runtime: cached `python:3.12-slim`, immutable local image ID to be recorded before invocation; linux/amd64, `--network none`, 1 CPU, 256 MiB, 64 PIDs, read-only root/source.
- Construction: `python -B -m unittest -v test_simulator.py`; zero external calls.
- Formal: one container invocation, `python -B simulator.py`; retain stdout exactly.
- Audit: only after formal exit 0, one separate invocation, `python -B audit.py <raw-file>`.
- No retry, tuning, image pull, GPU, runtime integration, or external side effect.

