# Run record

- Base: `4da4257ad481e9a4ea79133bdaf93c962e686fe7` (main), branch `research/speech-act-grounding-6424-t0-20261002`.
- Runtime: macOS 26.6.2 arm64, CPython 3.14.5. Neither `wslc.exe` nor `wslc` was available. Docker CLI context was `orbstack`; no Docker/OrbStack command was used, so the unrelated shared engine was not touched.
- Preformal construction: exact source-span check initially found three errors in authored fixture bounds; bounds were corrected before freeze. `python3 -m unittest discover -s research/analysis/speech_act_grounding_6424_t0_20261002 -p 'test_*.py' -v` passed 3/3. The first attempted unittest module syntax failed during import before candidate execution; corrected to explicit directory discovery.
- Formal candidate: `python3 research/analysis/speech_act_grounding_6424_t0_20261002/candidate.py`; exit 0, one invocation. Raw stdout/stderr and exit receipt retained.
- Formal auditor: `python3 research/analysis/speech_act_grounding_6424_t0_20261002/audit.py`; exit 1, one invocation. It correctly found its `turn_author_swapped` check did not materialize a mutation. Result is `FAIL_METHOD`; no retry and no scientific PASS.
- Post-allocation diagnostic (not a retry or formal result): `python3 research/analysis/speech_act_grounding_6424_t0_20261002/diagnose_audit_mutations.py`; `DIAGNOSTIC_PASS` means only all six diagnostic input objects differed from their originals. The candidate still accepts several mutated action-force promotions; that policy gap is a reason to fail this T0, not a pass.
- Post-allocation local construction tests: same unittest discovery command, 3/3 pass. This does not change the first formal outcome.
- No model, people, GUI, GPU, container, network, live approval, user data or external effect. Host-only result does not meet WSLc isolation evidence and says nothing about human intent truth, natural language generalization, authority, safety or runtime enforcement.

## Raw files

`candidate.raw.json`, `candidate.stdout.json`, `candidate.stderr.txt`, `candidate.exit.txt`, `audit.raw.json`, `audit.stdout.json`, `audit.stderr.txt`, `audit.exit.txt`, and `diagnostic_mutations.raw.json` preserve the output and sidecars. Formal files are never overwritten by the diagnostic.
