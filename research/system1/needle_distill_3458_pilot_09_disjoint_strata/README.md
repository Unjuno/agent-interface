# Needle pilot-09: contract-bound disjoint near-boundary strata

# Issue #4469 is a corrected successor to #4462. It tests the same multi-band training idea on fresh seeds, with band B starting at the exact public contract boundary |dx|=.111. The independent auditor checks each band separately and binds the public contract digest. The small model, paired training protocol, evaluation suites and acceptance gates remain fixed. See `ISSUE_CONTRACT.md`, `PREREGISTRATION.md` and `FREEZE.json`.

See [PREREGISTRATION.md](PREREGISTRATION.md) for H/T/D/C/U and [FREEZE.json](FREEZE.json) for pinned source, data mappings, cached Docker image and the one-shot command. The independent auditor does not import the runner. Construction tests do no model training.
