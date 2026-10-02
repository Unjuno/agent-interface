# Host method run 02

- Frozen synthetic fixture is the adjacent `fixture.json`; candidate source is `candidate.py`.
- Candidate command: `python3 candidate.py fixture.json`; exit 0. Exact stdout is `raw.json` (copied byte-for-byte from the captured command output).
- Independent audit command: `python3 audit.py fixture.json raw.json`; exit 0, `PASS_METHOD_SCOPED`, 10 checks. Auditor is a separate implementation and does not import the candidate.
- Host CI command: `python3 -m unittest -v test_method.py`, followed by `python3 -m py_compile candidate.py audit.py test_method.py` and `git diff --check`.
- Interpretation: the fixture routes 28 vs 14 requester task-effect minutes and 1 vs 17 collaborator active minutes (plain vs fast). These are stipulated inputs, not empirical estimates or an ethical threshold.
- Scope: no humans, real notifications, app/runtime, production data, or causal effect.
