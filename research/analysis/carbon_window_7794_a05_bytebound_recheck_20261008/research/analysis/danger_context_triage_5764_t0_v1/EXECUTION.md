# Execution record

## Frozen identity

- Issue: #5764; allocation: `DANGER-CONTEXT-TRIAGE-5764-T0-20261001-01`.
- Current-main freeze: `82a494a6666bdab92a399cf54ad31e1d42ab204d`.
- Branch: `research/danger-context-triage-5764-t0-20261001`.
- Environment: WSL2 Ubuntu x86_64, CPython 3.12.3; commands ran from the Windows-mounted scratch workspace.
- Docker Desktop: context `desktop-linux`; read-only `docker info` remained unresponsive for about 30 seconds and was interrupted. No inventory was obtained and no image/container was created, inspected, started, or changed. This finite CPU T0 used the host because the engine was unavailable; it is not Docker evidence.
- No network, model/provider, GPU, GUI, game, X11, or physical input was used by the candidate or auditor.

## Construction and TDD

- Test-first RED: `test_triage` first failed import because `runner.py` did not exist; after the minimal selector implementation the initial six policy/lineage/denominator tests passed.
- The new #5435 identity-batching case was observed RED for unknown policy, then passed after that comparator was implemented.
- Before candidate freeze, `python3 -B -m unittest -v test_triage test_preflight` passed 9/9; `py_compile` passed for the frozen candidate/auditor/test files.
- After audit-v1 STOP, test-first for the schema adapter was observed RED because `audit_v2.py` did not exist. An initial adapter-test invocation exposed a malformed six-character test digest (not an allocation); the test fixture was corrected to a 64-character hex digest. The complete construction suite then passed 11/11 and `py_compile` passed. Candidate and formal auditors were not invoked by these unit tests.

## Formal commands and first outcomes

1. Candidate, invoked exactly once after Issue freeze comment #5924792229:

   `python3 -B run.py --stream preaudit_stream.json --output results/raw.json`

   Exit 0. Population 12, mandatory lane 1, optional audit budget 4, six policy outputs. Candidate code reads no sealed outcomes. `results/raw.json` SHA-256: `abd43afc3bc77a0275e1e58d78f95c5b1c3123d6dc0956f262848daf8b46f91a`.

2. Audit-v1, invoked exactly once after candidate exit 0:

   `python3 -B audit.py --raw results/raw.json --output results/audit.json`

   Exit 1 before writing an output. `KeyError: 'preaudit_stream_sha256'` at `_validate` line 85. It expected a flattened key, while the frozen manifest nests the stream digest under `fixture.stream_sha256`; other source digests are likewise nested. No retry occurred. See `AUDIT_V1_STOP.md` and Issue comment #5924801730.

3. Audit-v2, separately frozen in Issue comment #5924836610, invoked exactly once against the unchanged candidate raw:

   `python3 -B audit_v2.py --raw results/raw.json --output results/audit_v2.json`

   Exit 0. The versioned adapter maps the nested freeze fields into the unchanged v1 raw-replay core; it imports no candidate selector. Selection replay PASS for all six policies; denominator 12; mandatory failure count 1; optional failures 5; 6/6 mutations rejected. `results/audit_v2.json` SHA-256 is recorded in `SHA256SUMS`.

There was no candidate retry and no audit-v1 retry. Candidate=1, audit-v1=1 (STOP), audit-v2=1 (PASS). The three invocations and their dispositions remain distinct.
