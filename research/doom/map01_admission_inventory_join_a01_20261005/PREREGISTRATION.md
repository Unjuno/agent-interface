# Admission-derived key inventory join A01

## H / T / D / C / U

**H:** In the retained V39 event stream, per-key `input_admission` events, associated with their preceding hold-step context, enumerate exactly the key set in every later `keys_held` aggregate acknowledgement for that same step. Admissions with no matching acknowledgement must remain explicit and unpaired, including the canceled `Down` race.

**T:** Pin the 634-row raw V39 stream from source commit `c99d93a2c81945f0946173e48247bdd49e32a02a`. Reconstruct admission step context, compare each aggregate receipt's complete key set against the corresponding admitted-key set, and independently repeat from raw using backward context lookup. Do not infer per-key key-up or physical held duration.

**D:** `PASS_ADMISSION_INVENTORY_JOIN_SCOPED` iff the raw counts are 39 admissions / 28 aggregate receipts, all 28 receipt key sets exactly equal the reconstructed admissions for their step, no admission is duplicated or ambiguously scoped, and exactly one unmatched admission remains: `Down` at `cover-4` step 10, followed by cancellation. Any receipt/admission set mismatch yields `COUNTEREXAMPLE`; source or audit defects yield `HOLD`.

**C:** The event stream does not put id/step on each per-key admission; context is reconstructed from preceding `step_started` and lifecycle events. `keys_held` is a same-process aggregate acknowledgement, not per-key release telemetry or an independently authored foreign key. One historical run cannot establish completeness for a future producer or detect a lost `input_admission` and corresponding aggregate event together.

**U:** This tests whether the retained admission events can serve as an inventory for joining future per-key release telemetry. It does not establish physical key-up, task usefulness, recovery, live control efficacy, MAP01 progress, safety, latency benefit, or human tempo.

## Frozen source

- Source commit: `c99d93a2c81945f0946173e48247bdd49e32a02a`.
- Source path: `research/doom/results/v39-control-telemetry-gap-audit-20261004/events.jsonl`.
- Expected source SHA-256: `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
- Current repository main at selection: `109cedcf1fafc150e235c91141eb47bbc7396b43`.
- Candidate and auditor file hashes are frozen in `FREEZE.json` before execution.
