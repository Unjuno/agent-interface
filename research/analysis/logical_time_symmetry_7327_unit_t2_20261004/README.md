# Logical-time unit-representation T2 — Issue #7327

T2 is a new successor allocation after T1 stopped before candidate output because its frozen top-level `reference_period` did not match the candidate scenario schema. T1 source and failure record remain unchanged. T2 places `reference_period` in every scenario and uses a distinct additive path.

The scoped first result is summarized in [REPORT.md](REPORT.md); detailed commands and limitations are in [RESULT.md](RESULT.md), with exact source and run identity in [RUN.json](RUN.json).

## H/T/D/C/U

- **H:** Explicit seconds and milliseconds encodings of each complete schedule, including the per-scenario reference period and all disturbance timestamps, produce byte-distinct raw inputs but exactly equal normalized event/state/held/release traces.
- **T:** Six deterministic schedules, eight time fields, exact `Fraction` arithmetic, frozen event tie order, one candidate and one independent raw-only auditor, four corruption controls. Construction preflight is separate and excluded. Formal candidate once, formal auditor once, no retries.
- **D:** `PASS_UNIT_REPRESENTATION_SCOPED` requires all six pairs to differ in source encoding, every field including reference period and every event timestamp to scale exactly, canonical traces to match, and all four corruptions to be rejected. Otherwise preserve FAIL/STOP and do not retry.
- **C:** This tests only a finite synthetic exact-time representation; it cannot establish a complete physical model, live GUI/control equivalence, quantization, asynchronous timing, or operational safety.
- **U:** Whether a genuine second-unit representation is behaviorally invariant for this declared model.

## Reproduction and runtime

OrbStack cannot inspect the required cached Python image because the local containerd blob lookup returns `operation not supported`; no image pull/retry will be attempted. Issue #7327 allows this optional CPU-only rung to run on the host when no eligible container is available. This uses Python standard library only, no GUI/model/input/network.

After freeze, candidate and auditor commands are:

```sh
python3 candidate.py spec.json output/candidate.raw.json
python3 audit.py spec.json output/candidate.raw.json output/audit.receipt.json
```

The separate preflight outputs are not formal allocation evidence.
