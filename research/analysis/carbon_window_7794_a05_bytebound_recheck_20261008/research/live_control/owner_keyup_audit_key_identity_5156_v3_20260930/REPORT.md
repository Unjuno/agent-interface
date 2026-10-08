# #5156 logical key-identity audit correction — T0 result

**Disposition: PASS_KEY_IDENTITY_AUDIT_T0_SYNTHETIC_ONLY.**

The exact three-row retained joined raw from PR #5467 was checked against its exact frozen expected inventory. Local Git blob hashes matched the four GitHub source blobs from PR #5415/#5467; the retained raw SHA-256 matches the published value `56842934b9f9b13fe0e52d515d31bd0c3d598cdb1cfa8b719dfb4c8ba463cbc2`.

The original completeness-v2 auditor accepted the pristine trace and returned `errors=[]` after either of the directed single-field corruptions: changing an explicit release's `key` from "a" to "b", and changing autonomous cleanup's `key` from `null` to "b". This reproduces the reported false-accept; it does not show the original producer raw was corrupt.

The additive candidate checks `key` against the independent expected inventory by exact release ID. Explicit releases require the frozen nonempty string key; autonomous cleanup requires exact null. It accepted pristine raw and rejected all 10 preregistered controls:

- explicit key changed, nulled, mistyped, or omitted;
- autonomous cleanup key changed to string or boolean;
- expected inventory's explicit/cleanup key contract corrupted;
- release ID changed, expected row deleted, or duplicate row added.

The focused mutation suite passed 8/8. The one deterministic runner completed with exit 0 and recorded upstream v2 false-accepts plus candidate decisions in `RUN.json`. A distinct `python3 -B audit_raw_only.py` process exited 0; `AUDIT.json` reports `PASS`, `errors=[]`, and 10/10 candidate controls independently rejected. No frozen input, predecessor PR, owner runner, or old raw was modified or rerun.

## Scope limits

Host CPython 3.14.5, standard library, one fixed synthetic joined trace. No Docker/OrbStack was used because the shared CPU lane is separately claimed by another active task and is not required for this host audit-integrity check. No owner execution, X11/XTest, GUI, physical input, game/MAP01, model, GPU, or network experiment occurred. This repairs only the copied-evidence `key`-field audit gap; it does not establish producer authenticity, release timing, physical occupancy, live completeness, useful task effect, MAP01 control, recovery efficacy, safety, or transfer. The separate #5156 formal X11 allocation remains untouched.

## Reproduction

From this directory:

1. `python3 -B -m unittest -v test_audit_key_identity.py` — 8 tests.
2. `python3 -B run_experiment.py` — one runner invocation; preserve stdout byte-for-byte as `RUN.json`.
3. After runner exit 0, `python3 -B audit_raw_only.py` — one distinct raw-only audit process; preserve stdout as `AUDIT.json`.

The plan, exact sources, blob IDs, and candidate script hashes are in `PLAN.md` and `FREEZE.json`.
