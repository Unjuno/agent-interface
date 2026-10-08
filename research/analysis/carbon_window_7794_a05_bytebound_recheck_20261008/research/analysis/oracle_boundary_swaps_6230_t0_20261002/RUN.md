# One-shot T0 run — Issue #6230

- Freeze preregistered on Issue #6230 before formal candidate invocation: GitHub comment `5941527039`.
- Base: `18ae2231df50b83920f4aadf26913bb4af4c4b62`.
- Branch: `research/oracle-boundary-swaps-6230-t0-20261002`.
- Runtime: CPython 3.12.10, Windows x64; standard library only.
- Docker Desktop: service `com.docker.service` Stopped/Manual; engine status request unresponsive. No container/shared allocation changed; host CPU fallback for this finite no-model fixture.
- Formal candidate invocations: 1; exit 0.
- Independent raw-only audit invocations: 1; exit 0; retained output `PASS_METHOD_SCOPED`, 7/7 implemented corruptions rejected.
- Retries/substitutions: 0. Candidate/auditor not rerun after formal invocation.
- Model/network/GUI/game/OS-input/external task effects: none.

Commands (executed once each, from repository root):

```powershell
$p = 'research/analysis/oracle_boundary_swaps_6230_t0_20261002'
python "$p/candidate.py" > "$p/candidate.json"
python -c "import json,sys; sys.path.insert(0, r'$p'); import audit; raw=json.load(open(r'$p/candidate.json',encoding='utf-8')); print(json.dumps(audit.audit(raw),sort_keys=True,separators=(',',':')))" > "$p/audit.json"
```

Construction tests, separate from the formal candidate/audit, ran with:

```powershell
python -m unittest discover -s research/analysis/oracle_boundary_swaps_6230_t0_20261002 -p 'test_*.py' -v
```

All six passed before freeze. The later post-run static finding is recorded in [REPORT.md](REPORT.md); it does not alter the frozen files or formal outputs. It limits the package disposition to `HOLD_AUDITOR_INTENT_EQUIVALENCE` despite the raw auditor's narrower PASS.
