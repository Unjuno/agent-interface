# Construction censor-cap probe A01 (not formal T0)

Status: frozen before local candidate invocation. This is a one-case
implementation/construction probe for the right-censoring code path. It is
not the six-case T0, does not consume the #5085 allocation, and cannot be
promoted to scientific coverage or safety evidence.

## H/T/D/C/U

- **H:** With a right-censored synthetic train and holdout, the typed gate
  refuses training eligibility, the deliberately naive comparators consume
  all reported endpoint values (including censor caps), and every holdout
  coverage field becomes `NOT_ESTIMABLE_CENSORED_HOLDOUT` rather than scoring
  only selected uncensored rows.
- **T:** One deterministic case, seed 65761101, 2,000 train and 2,000 held-out
  exponential latent delays, right censoring at 3.5 with censor probability
  increasing with latent delay. Run candidate exactly once, then the
  independent raw-only auditor exactly once iff candidate exits 0. Retries 0.
- **D:** Construction PASS only if candidate and auditor exit 0, the expected
  gate disposition is `NOT_ESTIMABLE_CENSORED_ENDPOINT`, and all three
  comparator score records have null exceedance/interval/coverage fields plus
  `NOT_ESTIMABLE_CENSORED_HOLDOUT`.
- **C:** macOS host CPython, CPU-only; no container, model, GUI, OS input,
  network calls from the candidate, or observed release samples. A host
  construction pass does not satisfy the requested OrbStack formal T0.
- **U:** No estimator calibration, population coverage, multi-seed error
  rate, realistic censoring mechanism validation, physical release behavior,
  safety bound, or applicability beyond this fixture is established.

This case uses seed 65761101 and sizes 2,000/2,000, not any of the frozen
formal seeds 65761001–65761006 or sizes 4,000/4,000. Preserve candidate raw
output and auditor result verbatim. A failed run is terminal for this probe.
