# Successor-2 one-shot run — Issue #6230

- Preregistration comment on Issue #6230: `5941630403`; posted before formal invocation.
- Frozen base: `1885210c4e326672391743ac10e227fea0f7a36f`.
- Branch: `research/oracle-boundary-swaps-6230-t0s2-20261002`.
- Runtime: CPython 3.12.10, Windows x64; stdlib only.
- Formal candidate: one invocation, exit 0; raw output retained in `candidate.json`.
- Independent raw-only auditor: one invocation, exit 0; output `PASS_METHOD_SCOPED`, 8/8 mutation controls rejected, zero errors, retained in `audit.json`.
- Retries/substitutions: 0. No formal candidate or auditor rerun.
- Construction tests (before freeze, distinct from formal run): five passed.
- No model/provider/network/GUI/game/OS input or external task effects.
- Docker Desktop service `com.docker.service`: Stopped/Manual; engine unavailable. No container/shared allocation changed; host-only is a scoped fallback, not container evidence.

Commands, run once each from repository root:

```powershell
$p = 'research/analysis/oracle_boundary_swaps_6230_t0s2_20261002'
python "$p/candidate.py" > "$p/candidate.json"
python -c "import json,sys; sys.path.insert(0, r'$p'); import audit; raw=json.load(open(r'$p/candidate.json',encoding='utf-8')); print(json.dumps(audit.audit(raw),sort_keys=True,separators=(',',':')))" > "$p/audit.json"
```

Construction test command:

```powershell
python -m unittest discover -s research/analysis/oracle_boundary_swaps_6230_t0s2_20261002 -p 'test_*.py' -v
```
