# Prefreeze correction before formal0

The first remotely staged `FREEZE.json` / source-manifest attempt referenced `test_controls.py`, whose construction-only implementation hard-coded `result.json` and `controls.json` in the source root. A fresh restored source capsule would therefore either fail because construction `result.json` is absent or inspect the wrong result if construction files happened to be present.

This defect was found before any formal candidate or auditor invocation. The first partial remote freeze remains preserved and is not treated as authorization for execution.

`test_controls_v2.py` changes only the controls orchestration boundary: it accepts the formal result path and controls output path as command-line arguments. The ten mutation definitions and unchanged `audit.py` are identical to the construction control semantics. Scientific corpus, candidate algorithm, audit algorithm, retrieval budget, decision gate, and H/T/D/C/U are unchanged.

`FREEZE_V2.json` and `SOURCE_V2.tar.xz.b64` are the only authoritative preformal source/gate commitment for allocation `RELATION-FIRST-8073-SYNTH-A01-20261006-01`.
