# Needle pilot-08: stratified near-boundary CORRECT augmentation

Issue #4462 is a successor to #3918. It tests whether two disjoint near-boundary training bands make the shifted-CORRECT improvement more stable across seeds. The small model, paired training protocol, evaluation suites and acceptance gates remain fixed. See `PREREGISTRATION.md` and `FREEZE.json`.

See [PREREGISTRATION.md](PREREGISTRATION.md) for H/T/D/C/U and [FREEZE.json](FREEZE.json) for pinned source, data mappings, cached Docker image and the one-shot command. The independent auditor does not import the runner. Construction tests do no model training.
