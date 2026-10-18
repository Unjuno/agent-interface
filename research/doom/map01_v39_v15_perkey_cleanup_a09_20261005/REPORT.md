# A09 result — fake-X V15 key-up retry construction

## Result

`PASS_CONSTRUCTION_SCOPED`. On current-main source `712a71b25dc024b5406b24b568225c0663e7278b`, the one-shot normal arm completed one F8 DOWN/UP step with one verified owner KeyRelease attempt and an empty fake-server keymap. In the treatment arm, the fake server dropped exactly the first KeyRelease; the owner sampled the key still down, issued a second KeyRelease, sampled it up, and published one identity-bound `input_release_transition` before a completed terminal with verified empty release. Both final fake keymaps were empty. The independent auditor found zero failures.

The difference from A07/A08 was confined to the test fixture: it now binds a stable observed fake focus to the actual ExecutorV13 lease and provides the `(intent, step)` context expected by the production release-batch telemetry path. The V13 executor and current-main V15/V4/V3/V12 owner/release implementation were loaded from the frozen source closure.

Before packaging, `main` advanced from the frozen base to `38fe303fec59cde15f708483cae00bf617f3bdd0`. A Git path comparison across all 21 frozen production source files found no changes, so the exercised software closure is byte-identical at that later main tip. The candidate itself remains explicitly pinned to `712a71b25dc024b5406b24b568225c0663e7278b`.

## Reproduction and records

- Freeze and exact source hashes: `FREEZE.json`, `source-manifest.json`.
- Candidate and independent raw auditor: `candidate.py`, `audit.py`.
- First candidate output and independent audit: `results/candidate.json`, `results/audit.stdout.log`.
- Process outputs: `results/candidate.stdout.log`, `results/candidate.stderr.log`, `results/audit.stderr.log`.
- On the same frozen checkout, the existing current-main regression suite `python -m unittest -v test_input_transition_owner_v4 test_input_owner_v12_explicit_up_cancel test_input_owner_v12_cleanup_after_explicit_up` passed 9/9 under bundled Python 3.12.14. This covers the joined owner receipt, dropped explicit key-up retry, ordered batch behavior, persistent loss custody, and cleanup boundaries; it remains software/fake-display evidence.
- A07's pre-treatment STOP and A08's sparse-checkout STOP remain separate in their respective result packages; neither was retried or relabeled.
- The package hash manifest is `SHA256SUMS`.

## Limits

OrbStack could not read its cached image blob, so A09 ran with the local bundled Python runtime; it is not a container result. No real X11 server, GUI, physical keyboard, Doom, model, application effect, independent task feedback, bounded recovery, live threat exposure, or latency distribution was exercised. Empty `query_keymap`/fake-server state proves only the synthetic software path. The #59 private game allocation remains unassigned and untouched. This result does not establish a live or product-level control improvement.
