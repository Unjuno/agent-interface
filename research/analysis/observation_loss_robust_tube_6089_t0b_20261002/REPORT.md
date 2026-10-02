# Result — Issue #6089 T0b scheduled-observation erasure

**Disposition: `PASS_METHOD_SCOPED`** for the seven frozen finite one-dimensional cases and declared loss bounds only.

| Case | No-loss horizon | A: assumes delivery | B: release on absence | C: loss-robust horizon |
|---|---:|---|---|---:|
| k=0 / no loss | 5 | safe in fixture | fresh checkpoint, safe | 5 (exactly recovers base) |
| one missed checkpoint | 5 | `UNSAFE_OPTIMISTIC_EXTENSION` | released; safe in fixture | 4; safe for all declared miss counts |
| two-miss burst, k=2 | 5 | safe in this fixture | released; safe in fixture | 4; safe for all declared miss counts |
| delayed old generation | 5 | `UNSAFE_OPTIMISTIC_EXTENSION` | stale receipt treated as absent; released | 4; safe for all declared miss counts |
| target invalidated during wait | 5 | invalidated | YIELD | 0 / `YIELD_INVALIDATED_TARGET` |
| two misses with k=1 | 5 | `UNSAFE_OPTIMISTIC_EXTENSION` | released; safe in fixture | deadline stop; beyond-bound continuation is uncertified and stress is unsafe |
| loss bound unsupported | 5 | safe in this fixture | released; safe in fixture | 0 / `HOLD_LOSS_BOUND_UNSUPPORTED` |

The independent recursive auditor reported `PASS_METHOD_SCOPED`, 7 rows, errors `[]`. Construction tests passed 6/6, including five result-corruption controls. Candidate and auditor each ran once; retries 0.

## Interpretation and limits

In the planted one-miss fixture, assuming the scheduled observation arrived extends the old action across a forbidden prefix. Releasing when no fresh receipt arrives remains safe in that specific fixture. Policy C trades one horizon slot (5→4) for tolerance to the declared missing-checkpoint burst while keeping every in-bound state and release prefix safe. A stale-generation response counts as an erasure, not fresh evidence; target invalidation and unsupported bounds force YIELD. For k=0, C exactly matches the base no-loss selector.

This is synthetic exact enumeration only. The burst bound, disturbance envelope, observation cadence and release lag are stipulated, not measured. It proves neither that any real channel satisfies k nor that an OS/application can meet the assumed release delay. The beyond-bound continuation is explicitly outside the certificate. No live GUI/DOOM effect, controller benefit, safety guarantee, human-tempo gain, or authority to hold input is established. This does not close #59.

Raw candidate SHA-256: `63f2f8acc696130b0c2db10619dd32c513977e342a946115597e3797e511e528`. Raw audit SHA-256: `5929fefe3cce62c46c54aa79434654bfd175a5a16fa51fe6e429b2501c05ccfc`. Complete source/result checksums are in `SHA256SUMS`.
