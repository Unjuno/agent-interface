# Local CI and integration checks

- `python -B -m unittest -v test_contract.py` — PASS, 3/3 construction tests (inline fixtures; no formal fixture input).
- `python -B -m py_compile candidate.py audit.py freeze.py` — PASS.
- `git diff --check` — PASS for tracked staged source before the run; report/evidence files are additive.
- Formal candidate and raw-only audit — see `RUN_RECORD.json`; each invoked once, no retry.
- Repository analytical index check is **not qualified in this sparse checkout**. It reports hundreds of absent sibling directories as stale. `check_index.py --write` was intentionally not run because sparse enumeration would discard retained entries. The normal generated-index/Public Navigation/Research Workspace CI should be checked on the full PR checkout; no repository-wide PASS is claimed locally.
- No hosted workflow, model, container, GUI, or runtime integration suite was run.
