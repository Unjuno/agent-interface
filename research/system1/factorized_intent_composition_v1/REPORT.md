# #4234 factorized intent composition result

Decision: **FAIL_REPRESENTATION_REGRESSION**.

Formal allocation `factorized-intent-composition-4234-20260923-01`: one fit per frozen arm, reruns/replacements/post-freeze tuning = 0/0/0. Independent audit passed with errors=[] and 8/8 copied-evidence corruptions rejected.

## Result

| metric | CATEGORICAL_ID | FACTORIZED_INTENT | frozen factorized gate |
|---|---:|---:|---:|
| held-out semantic accuracy | 0.490479 | 0.546631 | >=0.95 |
| exact both held-out intents/base | 0.284668 | 0.309082 | >=0.90 |
| held-out YIELD recall | 0.494565 | 0.725543 | >=0.98 |
| forbidden-effect proposal | 0.505435 | 0.274457 | <=0.01 |
| seen-intent control accuracy | 0.794434 | 0.653320 | >=0.97 |

Held-out accuracy advantage of factorized over categorical: 0.056152; frozen discriminator required >=0.15.

## Interpretation

The experiment does **not** establish that factorized semantics fail to transfer. The frozen factorized arm already fails the seen-intent regression prerequisite (0.6533 versus gate 0.97), and the categorical arm is also weak on seen controls (0.7944). Therefore the frozen 14→24→24→4 / 700-step delegate-training condition is not an adequate known-combination baseline for attributing held-out error specifically to representation.

The first outcome is retained as `FAIL_REPRESENTATION_REGRESSION`, not tuned into a transfer test. This narrows the next question: before another compositional-transfer allocation, a fresh successor would need to establish a representation-neutral **trainability/convergence precondition** on seen combinations without consuming held-out composition metrics. It must not reuse this allocation ID or change this result.

## Scope

Synthetic NumPy shadow task only. Six normalized state features, three authored binary intent factors, deterministic semantic teacher, no Astra/natural language, GUI/input, authority, model/provider API, network task, user data or application effect. The categorical OOV arm is a memorization discriminator, not a strongest-possible embedding baseline.

## H/T/D/C/U disposition

- **H:** factorized representation may enable unseen-combination transfer — **not resolved**, because the seen-control prerequisite failed.
- **T:** completed exactly as frozen: 4096 train bases ×6 seen intents; 2048 held-out bases ×2 unseen intents; 2048 control bases ×2 seen intents; one fit/arm.
- **D:** `FAIL_REPRESENTATION_REGRESSION` by frozen priority rule.
- **C:** optimizer/capacity/training schedule may dominate both arms; synthetic teacher may still be too nonlinear for this frozen training budget.
- **U:** transferability of a sufficiently trained factorized delegate remains unknown; no live or production inference follows.

## ERROR CHECK

- formal fits: 2 total (1 per arm)
- reruns/replacements/tuning: 0/0/0
- source hashes after formal: unchanged
- audit errors: []
- corruption controls rejected: 8/8
