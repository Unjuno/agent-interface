# Issue #5518 — adapter conformance T0

**Status:** synthetic finite-trace experiment; no adapter implementation or production ABI is changed.

## H / T / D / C / U

- **H:** An input-conditioned output-inclusion relation accepts a conforming adapter whose internal batch/cache/retry steps differ, rejects target, freshness, authority, and false-success outputs at their first forbidden prefix, and keeps explicit `UNKNOWN`/`QUIESCENT` distinct from missing output. Exact raw-trace equality is expected to reject the benign internal refactoring.
- **T:** Eight frozen finite traces against a hand-authored transition contract: direct and hidden-batch controls; target-switch, stale-evidence, unauthorized-admission, and false-success mutants; a delayed verifier with explicit UNKNOWN then bounded QUIESCENT; and a silent/missing-output case. Candidate runner and independent raw-only auditor execute in separate digest-pinned, network-disabled containers.
- **D:** PASS only if both conforming traces pass; all four forbidden-output traces return a finite first counterexample; delayed UNKNOWN/explicit QUIESCENT conform; missing output is UNKNOWN (never success); exact raw equality rejects the hidden implementation while visible input/output projections match; and all four auditor mutations are rejected. Any allowed safety mutation, control false-reject, or silence-to-success promotion is FAIL. Ambiguous contract policy is UNCERTAIN.
- **C:** This is a deliberately finite, deterministic, one-visible-output-per-input profile. The baseline compares instrumented raw traces including declared internal events; the proposed relation ignores only the explicit `internal` field. No timeout distribution is estimated.
- **U:** No GUI, real adapter, model, physical input, runtime task effect, full ioco conformance suite, probabilistic claim, cross-platform behavior, latency, or production ABI safety is tested. Results are only relative to this authored alphabet, contract, and fixtures.

## Frozen question and method

The contract state is 