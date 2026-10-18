# Issue #7865 T0 A02 result

Disposition: `PASS_METHOD_SCOPED` for this finite method fixture only.

## Result

The post-freeze OrbStack run passed 7/7 tests. Its static independent oracle
reconstructed all 28 policy/history rows. The field-scoped policy accepted
the disjoint-body history and preserved body `y`; the whole-object guard
conservatively held because the object generation changed. The blind inverse
restored body `x`, losing the planted external write. Same-field, visible ABA,
replacement, unavailable-history, and out-of-order-history traces all held
under field-scoped compensation. The mutation checks rejected a false ABA
acceptance and a corrupted effect footprint. No result labels compensation as
literal rollback.

## Provenance and execution

- Source hashes, prior A01 failure, base main SHA, exact command, and image
  digest: `FREEZE_A02.json`.
- Formal command: `python -B -m unittest -v test_model_a02`, in
  `python:3.12.11-slim@sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f`
  (`linux/arm64`), on the already-running OrbStack engine.
- Exit 0; 7 tests passed in 0.002 s (container call wall time 0.519 s).
- Container flags: `--network none --cpus=1 --memory=1g --pids-limit=64`;
  measured cgroup values are retained in `A02_CONTAINER_LIMITS.txt`.
- Source mount was read-only. No image pull, model, GUI, real artifact,
  network, or external write occurred.
- Host pre-freeze gate: 7/7 tests passed in 0.001 s before A02 freeze.
- A01 remains `FAIL_HARNESS`; its original raw failure and source hashes are
  retained without modification. A02 is a new version, not a repaired A01
  result.

## Interpretation and limits

The fixture supports the narrow discriminator that field-level compare plus
field revision can retain a disjoint update that an object-generation guard
must reject, while refusing the enumerated conflicts. It does not establish
that real applications expose complete field footprints, ordered revisions,
stable object identities, or independent fields. Cross-field invariants,
external side effects, GUI semantics, live undo reliability, security, task
benefit, and product safety remain untested. The conservative whole-object
guard or no-auto-compensation may be preferable in applications without the
required evidence. No live allocation or integration claim follows.
