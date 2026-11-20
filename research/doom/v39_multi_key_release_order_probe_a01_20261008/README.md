# V19 multi-key release-order probe A01

## H / T / D / C / U

**H.** The exact `_capture_backend` in PR #7692 head `7ec4e3e` stores only the most recent admission. For a simultaneous N-key hold it can obtain a matched down/up pair at the final empty-held boundary only when the most recently admitted key is also the last released key.

**T.** AST-extract that exact function from `research/doom/session_map01_v19.py` at the frozen PR head. For N=1,2,3, exhaust every admission ordering and every release ordering (1+4+36 schedules). A fake backend emits the V19 raw event names and maintains held keys. A match requires exact program/step/owner/intent/key/actuation identity and an empty backend after the final release. No X server, game, model, GUI, or OS input is launched.

**D.** PASS_SCOPED if every candidate is empty-held, no identity mismatch is counted as a match, and matched rates are exactly 1/N. Otherwise FAIL/HOLD as specified in `FREEZE.json`.

**C.** A no-pair tail is conservatively censored, not a false physical release. The feature is optional measurement; the exercised schedules may not match the canonical V39 action compiler or live actuation order.

**U.** Synthetic backend only. This does not establish how frequently multi-key overlaps occur, physical input state, game effect, feedback onset, recovery, or task impact. It evaluates measurement availability in the draft PR source, not code merged into main.

## Result

PASS_SCOPED. The source wrapper captured 1/1 single-key schedules, 2/4 two-key schedules (50%), and 12/36 three-key schedules (33.3%). In every nonmatching schedule, the candidate paired the most recent admission with the final released key and the downstream exact identity would reject it. The final backend held set was empty in every schedule. Thus this is a completeness/censoring limitation, not a release-safety failure.

The PR head already contains a focused test for one mismatched pair becoming `CENSORED/no_matched_release_pair`; this exhaustive probe extends that single case to all 2- and 3-key orders. A general per-key admission map plus a final empty-held boundary could preserve a matching identity for every ordering, if complete scorer-tail coverage is required.

## Reproduction

```powershell
python run_probe.py
python verify.py
python -m py_compile run_probe.py verify.py
```

`result.json` includes every enumerated schedule. The frozen source SHA-256 and Git blob identity are recorded in `FREEZE.json`; `SHA256SUMS.txt` covers the package files except itself.
