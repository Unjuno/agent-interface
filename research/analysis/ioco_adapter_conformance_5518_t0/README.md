# Issue #5518 — adapter conformance T0

**Status:** synthetic finite-trace experiment; no adapter implementation or production ABI is changed.

## H / T / D / C / U

- **H:** An input-conditioned output-inclusion relation accepts a conforming adapter whose internal batch/cache/retry steps differ, rejects target, freshness, authority, and false-success outputs at their first forbidden prefix, and keeps explicit `UNKNOWN`/`QUIESCENT` distinct from missing output. Exact raw-trace equality is expected to reject the benign internal refactoring.
- **T:** Eight frozen finite traces against a hand-authored transition contract: direct and hidden-batch controls; target-switch, stale-evidence, unauthorized-admission, and false-success mutants; a delayed verifier with explicit UNKNOWN then bounded QUIESCENT; and a silent/missing-output case. Candidate runner and independent raw-only auditor execute in separate digest-pinned, network-disabled containers.
- **D:** PASS only if both conforming traces pass; all four forbidden-output traces return a finite first counterexample; delayed UNKNOWN/explicit QUIESCENT conform; missing output is UNKNOWN (never success); exact raw equality rejects the hidden implementation while visible input/output projections match; and all four auditor mutations are rejected. Any allowed safety mutation, control false-reject, or silence-to-success promotion is FAIL. Ambiguous contract policy is UNCERTAIN.
- **C:** This is a deliberately finite, deterministic, one-visible-output-per-input profile. The baseline compares instrumented raw traces including declared internal events; the proposed relation ignores only the explicit `internal` field. No timeout distribution is estimated.
- **U:** No GUI, real adapter, model, physical input, runtime task effect, full ioco conformance suite, probabilistic claim, cross-platform behavior, latency, or production ABI safety is tested. Results are only relative to this authored alphabet, contract, and fixtures.

## Frozen question and method

The contract state is `READY → FRESH → ADMITTED → RELEASED → PENDING → DONE`, with `STALE` reachable by explicit invalidation. Each input has exactly one declared transition for the current state and an allowed output set. The checker returns the shortest observed prefix at the first unspecified input or forbidden output. Internal implementation events are retained in the synthetic raw fixture but ignored by the candidate relation.

Quiescence policy is explicit: `QUIESCENT` is an output label accepted only after `QUIESCENCE_PROBE`; an empty output list is missing evidence and yields UNKNOWN. Neither a timeout nor a missing event can be promoted to semantic success.

Issue #5518's comparison with #5513 (metamorphic relations) and #5516 (observation-preserving equivalence) remains open: this experiment tests input-conditioned output inclusion, not relation generation or bisimulation.

## Reproduction

Host construction tests:

```sh
python -B -m unittest discover -s tests -t . -p 'test_*.py' -v
```

The frozen runner is invoked once by `.github/workflows/issue-5518-ioco-t0.yml` inside the pinned image recorded in `FREEZE.json`. The independent `audit.py` then consumes only the raw result. The PR check repeats only the raw audit; it never executes `run.py`. Frozen source checksums cover only files in `FREEZE.json`, so appending outputs does not invalidate the preregistered input manifest.

Raw outputs, execution status, manifests, exact hashes, and the audit outcome are retained in this directory after the first run. Do not rerun the frozen candidate or overwrite its outcome.
