# Geometric image correspondence before MAP01 stopping transfer

Decision: **PASS_GEOMETRIC_IMAGE_CORRESPONDENCE_SCOPED**.

Issue #738. Immutable publication BASE `a4538c1edcaa8fb6a9305c303fa76c70561ffed9`. This is a deterministic synthetic horizontal-registration mechanism study, not fresh MAP01 evidence and not a reinterpretation of #710.

## One-factor question

The exact same generated reference/current image pairs were evaluated by (A) raw RGB MAE at zero displacement with threshold `<=0.035` and (B) bounded grayscale normalized cross-correlation over integer horizontal shifts `[-12,+12]`, with frozen confidence gates NCC>=0.80 and best-minus-second>=0.03. The independent authored geometric goal is `abs(shift)<=2 px`.

## Container-first method

- `py_compile`: PASS
- excluded-seed mechanics tests: **7/7 PASS**
- formal rows before freeze: 0
- formal runner: **1 invocation**
- formal reruns: **0**
- `verify.py`: **PASS_VERIFY**
- post-result frozen-source SHA-256 recheck: **7/7 exact**

Formal fixture: 160x96 deterministic RGB textures; frozen integer horizontal shifts; brightness gain/offset, bounded animated rectangle, and sparse deterministic noise as nuisance. Correspondence code receives image arrays only. Authored shift is scorer-only.

## First result

All six frozen gates are true.

Raw MAE false mismatches while geometric candidate was correct:
- `aligned_brightness`: shift 0, MAE 0.06831, NCC shift 0.
- `aligned_patch`: shift 0, MAE 0.04531, NCC shift 0.
- `near_goal_plus2`: shift +2, MAE 0.16343, NCC shift +2.

All eight identifiable shifted-scene cases were recovered with **0 px error** in this block and exact goal/non-goal disposition. The +10 px brightness+patch case remained identified at NCC 0.93486.

Controls:
- unrelated texture: best NCC 0.29371 -> `UNKNOWN`, not falsely aligned.
- low-texture constant image: no valid normalized correlation -> `UNKNOWN`; raw MAE alone would call it matched, illustrating that zero pixel difference does not make the geometric estimator invent identity evidence.

## Interpretation

This fixture demonstrates only that an explicit bounded geometric correspondence signal can separate horizontal displacement from some photometric/local-animation nuisance that defeats an unregistered raw-MAE proxy. It does **not** establish that horizontal image shift corresponds reliably to MAP01 yaw under perspective, parallax, dynamic actors, weapon bob, occlusion or native capture artifacts.

The correct next rung after retention is a separately frozen fresh MAP01 transfer of the *unchanged* estimator with an independent scorer. Do not retune #710 or reuse its unretained formal PNGs by assumption.

## Integrity

Full result SHA-256: `a65fbb5c53762d4376cc1cc23594a849f0b2fad3f560befb919e109130f0fe9d`. Exact measured source, cases, plan, freeze, environment, formal log, full result, verifier output and post-result rehash are retained in the deterministic evidence archive.
