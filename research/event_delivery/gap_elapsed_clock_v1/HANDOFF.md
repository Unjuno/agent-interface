# Integration handoff

## Local completion and remaining blockers

DONE: targeted repository intake; exact predecessor byte checks; H/T/D/C/U and local source freeze; excluded construction; one 72-case run; independent raw audit; mutation controls; source rehash; result and additive delivery material.

BLOCKED: remote successor creation/preregistration, GitHub result publication, PR creation/review/merge, main readback after merge and remote branch cleanup. No remote changes occurred. Overall ROADMAP remains open.

## Review without consuming another allocation

From this directory, ordinary Python 3.13 with its standard library is sufficient. Do not use Python `-O` because the frozen aggregate auditor uses assertions. No training, model, GUI or input is involved.

```sh
sha256sum -c SHA256SUMS
python -B -m unittest -v test_policy
python -B audit.py --root local-formal-01 --schedule schedule.json --freeze FREEZE.json --out independently_reaudited.json
python -B test_audit_controls.py --root local-formal-01 --schedule schedule.json --freeze FREEZE.json --out independently_reaudited_controls.json
```

The last two commands create new audit files and do not rerun producer/consumer cases. The frozen allocation command refuses an existing output directory. A new experimental replication requires a new allocation/schedule ID, output path and freeze; do not overwrite or replace this result.

## Applying the additive patch

The delivered patch is a binary-capable, addition-only git diff from a local empty patch carrier. It is NOT a checkout or commit descended from repository main. Patch applicability is checked in a clean local directory, not against a live cloned main. The intake main path was absent, but ownership may change after that read.

A publishing agent should fetch current main through its own authorized connection, recheck Issues/PRs/branches and the exact intended path, choose a unique additive branch, run `git apply --check` on that actual checkout, apply and review the patch, rerun the read-only audit and repository-specific checks, create/link the successor and PR while preserving local preregistration chronology, and merge only after review/checks allow it. Do not delete another worker's branch. Delete an own branch only after merge readback and dependency/provenance verification.

## Do not promote

Do not treat count notices as false permanent-loss claims, choose 80 ms as a production timeout, start automatic resync, use a read cursor as ACK, or claim bounded host/model notification latency. The timing state is process-local and payloads are represented by digests. This result remains separate from #3883/#3917 real producer-reader work and from active #3929.

## Evidence map

- PREREGISTRATION.md + FREEZE.json: premeasurement plan and hashes.
- ENVIRONMENT.json + PROVENANCE.json + INTAKE.md + SOURCES.md: environment and upstream lineage.
- LAUNCH.json / LAUNCHED.json / formal_exit.json: supplemental launch provenance and actual runner exit.
- local-formal-01/: raw case journals, SQLite bytes, process states and complete allocation record.
- formal_audit.json / formal_controls.json: independent reconstruction and corruption rejection.
- SOURCE_REHASH.json / SHA256SUMS: frozen-source and packaged-byte verification.
- construction-* / construction_*.json / unit outputs: excluded construction, retained separately.
- ANALYSIS.md: mathematical interpretation, not a post-result gate change.
- RESULT.md / RESULT_SUMMARY.json: completed local outcome.
