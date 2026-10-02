# Issue #6556 audit-validation successor

## H / T / D / C / U

- **H:** A strict successor auditor preserves the already-retained 50-row `METHOD_PASS_SCOPED` raw, but rejects malformed decision tokens and decision/oracle mismatches that the original auditor can count as ordinary refusals.
- **T:** Re-audit the immutable candidate raw from `retired_intention_cue_6556_t0_v1/formal_01_20261002/` with the successor auditor. Apply five in-memory raw corruptions: arbitrary decision token on a known-ineligible fence row; `UNKNOWN` instead of `REFUSE` for known retired lineage; `REFUSE` instead of `ADMIT` for an eligible fresh event; `REFUSE` instead of `UNKNOWN` when provenance is missing; and `UNKNOWN` for a non-fence policy. Do not change or rerun the original candidate, raw, report, or auditor.
- **D:** Scoped audit integrity passes only if the original raw still passes and every corruption is rejected with a diagnostic. No new scientific result is claimed.
- **C:** Strict token and policy-outcome validation should catch malformed records before they are counted as a refusal; fixture and oracle remain the stipulated finite synthetic source.
- **U:** This verifies only the retained synthetic output contract. It does not establish live event-source provenance, runtime safety, operating-system queue behavior, or human transfer.

Run locally with `python -m unittest -v test_auditor_v2` from this directory. This is a separate, additive audit-validation package. The historical #6556 result and its frozen source identities remain unchanged.
