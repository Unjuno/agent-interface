# #4240 seen-intent trainability result

Decision: **FAIL_SEEN_INTENT_TRAINABILITY**.

Allocation `seen-intent-trainability-4240-20260923-01` executed exactly one SHORT700 fit and one LONG2800 fit after public source/gate freeze. Reruns/replacements/post-freeze tuning: 0/0/0. No forbidden held-out intent combination was generated or scored.

## Result

| metric | SHORT 700 | LONG 2800 | frozen LONG gate |
|---|---:|---:|---:|
| seen semantic accuracy | 0.731608 | 0.855794 | >=0.97 |
| exact all six intents/base | 0.246094 | 0.511719 | >=0.90 |
| YIELD recall | 0.655776 | 0.978090 | >=0.98 |
| forbidden-effect proposal | 0.344224 | 0.021910 | <=0.01 |

LONG accuracy improvement over SHORT = 0.124186, satisfying the frozen >=0.10 improvement discriminator, but LONG still fails the absolute competence gates. YIELD recall misses by about 0.00191 and forbidden-effect rate remains above the 0.01 ceiling; accuracy/exact-all-six miss substantially.

## Interpretation

Increasing only the training schedule materially improves the frozen factorized delegate, so #4234's 700-step failure was partly undertraining. However 2,800 steps still do not establish the required seen-combination competence. Therefore a fresh compositional-transfer experiment is **not authorized by this result**.

Do not continue a step-count sweep under this allocation. The remaining ambiguity is broader model/teacher fit: architecture capacity, optimization geometry, or the hand-authored teacher boundary may dominate. A useful successor must change a scientifically distinct factor and retain this negative, rather than trying 5,600/11,200 steps until PASS.

## Integrity

- parent #4234 factorized source SHA-256 matched exactly;
- held-out generated rows: 0;
- source hashes unchanged after formal;
- independent audit errors=[];
- copied-evidence corruption controls rejected 8/8;
- formal fits = 2 total, one per frozen schedule;
- reruns/replacements/tuning = 0/0/0.

Hashes:
- RESULT SHA-256 `e422d9b127b891d83a3caa7f0f5b388fd4013232eafa7fb0064b19607d0c635b`
- AUDIT SHA-256 `8d95be34c746dbdc3df9e4433512e7902f18780237f2f8e191cf92e7fec2e376`

## H/T/D/C/U disposition

- **H:** 700→2800 steps could establish seen-intent competence — **rejected at the frozen gate**.
- **T:** six seen intent combinations only, 4096 training bases, 2048 disjoint validation bases, same factorized input and 14→24→24→4 MLP, exactly two fits.
- **D:** `FAIL_SEEN_INTENT_TRAINABILITY`.
- **C:** additional optimization might help, but a blind step sweep would no longer isolate a meaningful mechanism; architecture/teacher complexity may be the real limiter.
- **U:** sufficiently trainable factorized delegation remains unresolved. No unseen-combination transfer, Astra, GUI/input, authority, task-effect, latency/token or production claim follows.

## ERROR CHECK

Formal held-out composition rows: 0. Formal fits: 2. Reruns: 0. Replacements: 0. Post-freeze tuning: 0. Audit errors: 0. Mutation controls rejected: 8/8.
