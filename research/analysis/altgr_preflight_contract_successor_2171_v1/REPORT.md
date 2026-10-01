# AltGr preflight contract successor #2171

Status: PASS_ALTGR_PREFLIGHT_CONTRACT_SCOPED

An exhaustive six-state contract permits DIRECT_TYPE only for DIRECT_LEVEL0_3. Dead/compose-required characters, stale layout, unknown modifier state, and partial/unknown delivery fail closed; ALTERNATE_TEXT_PATH is distinct from direct typing.

This is a model-independent decision contract. It does not evaluate a model, a physical keyboard, a receiver, multilingual task success, clipboard/application routes, or platform transfer.

Reproduction: run python experiment.py, then python audit.py.
