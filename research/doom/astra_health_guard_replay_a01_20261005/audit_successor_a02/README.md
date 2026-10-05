# A02 full-table audit successor

This read-only successor addresses the audit limitation identified in PR #7913. It does not repeat the A01 candidate or change A01 raw.

## H / T / D / C / U

- **H:** The exact retained A01 raw table is reproduced by an independent scalar reconstruction from the frozen manual health readout and guard parameters.
- **T:** Reconstruct all evaluated samples for the five frozen loss thresholds and compare every field and row with the one-shot A01 `raw.json`. Run targeted field, omission, reordering, and extra-row mutation controls.
- **D:** PASS only if the raw hash, input hash, source identities, all five complete sample arrays (30 rows total), first invalidations, and pending/local boundary classifications match; every mutation control must fail exact comparison.
- **C:** This auditor checks arithmetic and serialization implied by the frozen guard contract. It does not re-run or independently validate the production evaluator or the human transcription.
- **U:** No candidate, model, game, GUI, X server, OS input, live threat exposure, release, recovery, or task effect.

The first audit invocation failed because the script referenced the wrong freeze keys; its output remains at `AUDIT.json`. A second invocation failed for the same provenance comparison because it compared candidate source hashes against the successor freeze rather than the parent A01 freeze; `recheck-01/AUDIT.json` is retained. After correcting the provenance reference, `recheck-02/AUDIT.json` passed. The auditor was then source-hash-pinned and rerun; `recheck-03/AUDIT.json` records that pass. After merging current main, the unchanged raw passed again at `recheck-04/AUDIT.json`, the latest result. This sequence is construction debugging and read-only rechecking, not a candidate retry.

## Reproduction

```sh
python3 -m unittest research.doom.astra_health_guard_replay_a01_20261005.audit_successor_a02.test_audit -v
python3 research/doom/astra_health_guard_replay_a01_20261005/audit_successor_a02/audit.py research/doom/astra_health_guard_replay_a01_20261005/raw.json /tmp/astra-a02-audit.json
```

The final audit reconstructs 5 threshold rows and 30 evaluated samples. Three mutation tests pass, covering changed values/labels/floors and missing, reordered, or additional rows. Scope remains offline policy-boundary evidence only.
