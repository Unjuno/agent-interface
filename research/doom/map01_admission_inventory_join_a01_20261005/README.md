# V39 admission-derived key inventory join A01

## Result

`PASS_ADMISSION_INVENTORY_JOIN_SCOPED`. On the frozen 634-row V39 trace, the candidate reconstructed 39 per-key admissions and 28 aggregate `keys_held` acknowledgements. Each of the 28 aggregate receipts has an exact key-set match with the admissions assigned to the same hold step; there are zero set mismatches. One admission (`Down`, `cover-4` step 10) has no aggregate receipt and remains unmatched after cancellation. The independent raw-only auditor independently reconstructed the full comparison and agrees with the candidate output.

This establishes a scoped way to derive the expected key set for aggregate-acknowledged hold steps from this event stream. Each `input_admission` row lacks its own `id` and `step`; both candidate and auditor recover context from event ordering around `step_started` and lifecycle events. This is not a runtime-authored foreign key, and a lost admission and matching aggregate receipt together would be invisible. The unmatched cancellation-racing `Down` event must remain `UNKNOWN` for acknowledged-held state and requires a separate partial-admission bound.

## Provenance and verification

- The exact raw stream is retrieved from source commit `c99d93a2c81945f0946173e48247bdd49e32a02a`; its SHA-256 is pinned in `FREEZE.json`.
- Candidate result is `candidate-output.json`; independent raw-only audit is `audit-output.json`.
- `python -m py_compile analyze_inventory.py audit_inventory.py` passed; `git diff --check` passed.
- `SHA256SUMS.txt` covers the frozen scripts, protocol, outputs, and report.

This is posthoc event-stream construction evidence only. It does not measure per-key key-up, physical occupancy, independently useful feedback, recovery, task effect, survival, MAP01 progress, safety, latency, or human tempo. It is not a new live allocation.
