# Issue #5908 T1 — quality-diversity archive construction

**Result: `PASS_METHOD_SCOPED`** for synthetic trace-descriptor archival and planted-mechanism retention only. This is not a benchmark-validity, controller, or empirical discovery result.

The frozen pool had 12 candidates: eight admitted legal cases, two invalid-source/target cases, and two oracle-shortcut cases. Three selectors each used six evaluations. The independent auditor reconstructed all 18 calls, their exact selected IDs, descriptor cells, labels, and exclusions with zero errors. Both planted mechanisms were retained in distinct trace cells. No invalid or shortcut candidate was evaluated.

| Selector | Selected IDs | Planted mechanisms | Trace cells |
|---|---|---:|---:|
| Seeded uniform order | c02, c00, c03, c01, c05, c04 | 2 | 2 |
| Pairwise-factor | c00, c04, c06, c07, c01, c02 | 2 | 4 |
| Descriptor archive | c00, c04, c06, c07, c01, c02 | 2 | 4 |

Pairwise and descriptor-archive selected the identical cases; all methods found both planted mechanisms. Therefore this T1 supplies **no comparative discovery advantage** for QD over simpler selection. The archive retains distinct observed trace cells, but no authentic failure landscape, adaptive held-out discovery, strongest-elite benefit, or useful case correction was tested.

## H / T / D / C / U

- **H:** An outcome-descriptor archive can retain two planted, independently labeled mechanisms in distinct cells without exposing oracle labels to the selector; equal-budget simpler policies reveal whether this construction adds discovery value.
- **T:** Enumerate 12 fixed candidates (8 legal, 2 invalid, 2 shortcut), apply uniform-seeded, pairwise-factor, and descriptor-archive policies at six calls each, keep truth outside selector input, then independently reconstruct all selections, traces, labels, archive cells, and pre-admission exclusions. Nine construction and mutation tests ran before freeze; candidate and auditor each ran once after freeze.
- **D:** `PASS_METHOD_SCOPED`: archive represented both planted mechanisms in distinct cells, all 18 selected-call rows reconciled, invalid/shortcut cases were rejected, and corruption controls failed as expected. The matched pairwise baseline recovered the same two mechanisms in the same six cases, so no discovery advantage is claimed.
- **C:** The result is determined by the hand-authored pool and trace map; factor coverage may suffice; exhaustive enumeration may be simpler; the synthetic oracle may be wrong. Descriptors could encode the desired taxonomy.
- **U:** No authentic generator, GUI/controller, benchmark-validity, rare-hazard sensitivity, generalization, independent adjudicator of real failures, or T2 hidden-family claim. The selector policies are demonstrations over eight legal fixtures, not a validated search system.

## Provenance and limits

Freeze base `2106f20d61e4ef80cfcdbb2b694bbe10a07b454d`; source hashes in `FREEZE.json`; raw outputs and their SHA-256 are recorded in `RUN.json`. CPython 3.12 on host only. Docker Engine did not answer the bounded CLI version probe, so no container-isolation claim is made. No model, GUI, real controller, participant, networked runtime, or shared GPU was used. The earlier Issue #5908 `T0_HOLD_FORMAL_SUBSTRATE` remains unchanged.
