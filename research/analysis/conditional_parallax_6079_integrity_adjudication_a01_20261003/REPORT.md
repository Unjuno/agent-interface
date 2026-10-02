# #6079 parent T0 integrity adjudication A01

**Disposition: `HOLD_PARENT_FORMAL_PROMOTION`.** The raw visible corpus, truth sidecar, and retained candidate output are internally reconstructable, but the parent allocation did not meet its declared provenance/first-exposure gate. Its unqualified `PASS_CONDITIONAL_IDENTIFIABILITY_SCOPED` must not be relied on as a protocol-qualified pass. The original files, hashes, output, and reported disposition remain unchanged as historical evidence; this audit adds no candidate run.

## Raw reconstruction

This audit independently rebuilt the deterministic fixture bytes (without importing or invoking `candidate.run`), checked all nine pair joins and frame digests against the truth sidecar, re-derived target-minus-landmark centroid separations, and compared those values with the retained output. There were zero raw reconstruction errors: pairs 01–03 separated at 11, 11, and 12 px; pairs 04–09 had 0 px and `UNKNOWN`. The nine passive frame pairs were byte-identical. Thus the finite recorded output is reproducible from the delivered bytes.

The visual corpus exposes only **one landmark pixel per passive member frame**, not a visible multi-depth background field. This substantially narrows interpretation. The separate foreground-control A01 also demonstrated that changing a visually dominant pattern at the accepted landmark intensity can induce a false distinction while target pixels do not move.

## Protocol and audit defects

1. `FREEZE.json` expects `PREREG.md` SHA-256 `e78b67a3…`; the delivered bytes and current manifest are `d6a96771…`. The original expected bytes are not present in retained evidence. This adjudication does not recreate them or rewrite the freeze.
2. The parent construction test's `setUpClass` calls `candidate.run(cls.visible)` on `fixture.build()`'s deterministic nine-pair corpus. Independent regeneration exactly matches the formal visible input SHA. The candidate therefore saw the same deterministic cases before the claimed freeze, contrary to the preregistration's zero pre-freeze candidate exposure condition.
3. In the parent auditor, the swapped-truth-label and sham-mislabeled-as-movement mutations are passed in the `visible` argument slot instead of the `truth` slot. Their recorded rejections are not valid evidence for those two controls. A corrected, separately implemented raw-only audit here applies mutations to their proper slots and rejects all 4/4 controls, but that successor check does not retroactively repair the original formal audit.
4. The original result remains conditioned on an authored rigid-background fixture; together with the one-visible-landmark fact and the foreground counterexample, no generic real-scene parallax transfer is supported.

## Scope and disposition

The original candidate ran once; this allocation ran it zero times. No parent source or raw output was changed, no missing source bytes were reconstructed, and no formal allocation was retried. Raw reconstruction corroborates what the retained candidate emitted; it cannot establish that the pre-run freeze and first-exposure protocol were satisfied. Keep the parent numerical observations, but classify protocol-qualified promotion as HOLD. A future experiment requires a fresh successor corpus, source bytes frozen and verified before candidate exposure, genuinely visible multi-depth background, independently identified target/background layers, and a dominant-foreground/task-wrong correspondence negative control.
