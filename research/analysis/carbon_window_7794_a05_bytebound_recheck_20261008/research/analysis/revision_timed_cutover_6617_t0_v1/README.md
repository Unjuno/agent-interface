# Issue #6617 — revision-timed speech-to-effect cutover (T0)

Status: T0 complete; `PASS_METHOD_SCOPED` in WSLc. This package is a deterministic finite event model only; no audio, model, GUI, user data, or physical input is involved.

The motivating question is whether a provisional prefix can safely support *read-only preparation* that survives to a committed utterance, without allowing an obsolete intent epoch to cross the consequential GUI-input boundary. The three arms compare final-only preparation, an intentionally unsafe naive provisional comparator, and exact-version-bound read-only preparation. The independent auditor derives dispositions from raw event traces and a separate hardcoded truth table.

See `PREREGISTRATION.md` for H/T/D/C/U and gates, `cases.json` for the frozen event schedule, and `candidate.py` / `audit.py` for the simulator and raw-only auditor. Formal artifacts will live under `formal_01_20261002/`; this source directory will not be modified after `FREEZE.json` is sealed.

The frozen 10×3 run produced 30 traces. The independent audit reports a three-logical-tick stable-case advantage for version-bound preparation (3 ticks versus 6 final-only), zero unsafe provisional inputs in either safe arm, 9 detected in the deliberately naive comparator, and rejection of all four planted mutations. These are stipulated logical ticks in one scripted model, not real latency or speech/GUI evidence. Exact hashes, invocations, WSLc warning and counts are in `formal_01_20261002/RUN_RECEIPT.json`.

## Reproduce construction checks

```powershell
python -m unittest -v test_method.py
```

## Formal runtime

The formal candidate and auditor run once each in separate WSLc invocations from the pinned, already-cached Python image. They use no GPU. See `formal_01_20261002/COMMANDS.txt` and the resulting receipt for exact invocation, runtime identity, warning text, output hashes and counts. A PASS is limited to deterministic logical-time method behavior.
